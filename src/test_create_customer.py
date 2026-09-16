from src.erpnext_client import ERPNextClient


client = ERPNextClient()

customer_data = {
    "customer_name": "Test Customer 001",
    "customer_group": "commercial",
    "territory": "All Territories",
    "customer_type": "Individual",
}

result = client.post(
    "Customer",
    customer_data
)

print("Created customer:")
print(result["data"]["name"])