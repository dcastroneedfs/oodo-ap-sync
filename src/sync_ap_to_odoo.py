import os
import requests
import json

# 🔑 Environment Variables from Render Dashboard
odoo_url = os.environ["ODOO_URL"]
odoo_db = os.environ["ODOO_DB"]
odoo_user = os.environ["ODOO_USER"]
odoo_pass = os.environ["ODOO_PASS"]

# 🌐 Mockaroo API details
mockaroo_url = "https://my.api.mockaroo.com/mock_ap3.json"
mockaroo_headers = {"X-API-Key": "1239ff60"}

print("📡 Fetching data from Mockaroo...")

try:
    response = requests.get(mockaroo_url, headers=mockaroo_headers)
    response.raise_for_status()
    mock_data = response.json()
except json.JSONDecodeError as e:
    print("❌ Error decoding JSON:", e)
    print("🔎 Response content:", response.text)
    exit()
except Exception as e:
    print("❌ Error fetching data:", e)
    exit()

# 🧮 Sum "Balance Due" from all records
total_balance_due = 0.0
for entry in mock_data:
    try:
        balance = float(entry.get("Balance Due", 0))
        total_balance_due += balance
    except (ValueError, TypeError):
        continue

print(f"✅ Total Balance Due: {total_balance_due}")

# 🔐 Authenticate with Odoo
print("🔐 Authenticating with Odoo...")
auth_payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "db": odoo_db,
        "login": odoo_user,
        "password": odoo_pass
    },
    "id": 1
}

auth_response = requests.post(f"{odoo_url}/web/session/authenticate", json=auth_payload)
if auth_response.status_code != 200 or "result" not in auth_response.json():
    print("❌ Failed to authenticate with Odoo:", auth_response.text)
    exit()

session = requests.Session()
session.cookies.update(auth_response.cookies)

# ✏️ Update the value in Odoo custom model
print("📤 Pushing total to Odoo...")
update_payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "x_ap_dashboard",
        "method": "search",
        "args": [[["id", "!=", 0]]],
        "kwargs": {}
    },
    "id": 2
}
search_response = session.post(f"{odoo_url}/web/dataset/call_kw", json=update_payload)
ids = search_response.json().get("result", [])

if ids:
    update_value_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "x_ap_dashboard",
            "method": "write",
            "args": [ids, {"x_studio_float_field_44o_1j0pl01m9": total_balance_due}],
            "kwargs": {}
        },
        "id": 3
    }
    write_response = session.post(f"{odoo_url}/web/dataset/call_kw", json=update_value_payload)
    if write_response.status_code == 200:
        print("🎉 Successfully updated AP total in Odoo!")
    else:
        print("❌ Failed to update AP total:", write_response.text)
else:
    print("⚠️ No AP Dashboard records found to update.")
