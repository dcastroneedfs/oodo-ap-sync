import requests
import json
import os

# 🌐 Load environment variables
odoo_url = os.environ['ODOO_URL']
odoo_user = os.environ['ODOO_USER']
odoo_pass = os.environ['ODOO_PASS']
odoo_db   = os.environ['ODOO_DB']

# 🔐 Login to Odoo
login_url = f"{odoo_url}/web/session/authenticate"
login_payload = {
    "params": {
        "db": odoo_db,
        "login": odoo_user,
        "password": odoo_pass
    }
}
login_response = requests.post(login_url, json=login_payload)
login_response.raise_for_status()
session_id = login_response.cookies.get("session_id")
headers = {
    "Content-Type": "application/json",
    "Cookie": f"session_id={session_id}"
}

# 📥 Fetch data from Mockaroo
mockaroo_url = "https://my.api.mockaroo.com/mock_ap.json"
mockaroo_headers = {
    "X-API-Key": "1239ff60",
    "Accept": "application/json"
}
mockaroo_response = requests.get(mockaroo_url, headers=mockaroo_headers)
mockaroo_response.raise_for_status()

try:
    data = mockaroo_response.json()
except Exception as e:
    print("❌ Error decoding JSON:", e)
    print("🔎 Response content:", mockaroo_response.text)
    exit(1)

# ➕ Sum the balance_due field
total_balance_due = sum(item.get("balance_due", 0) for item in data if isinstance(item.get("balance_due", 0), (int, float)))

# 🧾 Update Odoo field
write_url = f"{odoo_url}/web/dataset/call_kw"
write_payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "x_ap_dashboard",
        "method": "write",
        "args": [[1], {"x_studio_float_field_44o_1j0pl01m9": total_balance_due}],
        "kwargs": {}
    },
    "id": 1
}
write_response = requests.post(write_url, headers=headers, json=write_payload)
write_response.raise_for_status()

print(f"✅ Updated Odoo field with total AP balance: {total_balance_due}")
