import requests
import os

def fetch_ap_total():
    try:
        url = "https://my.api.mockaroo.com/mock_ap?key=1239ff60"
        response = requests.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data:
            total_ap = sum(item.get("amount", 0) for item in data)
            print(f"✅ Total AP: {total_ap}")
            return total_ap
        else:
            print("❌ Unexpected data format from Mockaroo:", data)
            return None
    except Exception as e:
        print("❌ Error fetching data:", e)
        return None

def update_odoo_ap_total(ap_total):
    try:
        import xmlrpc.client

        url = os.environ["ODOO_URL"]
        db = os.environ["ODOO_DB"]
        username = os.environ["ODOO_USERNAME"]
        password = os.environ["ODOO_PASSWORD"]
        field = os.environ["ODOO_FIELD"]

        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})

        if not uid:
            print("❌ Failed to authenticate with Odoo")
            return

        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

        ids = models.execute_kw(db, uid, password,
            'x_ap_dashboard', 'search', [[]], {'limit': 1})

        if ids:
            models.execute_kw(db, uid, password,
                'x_ap_dashboard', 'write',
                [ids, {field: ap_total}]
            )
            print("✅ Odoo updated successfully.")
        else:
            print("❌ No record found to update.")
    except Exception as e:
        print("❌ Error updating Odoo:", e)

if __name__ == "__main__":
    total = fetch_ap_total()
    if total is not None:
        update_odoo_ap_total(total)
