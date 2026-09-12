import os
from dotenv import load_dotenv

load_dotenv()

ERPNEXT_URL = os.getenv("ERPNEXT_URL")
ERPNEXT_API_KEY = os.getenv("ERPNEXT_API_KEY")
ERPNEXT_API_SECRET = os.getenv("ERPNEXT_API_SECRET")

if not all([ERPNEXT_URL, ERPNEXT_API_KEY, ERPNEXT_API_SECRET]):
    raise ValueError("Missing ERPNext environment variables")