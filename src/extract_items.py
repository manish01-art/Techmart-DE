import json
from pathlib import Path

from src.erpnext_client import ERPNextClient


client = ERPNextClient()

params = {
    "fields": '["name", "item_name", "item_group", "stock_uom"]'
}

result = client.get(
    "Item",
    params=params
)

output_path = Path("data/raw/items.json")

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

with output_path.open("w", encoding="utf-8") as file:
    json.dump(
        result["data"],
        file,
        indent=2,
        ensure_ascii=False
    )

print(f"Extracted {len(result['data'])} items")
print(f"Saved to {output_path}")