import os
import requests
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("ERPNEXT_URL")
api_key = os.getenv("ERPNEXT_API_KEY")
api_secret = os.getenv("ERPNEXT_API_SECRET")

headers = {
    "Authorization": f"token {api_key}:{api_secret}",
    "Accept": "application/json",
}

url = f"{base_url}/api/method/frappe.auth.get_logged_user"

response = requests.get(url, headers=headers)

print("Status:", response.status_code)
print("Response:", response.json())