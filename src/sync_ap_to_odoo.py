import os
import psycopg2
import requests
from decimal import Decimal

# Load environment variables
odoo_url = os.environ["ODOO_URL"]
odoo_user = os.environ["ODOO_USER"]
odoo_pass = os.environ["ODOO_PASS"]
odoo_db = os.environ["ODOO_DB"]
database_url = os.environ["DATABASE_URL"]

print("📡 Fetching total invoice amount from Neon DB...")

try:
    # Connect to the Neon (Postgres) database
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
    # Login to Odoo
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

    login_response = requests.post(f"{odoo_url}/web/session/authenticate", json=login_payload).json()
    uid = login_response["result"]["uid"]
    session_id = login_response["result"]["session_id"]
    headers = {"Cookie": f"session_id={session_id}"}

    print("✅ Logged into Odoo, updating field...")

    # Search for the record to update
    search_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "x_ap_dashboard",
            "method": "search",
            "args": [[]],  # Search all records
            "kwargs": {}
        },
        "id": 2
    }

    search_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=search_payload, headers=headers).json()
    record_ids = search_response["result"]

    if not record_ids:
        print("⚠️ No records found in x_ap_dashboard to update.")
        exit()

    # Update the float field with the invoice amount
    update_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "x_ap_dashboard",
            "method": "write",
            "args": [record_ids, {
                "x_studio_float_field_44o_1j0pl01m9": float(total_amount)
            }],
            "kwargs": {}
        },
        "id": 3
    }

    update_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=update_payload, headers=headers).json()

    if "result" in update_response and update_response["result"]:
        print("✅ Odoo field updated successfully!")
    else:
        print(f"❌ Failed to update Odoo: {update_response}")
except Exception as e:
    print(f"❌ Error updating Odoo: {e}")
