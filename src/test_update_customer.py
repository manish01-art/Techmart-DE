import requests

from src.erpnext_client import ERPNextClient


client = ERPNextClient()

customers = client.get_all(
    "Customer",
    params={
        "fields": '["name", "customer_name", "territory"]'
    },
    page_size=1
)

customer = customers[0]

print("Before:")
print(customer)

try:
    result = client.put(
        "Customer",
        customer["name"],
        {
            "territory": "India"
        }
    )

    print("After:")
    print(result["data"])

except requests.HTTPError as exc:
    print("STATUS:", exc.response.status_code)
    print("ERPNext response:")
    print(exc.response.text)