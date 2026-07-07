import sqlite3
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="⚡ Cyber Guard Advanced SIEM Engine ⚡")
DB_FILE = "cyber_integrity.db"

@app.get("/security/alerts")
def get_security_alerts():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT timestamp, event_type, file_path, severity FROM security_logs ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    
    critical_count = sum(1 for r in rows if "🔴" in str(r[3]))
    alerts_list = [{"time": r[0], "action": r[1].upper(), "target": r[2], "severity": r[3]} for r in rows]
    
    return {
        "metrics": {"total": len(rows), "critical": critical_count},
        "incidents": alerts_list
    }

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>⚡ Autonomous Cyber Guard Dashboard ⚡</title>
        <style>
            body { background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', monospace; margin: 30px; }
            h1 { color: #58a6ff; border-bottom: 2px solid #21262d; padding-bottom: 10px; }
            .metrics-container { display: flex; gap: 20px; margin-bottom: 20px; }
            .card { background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; flex: 1; text-align: center; }
            .card.critical { border-color: #f85149; }
            .number { font-size: 2em; font-weight: bold; color: #58a6ff; }
            .card.critical .number { color: #f85149; }
            table { width: 100%; border-collapse: collapse; background: #161b22; border: 1px solid #30363d; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #30363d; }
            th { background-color: #21262d; color: #58a6ff; }
            tr:hover { background-color: #1f242c; }
        </style>
        <script>
            async function fetchAlerts() {
                const response = await fetch('/security/alerts');
                const data = await response.json();
                document.getElementById('total-incidents').innerText = data.metrics.total;
                document.getElementById('critical-incidents').innerText = data.metrics.critical;
                
                let tableBody = '';
                data.incidents.forEach(inc => {
                    tableBody += `<tr>
                        <td>${inc.time}</td>
                        <td><strong>${inc.action}</strong></td>
                        <td>${inc.target}</td>
                        <td>${inc.severity}</td>
                    </tr>`;
                });
                document.getElementById('log-table').innerHTML = tableBody;
            }
            setInterval(fetchAlerts, 2000);
            window.onload = fetchAlerts;
        </script>
    </head>
    <body>
        <h1>🛡️ Autonomous Cyber Guard Live SIEM</h1>
        <div class="metrics-container">
            <div class="card">
                <div class="number" id="total-incidents">0</div>
                <div>Total Events Captured</div>
            </div>
            <div class="card critical">
                <div class="number" id="critical-incidents">0</div>
                <div>Unresolved/Mitigated Alerts</div>
            </div>
        </div>
        <h2>📜 Live Security Logs (Auto-Refreshes every 2s)</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Intercepted Action</th>
                    <th>Target Source Path</th>
                    <th>Threat Level</th>
                </tr>
            </thead>
            <tbody id="log-table"></tbody>
        </table>
    </body>
    </html>
    """
    return html_content
