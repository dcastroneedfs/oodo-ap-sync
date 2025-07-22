import os
import psycopg2
import requests

# Odoo connection settings from environment variables
ODOO_URL = os.getenv("ODOO_URL")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASS = os.getenv("ODOO_PASS")
ODOO_DB = os.getenv("ODOO_DB")

# Neon DB connection string (from DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")

# Odoo custom field to update
ODOO_CUSTOM_FIELD = "x_studio_total_ap"

def get_total_invoice_amount():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT SUM(invoice_amount) FROM invoices")
        total = cur.fetchone()[0] or 0.0
        conn.close()
        return round(total, 2)
    except Exception as e:
        print(f"❌ DB Error: {e}")
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

        payload = {
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

        search_response = requests.post(f"{ODOO_URL}/web/dataset/call_kw", json=payload, headers=headers)
        record_ids = search_response.json()["result"]

        if not record_ids:
            print("❌ No records found to update.")
            return

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
        update_response.raise_for_status()
        print("✅ Odoo field updated successfully!")

    except Exception as e:
        print(f"❌ Failed to update Odoo: {e}")

if __name__ == "__main__":
    print("📡 Fetching total invoice amount from Neon DB...")
    total_amount = get_total_invoice_amount()
    print(f"💰 Total Invoice Amount: ${total_amount:,.2f}")
    update_odoo(total_amount)
