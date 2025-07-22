import os
import requests
import xmlrpc.client

# Load environment variables
odoo_url = os.environ['ODOO_URL']
odoo_db = os.environ['ODOO_DB']
odoo_user = os.environ['ODOO_USER']
odoo_pass = os.environ['ODOO_PASS']

# Authenticate with Odoo
common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
uid = common.authenticate(odoo_db, odoo_user, odoo_pass, {})
models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

# Fetch data from Mockaroo
try:
    mockaroo_url = "https://my.api.mockaroo.com/mock_ap.json?key=1239ff60"
    headers = { "X-API-Key": "1239ff60" }
    response = requests.get(mockaroo_url, headers=headers)
    response.raise_for_status()
    mock_data = response.json()
except Exception as e:
    print(f"❌ Error fetching data: {e}")
    exit()

# Sum the 'balance_due' values
try:
    total_ap = sum(float(item.get('balance_due', 0)) for item in mock_data)
    print(f"🔢 Total AP: {total_ap}")
except Exception as e:
    print(f"❌ Error processing data: {e}")
    exit()

# Update Odoo model field
try:
    # Replace with your actual model name and field technical name
    model_name = 'x_ap_dashboard'
    field_name = 'x_studio_float_field_44o_1j0pl01m9'

    # Find the first record (or create one if needed)
    records = models.execute_kw(odoo_db, uid, odoo_pass, model_name, 'search', [[]])
    
    if records:
        # Update existing
        models.execute_kw(odoo_db, uid, odoo_pass, model_name, 'write', [[records[0]], {field_name: total_ap}])
    else:
        # Create new
        models.execute_kw(odoo_db, uid, odoo_pass, model_name, 'create', [{field_name: total_ap}])
    
    print("✅ Odoo updated successfully.")
except Exception as e:
    print(f"❌ Error updating Odoo: {e}")
