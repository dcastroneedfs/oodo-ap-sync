import requests
import json
import re
import os
import time

# 🌐 Environment variables from Render
odoo_url = os.environ['ODOO_URL']
odoo_user = os.environ['ODOO_USER']
odoo_pass = os.environ['ODOO_PASS']
odoo_db   = os.environ['ODOO_DB']

# 📡 Step 1: Fetch data from Mockaroo
headers = {
    "X-API-Key": "1239ff60"
}
mockaroo_url = "https://my.api.mockaroo.com/mock_ap4.json"

print("📡 Fetching data from Mockaroo...")
try:
    response = requests.get(mockaroo_url, headers=headers)
    response.raise_for_status()
    data = response.json()
except json.JSONDecodeError as e:
    print(f"❌ Error decoding JSON: {e}")
    print(f"🔎 Response content: {response.text}")
    exit()
except requests.RequestException as e:
    print(f"❌ Error fetching data: {e}")
    exit()

# 🧮 Step 2: Sum 'Invoice Amount' across all records
total_invoice = 0.0
for idx, record in enumerate(data):
    raw = record.get("Invoice Amount", "")
    try:
        # Strip currency symbols and commas
        cleaned = re.sub(r"[^\d.]", "", str(raw))
        amount = float(cleaned) if cleaned else 0.0
        print(f"🧾 Row {idx + 1}: Parsed Invoice Amount = {amount}")
        total_invoice += amount
    except (ValueError, TypeError):
        print(f"⚠️ Row {idx + 1}: Could not parse amount: {raw}")

print(f"💰 Total Invoice Amount (All Vendors): {total_invoice}")

# 🔑 Step 3: Log in to Odoo
print("🔑 Logging into Odoo...")
login_url = f"{odoo_url}/web/session/authenticate"
payload = {
    "jsonrpc": "2.0",
    "params": {
        "db": odoo_db,
        "login": odoo_user,
        "password": odoo_pass
    }
}

try:
    session = requests.Session()
    login_res = session.post(login_url, json=payload)
    login_res.raise_for_status()
    user_id = login_res.json()["result"]["uid"]
    print(f"✅ Logged in as user ID: {user_id}")
except Exception as e:
    print(f"❌ Login failed: {e}")
    exit()

# 🧾 Step 4: Update custom field in Odoo
print("📦 Updating Odoo custom field...")

update_url = f"{odoo_url}/web/dataset/call_kw"
headers.update({"Content-Type": "application/json"})

# Replace with your actual model and field name
model_name = "x_ap_dashboard"  # custom model from Studio
field_name = "x_studio_float_field_44o_1j0pl01m9"  # technical field name
record_id = 1  # usually ID of the record you're updating (adjust as needed)

payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": model_name,
        "method": "write",
        "args": [[record_id], {field_name: total_invoice}],
        "kwargs": {},
    },
    "id": 1,
}

try:
    update_res = session.post(update_url, headers=headers, json=payload)
    update_res.raise_for_status()
    print("✅ Odoo updated successfully!")
except Exception as e:
    print(f"❌ Error updating Odoo: {e}")
