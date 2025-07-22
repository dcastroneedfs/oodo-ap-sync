import requests
import xmlrpc.client

# === ODOO CONFIGURATION ===
odoo_url = "https://needfstrial.odoo.com"
db = "needfstrial"

import os

username = os.getenv("ODOO_USER")
password = os.getenv("ODOO_PASS")


# === ODOO CUSTOM MODEL DETAILS ===
model_name = "x_ap_dashboard"     # ← replace if your model name is different
target_field = "x_studio_float_field_44o_1j0pl01m9"  # ← field to update with AP total

# === MOCKAROO CONFIGURATION ===
mockaroo_url = "https://my.api.mockaroo.com/mock_ap.json?key=1239ff60"

# === STEP 1: FETCH AP TOTAL FROM MOCKAROO ===
try:
    response = requests.get(mockaroo_url)
    response.raise_for_status()
    data = response.json()

    # Assuming Mockaroo returns a list of dicts with 'ap_total'
    ap_total = data[0].get("ap_total", 0)
    print("✅ Fetched AP total from Mockaroo:", ap_total)

except Exception as e:
    print("❌ Error fetching data from Mockaroo:", e)
    exit(1)

# === STEP 2: AUTHENTICATE WITH ODOO ===
try:
    common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise Exception("Invalid Odoo credentials")

    print("🔑 Authenticated with Odoo")

except Exception as e:
    print("❌ Failed to authenticate with Odoo:", e)
    exit(1)

# === STEP 3: PUSH DATA INTO ODOO ===
try:
    models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

    # Find the first record in your custom model
    ids = models.execute_kw(db, uid, password, model_name, 'search', [[]], {'limit': 1})
    
    if not ids:
        print("⚠️ No records found in the model to update.")
        exit(0)

    # Update the record with new AP total
    models.execute_kw(db, uid, password, model_name, 'write', [ids, {target_field: ap_total}])
    print("✅ Successfully updated Odoo with new AP total:", ap_total)

except Exception as e:
    print("❌ Error updating Odoo:", e)

