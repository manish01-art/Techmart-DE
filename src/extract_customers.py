import uuid
import json
from pathlib import Path
from datetime import datetime, timezone

from src.erpnext_client import ERPNextClient


client = ERPNextClient()

params = {
    "fields": '["name", "customer_name", "customer_type", "customer_group", "territory"]'
}

customers = client.get_all(
    "Customer",
    params=params,
    page_size=5
)

batch_id = str(uuid.uuid4())
extracted_at = datetime.now(timezone.utc).isoformat()

output = {
    "source": "erpnext",
    "entity": "Customer",
    "batch_id": batch_id,
    "extracted_at": extracted_at,
    "record_count": len(customers),
    "data": customers,
}

output_path = Path("data/raw/customers.json")

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

with output_path.open("w", encoding="utf-8") as file:
    json.dump(
        output,
        file,
        indent=2,
        ensure_ascii=False
    )

print(f"Extracted {len(customers)} customers")
print(f"Saved to {output_path}")