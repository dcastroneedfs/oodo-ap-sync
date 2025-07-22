import requests
import json
import os
import time

import os
import requests

# Debug
print("🔍 Loaded env keys:", list(os.environ.keys()))

# Environment variables
odoo_url = os.environ['ODOO_URL']
odoo_db = os.environ['ODOO_DB']
odoo_user = os.environ['ODOO_USER']
odoo_pass = os.environ['ODOO_PASS']

# Mockaroo URL and API key (header style)
mockaroo_url = "https://my.api.mockaroo.com/mock_ap.json"
headers = {
    "X-API-Key": "1239ff60"
}

while True:
    try:
        # 🔄 Fetch from Mockaroo
        response = requests.get(mockaroo_url, headers=headers)
        response.raise_for_status()
        mock_data = response.json()

        # 🧮 Sum AP amounts
        total_ap = sum(entry.get("amount", 0) for entry in mock_data)

        print(f"✅ Total AP: {total_ap}")

        # 🔐 Login to Odoo
        login_payload = {
            "jsonrpc": "2.0",
            "params": {
                "db": odoo_db,
                "login": odoo_user,
                "password": odoo_pass
            }
        }
        login_response = requests.post(f"{odoo_url}/web/session/authenticate", json=login_payload)
        login_response.raise_for_status()
        session_id = login_response.cookies.get("session_id")

        # 📤 Push to Odoo custom field
        update_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "x_ap_dashboard",
                "method": "search",
                "args": [[[]]],
                "kwargs": {},
            },
            "id": 1
        }

        headers_with_session = {
            "Content-Type": "application/json",
            "Cookie": f"session_id={session_id}"
        }

        search_response = requests.post(f"{odoo_url}/jsonrpc", json=update_payload, headers=headers_with_session)
        search_response.raise_for_status()
        record_ids = search_response.json()['result']

        if record_ids:
            record_id = record_ids[0]
            update_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": "x_ap_dashboard",
                    "method": "write",
                    "args": [[record_id], {
                        "x_studio_float_field_44o_1j0pl01m9": total_ap
                    }],
                    "kwargs": {}
                },
                "id": 2
            }

            update_response = requests.post(f"{odoo_url}/jsonrpc", json=update_data, headers=headers_with_session)
            update_response.raise_for_status()
            print("✅ Odoo updated.")

        else:
            print("⚠️ No record found in Odoo to update.")

    except Exception as e:
        print(f"❌ Error: {e}")

    time.sleep(60)
