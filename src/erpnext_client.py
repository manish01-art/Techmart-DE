import requests


from src.config import (
    ERPNEXT_URL,
    ERPNEXT_API_KEY,
    ERPNEXT_API_SECRET,
)
from src.logger import get_logger

logger = get_logger(__name__)

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

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:

            logger.error(
                "GET request failed | endpoint=%s | error=%s",
                endpoint,
                exc
            )

            raise
    
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

        logger.info(
            "POST request to ERPNext endpoint=%s",
            endpoint
        )

        try:
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=30,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:

            logger.error(
                "POST request failed | endpoint=%s | error=%s",
                endpoint,
                exc
            )

            raise