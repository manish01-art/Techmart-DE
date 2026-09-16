from faker import Faker

from src.erpnext_client import ERPNextClient


fake = Faker()
Faker.seed(42)

client = ERPNextClient()

CUSTOMER_COUNT = 10


for _ in range(CUSTOMER_COUNT):

    customer_type = fake.random_element(
        elements=["Individual", "Company"]
    )

    if customer_type == "Company":
        customer_name = fake.company()
    else:
        customer_name = fake.name()

    customer_data = {
        "customer_name": customer_name,
        "customer_type": customer_type,
        "customer_group": "Commercial",
        "territory": "All Territories",
    }

    filters = {
        "customer_name": customer_name
    }

    if client.exists("Customer", filters):
        print(f"Skipped existing customer: {customer_name}")
        continue

    result = client.post("Customer", customer_data)

    print(f"Created customer: {result['data']['name']}")