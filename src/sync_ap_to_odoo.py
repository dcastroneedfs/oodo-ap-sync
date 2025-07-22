import os
import time
import requests

# Load environment variables
odoo_url = os.environ["ODOO_URL"]
odoo_user = os.environ["ODOO_USER"]
odoo_pass = os.environ["ODOO_PASS"]
odoo_db = os.environ["ODOO_DB"]

# New Mockaroo endpoint
mockaroo_url = "https://my.api.mockaroo.com/mock_ap2.json"
mockaroo_headers = {"X-API-Key": "1239ff60"}

# Custom field technical name
ap_field_name = "x_studio_float_field_44o_1j0pl01m9"

try:
    print("📡 Fetching data from Mockaroo...")
    response = requests.get(mockaroo_url, headers=mockaroo_headers)
    response.raise_for_status()
    data = response.json()

    print("🧮 Summing Balance Due...")
    balance_sum = 0.0
    for record in data:
        value = record.get("Balance Due")
        if isinstance(value, (int, float)):
            balance_sum += value
        else:
            try:
                balance_sum += float(str(value).replace(",", "").replace("$", ""))
            except:
                print(f"⚠️ Skipped invalid balance: {value}")

    print(f"💰 Total AP Balance: {balance_sum}")

    # Authenticate with Odoo
    print("🔐 Logging into Odoo...")
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
    auth_response.raise_for_status()
    uid = auth_response.json()["result"]["uid"]

    # Update field in first record of your model
    print("✍️ Updating Odoo model field...")
    update_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "x_ap_dashboard",
            "method": "write",
            "args": [[1], {ap_field_name: balance_sum}],
            "kwargs": {},
        },
        "id": 2
    }

    update_headers = {
        "Content-Type": "application/json",
        "Cookie": auth_response.headers.get("Set-Cookie")
    }

    update_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=update_payload, headers=update_headers)
    update_response.raise_for_status()

    print("✅ AP Balance updated in Odoo!")

except Exception as e:
    print(f"❌ Error: {e}")
