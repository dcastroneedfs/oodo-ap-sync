import os
import time
import psycopg2
import requests

# Load environment variables
ODOO_URL = os.environ["ODOO_URL"]
ODOO_DB = os.environ["ODOO_DB"]
ODOO_USER = os.environ["ODOO_USER"]
ODOO_PASS = os.environ["ODOO_PASS"]
DATABASE_URL = os.environ["DATABASE_URL"]

# Hardcoded custom field name in Odoo (you can change if needed)
ODOO_CUSTOM_FIELD = "x_studio_total_aps"

def fetch_total_invoice_amount():
    print("📡 Fetching total invoice amount from Neon DB...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(invoice_amount) FROM invoices")
        total = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        total = total or 0.0
        print(f"💰 Total Invoice Amount: ${total:,.2f}")
        return total
    except Exception as e:
        print(f"❌ Error fetching total: {e}")
        return 0.0

def update_odoo(total_amount):
    try:
        print("🔐 Logging into Odoo...")
        auth_response = requests.post(f"{ODOO_URL}/web/session/authenticate", json={
            "params": {
                "db": ODOO_DB,
                "login": ODOO_USER,
                "password": ODOO_PASS
            }
        })

        auth_response.raise_for_status()
        session_id = auth_response.cookies.get("session_id")

        if not session_id:
            print("❌ Failed to authenticate with Odoo.")
            return

        print("✅ Logged into Odoo, updating field...")
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"session_id={session_id}"
        }

        # Search for records to update
        search_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "x_ap_dash",
                "method": "search",
                "args": [[["id", "!=", 0]]],
                "kwargs": {},
            },
            "id": 1,
        }

        search_response = requests.post(f"{ODOO_URL}/web/dataset/call_kw", json=search_payload, headers=headers)
        search_json = search_response.json()

        if "error" in search_json:
            print("❌ Error in search response:", search_json["error"])
            return

        record_ids = search_json.get("result", [])

        if not record_ids:
            print("❌ No records found to update.")
            return

        # Update record(s)
        update_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "x_ap_dash",
                "method": "write",
                "args": [record_ids, {ODOO_CUSTOM_FIELD: total_amount}],
                "kwargs": {},
            },
            "id": 2,
        }

        update_response = requests.post(f"{ODOO_URL}/web/dataset/call_kw", json=update_payload, headers=headers)
        update_json = update_response.json()

        if "error" in update_json:
            print("❌ Error in update response:", update_json["error"])
        else:
            print("✅ Odoo field updated successfully!")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    while True:
        total = fetch_total_invoice_amount()
        update_odoo(total)
        time.sleep(60)
