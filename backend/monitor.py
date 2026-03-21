import json
import time
import os
import threading
from datetime import datetime

# Import your optimized lawyer agent!
from lawyer import generate_legal_letters

# Global state
_last_breach_count = 0
_notifications = []
_monitor_running = False

def get_notifications():
    return _notifications.copy()

def clear_notifications():
    global _notifications
    _notifications = []

def check_for_new_breaches(callback_function):
    global _last_breach_count

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assumes breach_db.json is inside a 'data' folder based on your original code
    breach_path = os.path.join(current_dir, 'data', 'breach_db.json')

    # --- CRITICAL FIX: INITIALIZE SILENTLY ---
    try:
        if os.path.exists(breach_path):
            with open(breach_path, 'r') as f:
                data = json.load(f)
                _last_breach_count = len(data.get('breaches', []))
    except Exception as e:
        print(f"[Monitor] Initial read error: {e}")
    # -----------------------------------------

    while True:
        try:
            with open(breach_path, 'r') as f:
                data = json.load(f)

            current_count = len(data.get('breaches', []))

            if current_count > _last_breach_count:
                new_breaches = data['breaches'][_last_breach_count:]
                _last_breach_count = current_count

                for breach in new_breaches:
                    notification = {
                        "type": "NEW_BREACH_DETECTED",
                        "company": breach.get('company', 'Unknown'),
                        "severity": breach.get('severity', 'critical'),
                        "records": breach.get('records_exposed', 0),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "message": f"NEW BREACH: {breach.get('company')} — {breach.get('records_exposed', 0):,} records exposed. Autonomous legal response initiated."
                    }
                    _notifications.append(notification)
                    
                    # Trigger the actual action
                    callback_function(breach)

        except Exception as e:
            # Silently pass file read errors in case you are actively saving the file during demo
            pass

        time.sleep(10) # 10 seconds for a snappy live demo

def on_new_breach(breach):
    company_name = breach.get('company', 'Unknown')
    print(f"\n🚨 [Monitor] CRITICAL THREAT DETECTED: {company_name}")
    print(f"📊 [Monitor] Records exposed: {breach.get('records_exposed', 0):,}")
    print(f"⚖️ [Monitor] Waking up Agent 4 (Lawyer) to draft Section 12 Notice...")
    
    # Create a targeted consent_expiry object just for this company
    target_data = [{
        "company": company_name, 
        "best_contact": f"dpo@{company_name.lower().replace(' ', '')}.com", 
        "section_16_violation": False,
        "escalation": {"regulator": "Data Protection Board of India"}
    }]
    
    try:
        # --- THE DEMO FIX: Hardcoded realistic email ---
        letters = generate_legal_letters(target_data, "rahul.sharma@gmail.com")
        print(f"✅ [Monitor] Autonomous letter drafted successfully for {company_name}. Ready for transmission.\n")
    except Exception as e:
        print(f"❌ [Monitor] AI drafting failed: {e}\n")

def start_monitor():
    global _monitor_running

    if _monitor_running:
        return

    _monitor_running = True

    thread = threading.Thread(
        target=check_for_new_breaches,
        args=(on_new_breach,),
        daemon=True
    )
    thread.start()
    print("[Monitor] Autonomous breach monitor ONLINE. Watching threat feeds...")