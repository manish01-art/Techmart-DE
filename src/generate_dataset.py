import random
import json
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# CONFIG
# ============================================================

SEED = 42

CUSTOMER_COUNT = 10_000
PRODUCT_COUNT = 2_000
SUPPLIER_COUNT = 1_000

SALES_COUNT = 150_000
PURCHASE_COUNT = 75_000
INVENTORY_COUNT = 150_000

OUTPUT_DIR = Path("data/generated")

random.seed(SEED)
np.random.seed(SEED)

fake = Faker("en_IN")
Faker.seed(SEED)


# ============================================================
# HELPERS
# ============================================================

def save_parquet(df, filename):
    path = OUTPUT_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"Saved {len(df):,} rows -> {path}")


def random_dates(count, start="2024-01-01", end="2026-09-30"):
    start_ts = pd.Timestamp(start).timestamp()
    end_ts = pd.Timestamp(end).timestamp()

    timestamps = np.random.uniform(
        start_ts,
        end_ts,
        count
    )

    return pd.to_datetime(timestamps, unit="s")


# ============================================================
# CUSTOMERS
# ============================================================

def generate_customers():

    rows = []

    # Try to reuse ERPNext customer data if available.
    erp_files = list(
        Path("data/raw/customers").glob(
            "batch_id=*/customers.json"
        )
    )

    erp_customers = []

    for file in erp_files:

     try:
        with file.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        records = payload.get("data", [])

        if isinstance(records, list):
            erp_customers.extend(records)

     except (json.JSONDecodeError, OSError) as exc:
        print(f"Could not read {file}: {exc}")
        continue

    # Remove duplicate ERPNext customers.
    seen = set()

    clean_erp_customers = []

    for customer in erp_customers:

        name = customer.get("name")

        if name and name not in seen:
            seen.add(name)
            clean_erp_customers.append(customer)

    # Use existing ERPNext customers first.
    for customer in clean_erp_customers:

        rows.append({
            "customer_id": customer["name"],
            "customer_name": customer.get(
                "customer_name",
                customer["name"]
            ),
            "customer_type": customer.get(
                "customer_type",
                "Company"
            ),
            "customer_group": customer.get(
                "customer_group",
                "Commercial"
            ),
            "territory": customer.get(
                "territory",
                "India"
            ),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "created_at": fake.date_time_between(
                start_date="-2y",
                end_date="now"
            ),
        })

    # Fill remaining customers synthetically.
    while len(rows) < CUSTOMER_COUNT:

        customer_type = random.choice(
            ["Individual", "Company"]
        )

        if customer_type == "Company":
            name = fake.company()
        else:
            name = fake.name()

        customer_id = f"CUST-SYN-{len(rows) + 1:06d}"

        rows.append({
            "customer_id": customer_id,
            "customer_name": name,
            "customer_type": customer_type,
            "customer_group": random.choice([
                "Commercial",
                "Retail",
                "Wholesale",
                "Government",
            ]),
            "territory": random.choice([
                "India",
                "Rest Of The World",
            ]),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "created_at": fake.date_time_between(
                start_date="-2y",
                end_date="now"
            ),
        })

    return pd.DataFrame(rows)


# ============================================================
# PRODUCTS
# ============================================================

def generate_products():

    categories = [
        "Electronics",
        "Home Appliances",
        "Mobile Accessories",
        "Office Supplies",
        "Personal Care",
    ]

    rows = []

    for i in range(1, PRODUCT_COUNT + 1):

        category = random.choice(categories)

        rows.append({
            "product_id": f"PROD-{i:06d}",
            "product_name": f"{fake.word().title()} {fake.word().title()}",
            "category": category,
            "unit": random.choice([
                "Nos",
                "Box",
                "Kg",
                "Pack",
            ]),
            "unit_price": round(
                random.uniform(50, 100000),
                2
            ),
            "created_at": fake.date_time_between(
                start_date="-2y",
                end_date="now"
            ),
        })

    return pd.DataFrame(rows)


# ============================================================
# SUPPLIERS
# ============================================================

def generate_suppliers():

    rows = []

    for i in range(1, SUPPLIER_COUNT + 1):

        rows.append({
            "supplier_id": f"SUP-{i:06d}",
            "supplier_name": fake.company(),
            "city": fake.city(),
            "state": fake.state(),
            "country": random.choice([
                "India",
                "India",
                "India",
                "China",
                "UAE",
            ]),
            "email": fake.company_email(),
            "phone": fake.phone_number(),
            "created_at": fake.date_time_between(
                start_date="-2y",
                end_date="now"
            ),
        })

    return pd.DataFrame(rows)


# ============================================================
# SALES
# ============================================================

def generate_sales(customers, products):

    customer_ids = customers["customer_id"].tolist()
    product_ids = products["product_id"].tolist()

    dates = random_dates(SALES_COUNT)

    rows = {
        "order_id": [
            f"SO-{i:08d}"
            for i in range(1, SALES_COUNT + 1)
        ],
        "customer_id": np.random.choice(
            customer_ids,
            SALES_COUNT
        ),
        "product_id": np.random.choice(
            product_ids,
            SALES_COUNT
        ),
        "order_date": dates,
        "quantity": np.random.randint(
            1,
            50,
            SALES_COUNT
        ),
        "unit_price": np.round(
            np.random.uniform(
                50,
                100000,
                SALES_COUNT
            ),
            2
        ),
        "currency": np.random.choice(
            ["INR", "INR", "INR", "USD"],
            SALES_COUNT
        ),
        "status": np.random.choice(
            [
                "Completed",
                "Completed",
                "Completed",
                "Cancelled",
                "Pending",
            ],
            SALES_COUNT
        ),
    }

    df = pd.DataFrame(rows)

    df["total_amount"] = (
        df["quantity"] * df["unit_price"]
    ).round(2)

    return df


# ============================================================
# PURCHASES
# ============================================================

def generate_purchases(suppliers, products):

    supplier_ids = suppliers["supplier_id"].tolist()
    product_ids = products["product_id"].tolist()

    df = pd.DataFrame({
        "purchase_id": [
            f"PO-{i:08d}"
            for i in range(1, PURCHASE_COUNT + 1)
        ],
        "supplier_id": np.random.choice(
            supplier_ids,
            PURCHASE_COUNT
        ),
        "product_id": np.random.choice(
            product_ids,
            PURCHASE_COUNT
        ),
        "purchase_date": random_dates(
            PURCHASE_COUNT
        ),
        "quantity": np.random.randint(
            1,
            100,
            PURCHASE_COUNT
        ),
        "unit_cost": np.round(
            np.random.uniform(
                30,
                80000,
                PURCHASE_COUNT
            ),
            2
        ),
        "currency": np.random.choice(
            ["INR", "INR", "INR", "USD"],
            PURCHASE_COUNT
        ),
        "status": np.random.choice(
            [
                "Received",
                "Received",
                "Pending",
                "Cancelled",
            ],
            PURCHASE_COUNT
        ),
    })

    df["total_cost"] = (
        df["quantity"] * df["unit_cost"]
    ).round(2)

    return df


# ============================================================
# INVENTORY
# ============================================================

def generate_inventory(products):

    product_ids = products["product_id"].tolist()

    df = pd.DataFrame({
        "stock_entry_id": [
            f"ST-{i:08d}"
            for i in range(1, INVENTORY_COUNT + 1)
        ],
        "product_id": np.random.choice(
            product_ids,
            INVENTORY_COUNT
        ),
        "warehouse": np.random.choice(
            [
                "Delhi Warehouse",
                "Mumbai Warehouse",
                "Bangalore Warehouse",
            ],
            INVENTORY_COUNT
        ),
        "transaction_date": random_dates(
            INVENTORY_COUNT
        ),
        "quantity": np.random.randint(
            -100,
            500,
            INVENTORY_COUNT
        ),
        "movement_type": np.random.choice(
            [
                "Purchase",
                "Sale",
                "Transfer",
                "Adjustment",
            ],
            INVENTORY_COUNT
        ),
    })

    return df


# ============================================================
# DATA CORRUPTION
# ============================================================

def corrupt_customers(df):

    df = df.copy()

    n = len(df)

    # 2% whitespace problems
    idx = np.random.choice(
        n,
        int(n * 0.02),
        replace=False
    )

    df.loc[idx, "customer_name"] = (
        "  "
        + df.loc[idx, "customer_name"].astype(str)
        + "  "
    )

    # 1% casing problems
    idx = np.random.choice(
        n,
        int(n * 0.01),
        replace=False
    )

    df.loc[idx, "customer_name"] = (
        df.loc[idx, "customer_name"]
        .astype(str)
        .str.upper()
    )

    # 1% missing email
    idx = np.random.choice(
        n,
        int(n * 0.01),
        replace=False
    )

    df.loc[idx, "email"] = None

    # 0.5% malformed email
    idx = np.random.choice(
        n,
        int(n * 0.005),
        replace=False
    )

    df.loc[idx, "email"] = "invalid-email"

    # 0.5% duplicate rows
    duplicate_rows = df.sample(
        int(n * 0.005),
        random_state=SEED
    )

    df = pd.concat(
        [df, duplicate_rows],
        ignore_index=True
    )

    return df


def corrupt_sales(df):

    df = df.copy()

    n = len(df)

    # 1% missing customer IDs
    idx = np.random.choice(
        n,
        int(n * 0.01),
        replace=False
    )

    df.loc[idx, "customer_id"] = None

    # 0.5% orphan customer IDs
    idx = np.random.choice(
        n,
        int(n * 0.005),
        replace=False
    )

    df.loc[idx, "customer_id"] = [
        f"CUST-INVALID-{i}"
        for i in range(len(idx))
    ]

    # 1% negative quantities
    idx = np.random.choice(
        n,
        int(n * 0.01),
        replace=False
    )

    df.loc[idx, "quantity"] *= -1

    # 0.5% zero prices
    idx = np.random.choice(
        n,
        int(n * 0.005),
        replace=False
    )

    df.loc[idx, "unit_price"] = 0

    # 1% duplicate transactions
    duplicate_rows = df.sample(
        int(n * 0.01),
        random_state=SEED
    )

    df = pd.concat(
        [df, duplicate_rows],
        ignore_index=True
    )

    return df


def corrupt_products(df):

    df = df.copy()

    n = len(df)

    # Missing category
    idx = np.random.choice(
        n,
        int(n * 0.01),
        replace=False
    )

    df.loc[idx, "category"] = None

    # Inconsistent category casing
    idx = np.random.choice(
        n,
        int(n * 0.01),
        replace=False
    )

    df.loc[idx, "category"] = (
        df.loc[idx, "category"]
        .astype(str)
        .str.lower()
    )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("Starting dataset generation...")

    print("\nGenerating customers...")
    customers = generate_customers()

    print("\nGenerating products...")
    products = generate_products()

    print("\nGenerating suppliers...")
    suppliers = generate_suppliers()

    print("\nGenerating sales...")
    sales = generate_sales(
        customers,
        products
    )

    print("\nGenerating purchases...")
    purchases = generate_purchases(
        suppliers,
        products
    )

    print("\nGenerating inventory...")
    inventory = generate_inventory(
        products
    )

    print("\nIntroducing controlled data-quality problems...")

    customers = corrupt_customers(customers)
    products = corrupt_products(products)
    sales = corrupt_sales(sales)

    print("\nSaving datasets...")

    save_parquet(
        customers,
        "customers.parquet"
    )

    save_parquet(
        products,
        "products.parquet"
    )

    save_parquet(
        suppliers,
        "suppliers.parquet"
    )

    save_parquet(
        sales,
        "sales.parquet"
    )

    save_parquet(
        purchases,
        "purchases.parquet"
    )

    save_parquet(
        inventory,
        "inventory.parquet"
    )

    print("\n===================================")
    print("DATASET GENERATION COMPLETE")
    print("===================================")

    print(
        f"Customers : {len(customers):,}"
    )

    print(
        f"Products  : {len(products):,}"
    )

    print(
        f"Suppliers : {len(suppliers):,}"
    )

    print(
        f"Sales     : {len(sales):,}"
    )

    print(
        f"Purchases : {len(purchases):,}"
    )

    print(
        f"Inventory : {len(inventory):,}"
    )


if __name__ == "__main__":
    main()