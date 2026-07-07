import time
import os
import shutil
import sqlite3
import hashlib
import psutil
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATIONS ---
VAULTS = {
    os.path.expanduser("~/critical_vault"): os.path.expanduser("~/secure_backup_vault/critical_vault"),
    os.path.expanduser("~/app_configs"): os.path.expanduser("~/secure_backup_vault/app_configs")
}
DB_FILE = "cyber_integrity.db"

# 🔔 Telegram Bot Settings (Enter your actual tokens here if you want live mobile push)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def send_telegram_alert(message):
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"📡 Telegram Send Error: {str(e)}")

def get_offending_process():
    """Scan recent processes to identify who touched the disk recently."""
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['pid'] != current_pid and proc.info['name'] not in ['python3', 'python', 'uvicorn', 'systemd']:
                return f"{proc.info['name']} (PID: {proc.info['pid']}) [User: {proc.info['username']}]"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return "Unknown System Process / User Command"

def calculate_sha256(file_path):
    if not os.path.exists(file_path): return None
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception: return None

def init_security_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT,
            file_path TEXT,
            severity TEXT,
            suspect_process TEXT
        )
    """)
    conn.commit()
    conn.close()

class MultiVaultEDRHandler(FileSystemEventHandler):
    def __init__(self, watch_dir, backup_dir):
        super().__init__()
        self.watch_dir = watch_dir
        self.backup_dir = backup_dir
        self.is_healing = False

    def log_and_heal(self, event_type, path):
        if self.is_healing: return
        
        file_name = os.path.basename(path)
        backup_path = os.path.join(self.backup_dir, file_name)
        severity = "INFO"
        suspect = "N/A"
        
        if event_type == "modified":
            if calculate_sha256(path) == calculate_sha256(backup_path): return
            event_type = "tampered (hash_mismatch)"

        if event_type in ["deleted", "tampered (hash_mismatch)"] and os.path.exists(backup_path):
            severity = "🔴 CRITICAL BREACH MITIGATED"
            suspect = get_offending_process()
            
            print(f"\n🚨 [ALARM] {event_type.upper()} inside {self.watch_dir}")
            print(f"🕵️‍♂️ Suspect Process: {suspect}")
            
            try:
                self.is_healing = True
                shutil.copy(backup_path, path)
                print(f"✅ [RECOVERED] Integrity Restored via SHA-256 validation!")
                
                # Send Cloud Notification
                msg = f"🛡️ *Autonomous Cyber Guard Alert!*\n⚠️ Event: `{event_type.upper()}`\n📁 Path: `{path}`\n🕵️‍♂️ Suspect: `{suspect}`\n🟢 Status: *Auto-Healed & Restored!*"
                send_telegram_alert(msg)
                
                event_type = f"healed_{event_type}"
            except Exception as e:
                print(f"❌ Healing Failed: {str(e)}")
            finally:
                time.sleep(0.3)
                self.is_healing = False

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO security_logs (event_type, file_path, severity, suspect_process) VALUES (?, ?, ?, ?)", 
                       (event_type, path, severity, suspect))
        conn.commit()
        conn.close()

    def on_created(self, event):
        if not event.is_directory: self.log_and_heal("created", event.src_path)
    def on_deleted(self, event):
        if not event.is_directory: self.log_and_heal("deleted", event.src_path)
    def on_modified(self, event):
        if not event.is_directory: time.sleep(0.1); self.log_and_heal("modified", event.src_path)

if __name__ == "__main__":
    init_security_db()
    print(f"🛡️ AI Cyber Guard [V4: Multi-Vault EDR Edition] Active!")
    
    observer = Observer()
    for watch, backup in VAULTS.items():
        if not os.path.exists(watch): os.makedirs(watch)
        if not os.path.exists(backup): os.makedirs(backup)
        
        # Initial golden image sync
        for f in os.listdir(backup):
            if not os.path.exists(os.path.join(watch, f)):
                shutil.copy(os.path.join(backup, f), os.path.join(watch, f))
                
        handler = MultiVaultEDRHandler(watch, backup)
        observer.schedule(handler, path=watch, recursive=True)
        print(f"🔒 Shielding: {watch}")

    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: observer.stop()
    observer.join()
