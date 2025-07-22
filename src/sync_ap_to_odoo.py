import os
import psycopg2
import requests

# Load environment variables
DATABASE_URL = os.environ['DATABASE_URL']
ODOO_URL = os.environ['ODOO_URL']
ODOO_USER = os.environ['ODOO_USER']
ODOO_PASS = os.environ['ODOO_PASS']
ODOO_DB = os.environ['ODOO_DB']
ODOO_CUSTOM_FIELD = "x_studio_balance_due_total"

def get_total_invoice_amount():
    try:
        print("📡 Fetching total invoice amount from Neon DB...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT SUM(invoice_amount) FROM invoices;")
        result = cur.fetchone()
        total = result[0] or 0
        cur.close()
        conn.close()
        print(f"💰 Total Invoice Amount: ${total:,.2f}")
        return total
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return 0

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

        # Find all records in x_ap_dash to update
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
        print("🔎 Search response:", search_json)

        if "error" in search_json:
            print("❌ Error in search response:", search_json["error"])
            return

        record_ids = search_json.get("result", [])
        if not record_ids:
            print("❌ No records found to update.")
            return

        # Update the custom field
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
        print("🛠 Update response:", update_json)

        if "error" in update_json:
            print("❌ Error in update response:", update_json["error"])
        else:
            print("✅ Odoo field updated successfully!")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    total = get_total_invoice_amount()
    update_odoo(total)
