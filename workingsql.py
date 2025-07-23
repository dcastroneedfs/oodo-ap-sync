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
    # Authenticate to get the user ID
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
    
    uid = login_json["result"]["uid"]
    if not uid:
        print("❌ Failed to log in to Odoo (UID not found).")
        exit()

    print("✅ Logged into Odoo, updating field...")

    # Search for record(s) in your custom model
    search_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [
                odoo_db,
                uid,
                odoo_pass,
                "x_ap_dashboard",
                "search",
                [[]]  # match all records
            ]
        },
        "id": 2
    }

    search_response = requests.post(f"{odoo_url}/jsonrpc", json=search_payload)
    record_ids = search_response.json().get("result", [])

    if not record_ids:
        print("⚠️ No records found in x_ap_dashboard.")
        exit()

    # Convert to float for serialization
    float_amount = float(total_amount)

    # Update the field
    update_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [
                odoo_db,
                uid,
                odoo_pass,
                "x_ap_dashboard",
                "write",
                [record_ids, {
                    "x_studio_float_field_44o_1j0pl01m9": float_amount
                }]
            ]
        },
        "id": 3
    }

    update_response = requests.post(f"{odoo_url}/jsonrpc", json=update_payload)
    if update_response.json().get("result", False):
        print("✅ Odoo field updated successfully!")
    else:
        print(f"❌ Failed to update Odoo: {update_response.json()}")
except Exception as e:
    print(f"❌ Error updating Odoo: {e}")
