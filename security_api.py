import sqlite3
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="⚡ Next-Gen Forensic SIEM Engine ⚡")
DB_FILE = "cyber_integrity.db"

@app.get("/security/alerts")
def get_security_alerts():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT timestamp, event_type, file_path, severity, suspect_process FROM security_logs ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    
    critical_count = sum(1 for r in rows if "🔴" in str(r[3]))
    alerts_list = [{"time": r[0], "action": r[1].upper(), "target": r[2], "severity": r[3], "suspect": r[4]} for r in rows]
    
    return {"metrics": {"total": len(rows), "critical": critical_count}, "incidents": alerts_list}

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>⚡ Next-Gen Autonomous EDR Center ⚡</title>
        <style>
            body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; margin: 30px; }
            h1 { color: #58a6ff; border-bottom: 2px solid #21262d; }
            .metrics { display: flex; gap: 20px; margin-bottom: 20px; }
            .card { background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; flex: 1; text-align: center; }
            .card.crit { border-color: #f85149; color: #f85149; }
            table { width: 100%; border-collapse: collapse; background: #161b22; }
            th, td { padding: 12px; border-bottom: 1px solid #30363d; text-align: left; }
            th { background: #21262d; color: #58a6ff; }
            .bad-proc { color: #ffa657; font-weight: bold; }
        </style>
        <script>
            async function refreshLogs() {
                const res = await fetch('/security/alerts');
                const data = await res.json();
                document.getElementById('tot').innerText = data.metrics.total;
                document.getElementById('crit').innerText = data.metrics.critical;
                let body = '';
                data.incidents.forEach(i => {
                    body += `<tr>
                        <td>${i.time}</td>
                        <td><b>${i.action}</b></td>
                        <td>${i.target}</td>
                        <td>${i.severity}</td>
                        <td class="bad-proc">${i.suspect}</td>
                    </tr>`;
                });
                document.getElementById('rows').innerHTML = body;
            }
            setInterval(refreshLogs, 2000); window.onload = refreshLogs;
        </script>
    </head>
    <body>
        <h1>🛡️ Autonomous Forensic EDR & SIEM Portal</h1>
        <div class="metrics">
            <div class="card"><h2><span id="tot">0</span></h2>Total Incidents Logged</div>
            <div class="card crit"><h2><span id="crit">0</span></h2>Active Crypto Mitigations</div>
        </div>
        <table>
            <thead><tr><th>Timestamp</th><th>Action</th><th>Target Path</th><th>Threat Level</th><th>Forensic Suspect (PID)</th></tr></thead>
            <tbody id="rows"></tbody>
        </table>
    </body>
    </html>
    """
