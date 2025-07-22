import os
import requests

# 🌍 Odoo credentials from environment variables
odoo_url = os.environ["ODOO_URL"]
odoo_db = os.environ["ODOO_DB"]
odoo_user = os.environ["ODOO_USER"]
odoo_pass = os.environ["ODOO_PASS"]

# 🔗 Mockaroo endpoint
mockaroo_url = "https://my.api.mockaroo.com/mock_ap4.json"
headers = {"X-API-Key": "1239ff60"}

try:
    print("📡 Fetching data from Mockaroo...")
    response = requests.get(mockaroo_url, headers=headers)
    response.raise_for_status()
    data = response.json()

    # 🧮 Sum 'Balance Due'
    total_due = 0.0
    for record in data:
        try:
            amount = float(record.get("Balance Due", 0))
            total_due += amount
        except (ValueError, TypeError):
            pass

    print(f"💰 Total Balance Due: {total_due}")

    # 🔐 Authenticate with Odoo
    print("🔑 Logging into Odoo...")
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
    uid = login_response.json()["result"]["uid"]
    print(f"✅ Logged in as user ID: {uid}")

    # 📤 Update Odoo model field
    print("📦 Updating Odoo custom field...")
    model = "x_ap_dashboard"  # Your custom model's technical name
    field_name = "x_studio_float_field_44o_1j0pl01m9"  # Your custom field technical name

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": model,
            "method": "search",
            "args": [[]],  # Find all records
            "kwargs": {}
        },
        "id": 2
    }
    search_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=payload, cookies=login_response.cookies)
    ids = search_response.json()["result"]
    
    if not ids:
        print("⚠️ No records found to update.")
    else:
        record_id = ids[0]
        update_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": "write",
                "args": [[record_id], {field_name: total_due}],
                "kwargs": {}
            },
            "id": 3
        }
        update_response = requests.post(f"{odoo_url}/web/dataset/call_kw", json=update_payload, cookies=login_response.cookies)
        print("✅ Odoo updated successfully!")

except requests.exceptions.RequestException as e:
    print(f"❌ Error fetching data: {e}")
except ValueError as e:
    print(f"❌ Error decoding JSON: {e}")
except Exception as e:
    print(f"❌ General error: {e}")
