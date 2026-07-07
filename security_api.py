import sqlite3
from fastapi import FastAPI

app = FastAPI(title="⚡ Cyber Guard SIEM ⚡")
DB_FILE = "cyber_integrity.db"

@app.get("/")
def health():
    return {"agent_status": "🟢 RUNNING", "integrity_shield": "🛡️ ACTIVE"}

@app.get("/security/alerts")
def get_security_alerts():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT timestamp, event_type, file_path, severity FROM security_logs ORDER BY id DESC")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    
    alerts_list = [{"time": r[0], "action": r[1].upper(), "target": r[2], "severity_level": r[3]} for r in rows]
    return {"summary": {"total_incidents_logged": len(rows)}, "incidents": alerts_list}
