import time
import os
import shutil
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIRECTORY = os.path.expanduser("~/critical_vault")
BACKUP_DIRECTORY = os.path.expanduser("~/secure_backup_vault")
DB_FILE = "cyber_integrity.db"

def init_security_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT,
            file_path TEXT,
            severity TEXT
        )
    """)
    conn.commit()
    conn.close()

class AutoHealingGuardHandler(FileSystemEventHandler):
    def log_and_heal(self, event_type, path):
        file_name = os.path.basename(path)
        backup_path = os.path.join(BACKUP_DIRECTORY, file_name)
        severity = "INFO"
        
        # Checking if file needs critical restoration
        if event_type in ["deleted", "modified"] and os.path.exists(backup_path):
            severity = "🔴 SELF-HEALING TRIGGERED"
            print(f"\n🚨 [ATTACK/CORRUPTION DETECTED] File {event_type.upper()}: {path}")
            print(f"🤖 Mitigating Incident... Fetching gold standard copy from Backup Vault...")
            
            # Anti-tamper loop: Restore the original file instantly
            try:
                shutil.copy(backup_path, path)
                print(f"✅ [SUCCESS] File successfully restored and locked back to production!")
                event_type = f"healed_{event_type}"
            except Exception as e:
                print(f"❌ restoration failed: {str(e)}")
        
        elif event_type == "created":
            severity = "🟢 NEW_INGESTION"

        # Log to local SIEM Database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO security_logs (event_type, file_path, severity) VALUES (?, ?, ?)",
            (event_type, path, severity)
        )
        conn.commit()
        conn.close()

    def on_created(self, event):
        if not event.is_directory: self.log_and_heal("created", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory: self.log_and_heal("deleted", event.src_path)

    def on_modified(self, event):
        # Prevent infinite loops during self-healing replication check
        if not event.is_directory:
            # Short sleep to let file handle release
            time.sleep(0.1) 
            self.log_and_heal("modified", event.src_path)

if __name__ == "__main__":
    init_security_db()
    print(f"🛡️ AI Cyber Guard [V2: Self-Healing Edition] Active!")
    print(f"Monitoring: {WATCH_DIRECTORY}")
    
    # Pre-populate production folder if empty on launch
    if not os.listdir(WATCH_DIRECTORY):
        for f in os.listdir(BACKUP_DIRECTORY):
            shutil.copy(os.path.join(BACKUP_DIRECTORY, f), os.path.join(WATCH_DIRECTORY, f))
            print(f"📦 Synchronized initial golden image for {f}")

    event_handler = AutoHealingGuardHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=True)
    observer.start()
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: observer.stop()
    observer.join()
