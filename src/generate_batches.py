import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


SOURCE_DIR = Path("data/generated")
BATCH_DIR = Path("data/source_batches")

np.random.seed(42)


def create_batch(batch_name, extracted_at):
    batch_id = str(uuid.uuid4())

    batch_dir = BATCH_DIR / f"batch_id={batch_id}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "batch_id": batch_id,
        "batch_name": batch_name,
        "source_system": "Synthetic ERPNext Source",
        "extracted_at": extracted_at,
        "schema_version": 1,
    }

    return batch_id, batch_dir, metadata


def main():
    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    customers = pd.read_parquet(SOURCE_DIR / "customers.parquet")
    products = pd.read_parquet(SOURCE_DIR / "products.parquet")
    suppliers = pd.read_parquet(SOURCE_DIR / "suppliers.parquet")
    sales = pd.read_parquet(SOURCE_DIR / "sales.parquet")
    purchases = pd.read_parquet(SOURCE_DIR / "purchases.parquet")
    inventory = pd.read_parquet(SOURCE_DIR / "inventory.parquet")

    # ---------------------------------------------------------
    # BATCH 001 - INITIAL LOAD
    # ---------------------------------------------------------

    batch_id, batch_dir, metadata = create_batch(
        "initial_load",
        "2026-09-30T09:00:00"
    )

    for name, df in {
        "customers": customers,
        "products": products,
        "suppliers": suppliers,
        "sales": sales,
        "purchases": purchases,
        "inventory": inventory,
    }.items():
        df.to_parquet(batch_dir / f"{name}.parquet", index=False)

    with open(batch_dir / "batch_metadata.json", "w") as f:
        json.dump(
            {
                **metadata,
                "record_counts": {
                    name: len(df)
                    for name, df in {
                        "customers": customers,
                        "products": products,
                        "suppliers": suppliers,
                        "sales": sales,
                        "purchases": purchases,
                        "inventory": inventory,
                    }.items()
                },
            },
            f,
            indent=2,
        )

    print(f"Created Batch 001 | {batch_id}")

    # ---------------------------------------------------------
    # BATCH 002 - INCREMENTAL + UPDATES + LATE DATA
    # ---------------------------------------------------------

    batch_id, batch_dir, metadata = create_batch(
        "incremental_001",
        "2026-10-02T09:00:00"
    )

    # New sales
    new_sales = sales.sample(5000, random_state=10).copy()
    new_sales["order_id"] = [
        f"SO-B002-{i:06d}" for i in range(1, len(new_sales) + 1)
    ]

    new_sales["order_date"] = pd.Timestamp("2026-10-01") + pd.to_timedelta(
        np.random.randint(0, 48 * 60, len(new_sales)),
        unit="m",
    )

    # New purchases
    new_purchases = purchases.sample(2500, random_state=11).copy()
    new_purchases["purchase_id"] = [
        f"PO-B002-{i:06d}" for i in range(1, len(new_purchases) + 1)
    ]

    # Customer updates → SCD2 later
    customer_updates = customers.sample(100, random_state=12).copy()

    customer_updates["territory"] = np.where(
        customer_updates["territory"].eq("India"),
        "Rest Of The World",
        "India",
    )

    # Soft deletes
    deleted_customers = customers.sample(20, random_state=13).copy()
    deleted_customers["is_deleted"] = True
    deleted_customers["deleted_at"] = "2026-10-02T08:30:00"

    # Late-arriving sales
    late_sales = new_sales.sample(100, random_state=14).copy()
    late_sales["order_date"] = (
        pd.Timestamp("2026-09-25")
        + pd.to_timedelta(
            np.random.randint(0, 24 * 60, len(late_sales)),
            unit="m",
        )
    )
    late_sales["is_late_arriving"] = True

    # Schema evolution: new column appears
    new_sales["discount_amount"] = np.round(
        new_sales["total_amount"] * np.random.uniform(0, 0.15, len(new_sales)),
        2,
    )

    new_sales.to_parquet(batch_dir / "sales.parquet", index=False)
    new_purchases.to_parquet(batch_dir / "purchases.parquet", index=False)
    customer_updates.to_parquet(
        batch_dir / "customer_updates.parquet",
        index=False,
    )
    deleted_customers.to_parquet(
        batch_dir / "customer_deletes.parquet",
        index=False,
    )
    late_sales.to_parquet(
        batch_dir / "late_sales.parquet",
        index=False,
    )

    with open(batch_dir / "batch_metadata.json", "w") as f:
        json.dump(
            {
                **metadata,
                "schema_version": 2,
                "record_counts": {
                    "sales": len(new_sales),
                    "purchases": len(new_purchases),
                    "customer_updates": len(customer_updates),
                    "customer_deletes": len(deleted_customers),
                    "late_sales": len(late_sales),
                },
                "changes": [
                    "new records",
                    "customer updates",
                    "soft deletes",
                    "late-arriving records",
                    "schema evolution: discount_amount added to sales",
                ],
            },
            f,
            indent=2,
        )

    print(f"Created Batch 002 | {batch_id}")

    # ---------------------------------------------------------
    # BATCH 003 - ANOTHER INCREMENTAL LOAD
    # ---------------------------------------------------------

    batch_id, batch_dir, metadata = create_batch(
        "incremental_002",
        "2026-10-04T09:00:00"
    )

    newer_sales = sales.sample(3000, random_state=20).copy()
    newer_sales["order_id"] = [
        f"SO-B003-{i:06d}" for i in range(1, len(newer_sales) + 1)
    ]

    newer_sales["order_date"] = pd.Timestamp("2026-10-03") + pd.to_timedelta(
        np.random.randint(0, 24 * 60, len(newer_sales)),
        unit="m",
    )

    newer_sales["discount_amount"] = np.round(
        newer_sales["total_amount"] * np.random.uniform(0, 0.20, len(newer_sales)),
        2,
    )

    customer_updates_2 = customers.sample(50, random_state=21).copy()

    customer_updates_2["territory"] = np.where(
        customer_updates_2["territory"].eq("India"),
        "Rest Of The World",
        "India",
    )

    newer_sales.to_parquet(
        batch_dir / "sales.parquet",
        index=False,
    )

    customer_updates_2.to_parquet(
        batch_dir / "customer_updates.parquet",
        index=False,
    )

    with open(batch_dir / "batch_metadata.json", "w") as f:
        json.dump(
            {
                **metadata,
                "schema_version": 2,
                "record_counts": {
                    "sales": len(newer_sales),
                    "customer_updates": len(customer_updates_2),
                },
                "changes": [
                    "new incremental records",
                    "additional customer updates",
                ],
            },
            f,
            indent=2,
        )

    print(f"Created Batch 003 | {batch_id}")

    print("\nSource batch generation completed.")


if __name__ == "__main__":
    main()