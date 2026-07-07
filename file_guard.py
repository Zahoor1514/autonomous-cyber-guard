import time
import os
import shutil
import sqlite3
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIRECTORY = os.path.expanduser("~/critical_vault")
BACKUP_DIRECTORY = os.path.expanduser("~/secure_backup_vault")
DB_FILE = "cyber_integrity.db"

def calculate_sha256(file_path):
    """Calculate cryptographic SHA-256 checksum of a file."""
    if not os.path.exists(file_path):
        return None
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

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

class CryptoHashGuardHandler(FileSystemEventHandler):
    def log_and_heal(self, event_type, path):
        file_name = os.path.basename(path)
        backup_path = os.path.join(BACKUP_DIRECTORY, file_name)
        severity = "INFO"
        
        # Core Hash Verification Logic
        if event_type == "modified":
            current_hash = calculate_sha256(path)
            backup_hash = calculate_sha256(backup_path)
            
            # If hashes match, it means it was just restored or untouched
            if current_hash == backup_hash:
                return
                
            event_type = "tampered (hash_mismatch)"

        if event_type in ["deleted", "tampered (hash_mismatch)"] and os.path.exists(backup_path):
            severity = "🔴 CRYPTO CRITICAL UNRESOLVED"
            print(f"\n🚨 [TAMPER/CRYPTO ALERT] Action: {event_type.upper()} on {file_name}")
            print(f"🤖 Calculating SHA-256 Mismatch... Initiating self-healing protocol...")
            
            try:
                shutil.copy(backup_path, path)
                print(f"✅ [RESTORED] Cryptographic integrity re-established for {file_name}!")
                event_type = f"healed_{event_type}"
            except Exception as e:
                print(f"❌ Rollback failed: {str(e)}")

        elif event_type == "created":
            severity = "🟢 SYSTEM_INGESTION"

        # Log event to SIEM DB
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
        if not event.is_directory:
            time.sleep(0.1)
            self.log_and_heal("modified", event.src_path)

if __name__ == "__main__":
    init_security_db()
    print(f"🛡️ AI Cyber Guard [V3: Cryptographic Integrity Edition] Active!")
    
    if not os.listdir(WATCH_DIRECTORY) and os.path.exists(BACKUP_DIRECTORY):
        for f in os.listdir(BACKUP_DIRECTORY):
            shutil.copy(os.path.join(BACKUP_DIRECTORY, f), os.path.join(WATCH_DIRECTORY, f))
            print(f"🔑 Loaded master copy for {f} (SHA-256 Active)")

    event_handler = CryptoHashGuardHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=True)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: observer.stop()
    observer.join()
# Is class structure ko update karein file_guard.py mein
class CryptoHashGuardHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.is_healing = False  # Lock initialization flag

    def log_and_heal(self, event_type, path):
        if self.is_healing:
            return  # Agar system abhi khud file copy kar raha hai, toh naya loop intercept mat karo
            
        file_name = os.path.basename(path)
        backup_path = os.path.join(BACKUP_DIRECTORY, file_name)
        severity = "INFO"
        
        if event_type == "modified":
            current_hash = calculate_sha256(path)
            backup_hash = calculate_sha256(backup_path)
            if current_hash == backup_hash:
                return
            event_type = "tampered (hash_mismatch)"

        if event_type in ["deleted", "tampered (hash_mismatch)"] and os.path.exists(backup_path):
            severity = "🔴 CRYPTO CRITICAL UNRESOLVED"
            print(f"\n🚨 [TAMPER ALERT] Action: {event_type.upper()} on {file_name}")
            
            try:
                self.is_healing = True  # Lock lagao
                shutil.copy(backup_path, path)
                print(f"✅ [RESTORED] Cryptographic integrity re-established for {file_name}!")
                event_type = f"healed_{event_type}"
            except Exception as e:
                print(f"❌ Rollback failed: {str(e)}")
            finally:
                time.sleep(0.5) # System cooldown breath
                self.is_healing = False  # Lock kholo

        # Save to database logic remains same...
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO security_logs (event_type, file_path, severity) VALUES (?, ?, ?)", (event_type, path, severity))
        conn.commit()
        conn.close()
