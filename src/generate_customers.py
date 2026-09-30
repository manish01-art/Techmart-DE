from faker import Faker

from src.erpnext_client import ERPNextClient
from src.logger import get_logger


logger = get_logger(__name__)

fake = Faker()
Faker.seed(42)

client = ERPNextClient()

CUSTOMER_COUNT = 100


for i in range(1, CUSTOMER_COUNT + 1):

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

        logger.info(
            "Skipped existing customer: %s",
            customer_name
        )

        continue

    result = client.post(
        "Customer",
        customer_data
    )

    logger.info(
        "Created customer: %s",
        result["data"]["name"]
    )


logger.info(
    "Customer generation completed | requested=%s",
    CUSTOMER_COUNT
)