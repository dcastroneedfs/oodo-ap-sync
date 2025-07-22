import os
import psycopg2
import requests

# Load environment variables
odoo_url = os.environ['ODOO_URL']
odoo_user = os.environ['ODOO_USER']
odoo_pass = os.environ['ODOO_PASS']
odoo_db = os.environ['ODOO_DB']
database_url = os.environ['DATABASE_URL']

print("📡 Fetching total invoice amount from Neon DB...")

# Connect to PostgreSQL and sum invoice_amount
try:
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("SELECT SUM(invoice_amount) FROM invoices;")
    total_amount = cur.fetchone()[0] or 0.0
    cur.close()
    conn.close()
    print(f"💰 Total Invoice Amount: ${total_amount:,.2f}")
except Exception as e:
    print(f"❌ Error fetching from Neon DB: {e}")
    total_amount = 0.0

# Log into Odoo
print("🔐 Logging into Odoo...")
login_payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "db": odoo_db,
        "login": odoo_user,
        "password": odoo_pass
    },
    "id": 1
}

try:
    login_response = requests.post(f"{odoo_url}/web/session/authenticate", json=login_payload)
    uid = login_response.json()["result"]["uid"]
    print("✅ Logged into Odoo, updating field...")

    # Update custom field
    headers = {
        "Content-Type": "application/json",
        "X-Openerp-Session-Id": login_response.cookies.get("session_id")
    }

    # Search for record in the custom model
    search_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "x_ap_dashboard",
            "method": "search",
            "args": [[]],
            "kwargs": {}
        },
        "id": 2
    }

    search_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=search_payload, headers=headers, cookies=login_response.cookies)
    record_ids = search_response.json()["result"]

    if record_ids:
        update_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "x_ap_dashboard",
                "method": "write",
                "args": [record_ids, {
                    "x_studio_float_field_44o_1j0pl01m9": total_amount
                }],
                "kwargs": {}
            },
            "id": 3
        }

        update_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=update_payload, headers=headers, cookies=login_response.cookies)
        print("✅ Odoo field updated successfully!")
    else:
        print("⚠️ No records found in model x_ap_dashboard.")
except Exception as e:
    print(f"❌ Failed to update Odoo: {e}")
