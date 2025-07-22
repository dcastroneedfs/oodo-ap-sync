import os
import psycopg2
import requests
from decimal import Decimal

# Load env variables
odoo_url = os.environ["ODOO_URL"]
odoo_user = os.environ["ODOO_USER"]
odoo_pass = os.environ["ODOO_PASS"]
odoo_db = os.environ["ODOO_DB"]
database_url = os.environ["DATABASE_URL"]

print("📡 Fetching total invoice amount from Neon DB...")

try:
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("SELECT SUM(invoice_amount) FROM invoices")
    result = cur.fetchone()
    total_amount = result[0] or Decimal("0.0")
    print(f"💰 Total Invoice Amount: ${total_amount:,.2f}")
except Exception as e:
    print(f"❌ Failed to fetch invoice total: {e}")
    exit()

print("🔐 Logging into Odoo...")

try:
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

    login_response = requests.post(f"{odoo_url}/web/session/authenticate", json=login_payload)
    login_json = login_response.json()

    if "result" not in login_json or "session_id" not in login_json["result"]:
        print(f"❌ Error updating Odoo: 'session_id' not found in login response")
        exit()

    uid = login_json["result"]["uid"]
    session_id = login_json["result"]["session_id"]
    headers = {"Cookie": f"session_id={session_id}"}

    print("✅ Logged into Odoo, updating field...")

    # Search for records in x_ap_dashboard
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

    search_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=search_payload, headers=headers).json()
    record_ids = search_response.get("result", [])

    if not record_ids:
        print("⚠️ No records found to update.")
        exit()

    # Convert Decimal to float explicitly
    float_amount = float(total_amount)

    # Update the custom float field
    update_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "x_ap_dashboard",
            "method": "write",
            "args": [record_ids, {
                "x_studio_float_field_44o_1j0pl01m9": float_amount
            }],
            "kwargs": {}
        },
        "id": 3
    }

    update_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=update_payload, headers=headers).json()

    if update_response.get("result", False):
        print("✅ Odoo field updated successfully!")
    else:
        print(f"❌ Failed to update Odoo: {update_response}")
except Exception as e:
    print(f"❌ Error updating Odoo: {e}")
