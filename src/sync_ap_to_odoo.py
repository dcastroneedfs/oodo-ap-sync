import os
import psycopg2
import requests

# Load from environment
ODOO_URL = os.environ['ODOO_URL']
ODOO_USERNAME = os.environ['ODOO_USERNAME']
ODOO_PASSWORD = os.environ['ODOO_PASSWORD']
DATABASE_URL = os.environ['DATABASE_URL']

# Hardcoded Odoo field name
ODOO_FIELD = 'x_studio_total_ap'

def fetch_total_invoice_amount():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT SUM(invoice_amount) FROM invoices;")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
        return total if total else 0.0
    except Exception as e:
        print(f"❌ Database error: {e}")
        return 0.0

def update_odoo_field(total_amount):
    # Step 1: Authenticate
    auth_response = requests.post(f'{ODOO_URL}/web/session/authenticate', json={
        "jsonrpc": "2.0",
        "params": {
            "db": "dummy",  # Required by Odoo even if ignored on SaaS
            "login": ODOO_USERNAME,
            "password": ODOO_PASSWORD
        }
    })

    if auth_response.status_code != 200 or 'result' not in auth_response.json():
        print("❌ Failed to authenticate with Odoo.")
        return

    uid = auth_response.json()['result']['uid']
    session_id = auth_response.cookies['session_id']

    # Step 2: Update Odoo record
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }

    update_response = requests.post(f'{ODOO_URL}/web/dataset/call_kw/ap.dash/write', json={
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "ap.dash",
            "method": "write",
            "args": [[1], {ODOO_FIELD: total_amount}],
            "kwargs": {}
        }
    }, headers=headers)

    if update_response.status_code == 200:
        print(f"✅ Pushed ${total_amount:,.2f} to Odoo field '{ODOO_FIELD}'")
    else:
        print(f"❌ Failed to update Odoo: {update_response.text}")

if __name__ == "__main__":
    print("📡 Fetching total invoice amount from Neon DB...")
    total = fetch_total_invoice_amount()
    print(f"💰 Total Invoice Amount: ${total:,.2f}")
    print("🔐 Updating Odoo...")
    update_odoo_field(total)
