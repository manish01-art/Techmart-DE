import uuid
import json
from pathlib import Path
from datetime import datetime, timezone

from src.erpnext_client import ERPNextClient
from src.watermark import load_watermark, save_watermark

client = ERPNextClient()

watermark = load_watermark("Customer")

print(f"Previous watermark: {watermark}")

params = {
    "fields": '["name", "customer_name", "customer_type", "customer_group", "territory","modified"]'
}

if watermark:
    params["filters"] = str([
        ["modified", ">", watermark]
    ]).replace("'", '"')


customers = client.get_all(
    "Customer",
    params=params,
    page_size=5
)

new_watermark = watermark

if customers:
    new_watermark = max(
        customer["modified"]
        for customer in customers
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

output_path = (
    Path("data/raw/customers")
    / f"batch_id={batch_id}"
    / "customers.json"
)

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

save_watermark(
    "Customer",
    new_watermark
)

print(f"Extracted {len(customers)} customers")
print(f"Batch ID: {batch_id}")
print(f"Saved to {output_path}")