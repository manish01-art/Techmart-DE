from src.erpnext_client import ERPNextClient
from src.logger import get_logger


logger = get_logger(__name__)

client = ERPNextClient()

customers = client.get_all(
    "Customer",
    params={
        "fields": '["name", "customer_name", "territory"]'
    },
    page_size=100
)

customers_to_change = customers[:10]

territories = [
    "India",
    "Rest Of The World",
]


for index, customer in enumerate(customers_to_change):

    current_territory = customer["territory"]

    new_territory = (
        "Rest Of The World"
        if current_territory == "India"
        else "India"
    )

    client.put(
        "Customer",
        customer["name"],
        {
            "territory": new_territory
        }
    )

    logger.info(
        "Updated customer | name=%s | old_territory=%s | new_territory=%s",
        customer["name"],
        current_territory,
        new_territory
    )


logger.info(
    "Customer change generation completed | updated=%s",
    len(customers_to_change)
)