import os
import time
import random

TARGET_DIR = os.path.expanduser("~/critical_vault")

def launch_stress_attack():
    print("☣️ [LAUNCHING ATTACK SIMULATION] Initializing Ransomware Payload mimic script...")
    time.sleep(2)
    
    if not os.path.exists(TARGET_DIR):
        print("❌ Target directory missing. Aborting attack vector.")
        return

    files = [f for f in os.listdir(TARGET_DIR) if os.path.isfile(os.path.join(TARGET_DIR, f))]
    
    if not files:
        print("⚠️ No production assets found in Vault to target! Put some dummy files first.")
        return

    print(f"🎯 Target files spotted: {files}")
    
    # 1. Tamper Attack Simulation (Scrambling content)
    for f in files:
        file_path = os.path.join(TARGET_DIR, f)
        print(f"⚡ [TAMPERING] Overwriting headers of: {f}")
        with open(file_path, "w") as target:
            target.write(f"CRITICAL_SYSTEM_DATA_LOCKED_BY_EXPLOIT_VECTOR_{random.randint(1000,9999)}")
        
        time.sleep(1.5) # Giving observer time to process logs
        
    # 2. Hard Deletion Simulation
    for f in files:
        file_path = os.path.join(TARGET_DIR, f)
        print(f"🔥 [PURGING] Force removing target file: {f}")
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        time.sleep(1.5)

    print("\n🏁 [SIMULATION END] Stress sequence completed. Verify dashboard for automated forensic rollbacks!")

if __name__ == "__main__":
    launch_stress_attack()
