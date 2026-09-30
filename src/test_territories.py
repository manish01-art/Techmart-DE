from src.erpnext_client import ERPNextClient


client = ERPNextClient()

territories = client.get_all(
    "Territory",
    params={
        "fields": '["name"]'
    },
    page_size=100
)

for territory in territories:
    print(territory["name"])