import os
import requests
from dotenv import load_dotenv

# Load env vars
load_dotenv()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_LOGIN = os.getenv("ODOO_LOGIN")
ODOO_API_KEY = os.getenv("ODOO_API_KEY")

# Optional - replace this with your logic to fetch data (e.g., from Neon)
def fetch_total_invoice_amount():
    # For example purposes
    return 28583.26

# Sync AP value to Odoo
def update_odoo_field(value):
    login_url = f"{ODOO_URL}/web/session/authenticate"
    headers = {'Content-Type': 'application/json'}
    auth_payload = {
        "params": {
            "db": ODOO_DB,
            "login": ODOO_LOGIN,
            "password": ODOO_API_KEY
        }
    }

    print("🔐 Authenticating with Odoo using API Key...")
    response = requests.post(login_url, json=auth_payload, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to authenticate: {response.status_code} - {response.text}")
        return

    result = response.json().get("result")
    if not result or not result.get("session_id"):
        print("❌ Authentication failed: No session_id returned")
        return

    session_id = result["session_id"]
    uid = result["uid"]

    # Now update the field
    update_url = f"{ODOO_URL}/web/dataset/call_kw/x_ap_dashboard/write"
    update_payload = {
        "args": [[1], {  # assumes record ID 1
            "x_studio_float_field_44o_1j0pl01m9": value
        }],
        "kwargs": {},
        "model": "x_ap_dashboard",
        "method": "write"
    }

    update_headers = {
        "Content-Type": "application/json",
        "Cookie": f"session_id={session_id}"
    }

    print("📡 Updating AP total in Odoo...")
    update_response = requests.post(update_url, json=update_payload, headers=update_headers)

    if update_response.status_code == 200:
        print("✅ Successfully updated Odoo field.")
    else:
        print(f"❌ Failed to update Odoo: {update_response.status_code} - {update_response.text}")

if __name__ == "__main__":
    print("📡 Fetching total invoice amount from Neon DB...")
    total = fetch_total_invoice_amount()
    print(f"💰 Total Invoice Amount: ${total:,.2f}")
    update_odoo_field(total)
