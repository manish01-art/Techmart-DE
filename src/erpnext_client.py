import requests

from src.config import (
    ERPNEXT_URL,
    ERPNEXT_API_KEY,
    ERPNEXT_API_SECRET,
)


class ERPNextClient:

    def __init__(self):
        self.base_url = ERPNEXT_URL.rstrip("/")

        self.headers = {
            "Authorization": (
                f"token {ERPNEXT_API_KEY}:{ERPNEXT_API_SECRET}"
            ),
            "Accept": "application/json",
        }

    def get(self, endpoint, params=None):

        url = f"{self.base_url}/api/resource/{endpoint}"

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()
    
    def exists(self, endpoint, filters):

        params = {
            "filters": str(filters).replace("'", '"'),
            "fields": '["name"]',
            "limit_page_length": 1,
        }

        result = self.get(
            endpoint,
            params=params
        )

        return len(result.get("data", [])) > 0

    def post(self, endpoint, data):

        url = f"{self.base_url}/api/resource/{endpoint}"

        headers = {
            **self.headers,
            "Expect": "",
        }

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30,
        )

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        response.raise_for_status()

        return response.json()