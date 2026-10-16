from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    trim,
    upper,
    lower,
    lit,
    when,
    concat_ws,
    count,
    current_timestamp,
)
from pyspark.sql.window import Window


BASE_PATH = "data/generated"
SILVER_PATH = "data/silver"
QUARANTINE_PATH = "data/quarantine"


def clean_purchases(spark):
    print("\n========== PURCHASES ==========")

    df = spark.read.parquet(f"{BASE_PATH}/purchases.parquet")
    raw_count = df.count()

    # Standardization
    df = (
        df.withColumn("purchase_id", trim(col("purchase_id")))
        .withColumn("supplier_id", trim(col("supplier_id")))
        .withColumn("product_id", trim(col("product_id")))
        .withColumn("currency", upper(trim(col("currency"))))
        .withColumn("status", upper(trim(col("status"))))
    )

    # Reference data
    suppliers = (
        spark.read.parquet(f"{SILVER_PATH}/suppliers")
        .select("supplier_id")
        .dropDuplicates()
    )

    products = (
        spark.read.parquet(f"{SILVER_PATH}/products")
        .select("product_id")
        .dropDuplicates()
    )

    df = df.join(
        suppliers.withColumn("supplier_exists", lit(1)),
        on="supplier_id",
        how="left",
    )

    df = df.join(
        products.withColumn("product_exists", lit(1)),
        on="product_id",
        how="left",
    )

    # Duplicate detection
    duplicate_window = Window.partitionBy("purchase_id")

    df = df.withColumn(
        "duplicate_count",
        count("*").over(duplicate_window),
    )

    # DQ rules
    df = df.withColumn(
        "dq_reason",
        concat_ws(
            "; ",
            when(
                col("purchase_id").isNull() | (col("purchase_id") == ""),
                lit("missing_purchase_id"),
            ),
            when(
                col("supplier_id").isNull() | (col("supplier_id") == ""),
                lit("missing_supplier_id"),
            ),
            when(
                col("supplier_exists").isNull(),
                lit("orphan_supplier_id"),
            ),
            when(
                col("product_id").isNull() | (col("product_id") == ""),
                lit("missing_product_id"),
            ),
            when(
                col("product_exists").isNull(),
                lit("orphan_product_id"),
            ),
            when(
                col("quantity").isNull() | (col("quantity") <= 0),
                lit("invalid_quantity"),
            ),
            when(
                col("unit_cost").isNull() | (col("unit_cost") <= 0),
                lit("invalid_unit_cost"),
            ),
            when(
                ~col("currency").isin("INR", "USD", "EUR"),
                lit("unsupported_currency"),
            ),
            when(
                col("purchase_date").isNull(),
                lit("missing_purchase_date"),
            ),
            when(
                col("duplicate_count") > 1,
                lit("duplicate_purchase_id"),
            ),
        ),
    )

    df = df.withColumn(
        "dq_status",
        when(col("dq_reason") == "", lit("VALID"))
        .otherwise(lit("INVALID")),
    )

    df = df.withColumn("silver_processed_at", current_timestamp())

    valid = df.filter(col("dq_status") == "VALID").drop(
        "supplier_exists",
        "product_exists",
        "duplicate_count",
    )

    invalid = df.filter(col("dq_status") == "INVALID").drop(
        "supplier_exists",
        "product_exists",
        "duplicate_count",
    )

    valid.write.mode("overwrite").parquet(
        f"{SILVER_PATH}/purchases"
    )

    invalid.write.mode("overwrite").parquet(
        f"{QUARANTINE_PATH}/purchases"
    )

    valid_count = valid.count()
    invalid_count = invalid.count()

    print(f"Raw records        : {raw_count}")
    print(f"Valid records      : {valid_count}")
    print(f"Quarantined records: {invalid_count}")
    print(f"Accounting check   : {valid_count + invalid_count}/{raw_count}")


def clean_inventory(spark):
    print("\n========== INVENTORY ==========")

    df = spark.read.parquet(f"{BASE_PATH}/inventory.parquet")
    raw_count = df.count()

    # Standardization
    df = (
        df.withColumn("stock_entry_id", trim(col("stock_entry_id")))
        .withColumn("product_id", trim(col("product_id")))
        .withColumn("warehouse", trim(col("warehouse")))
        .withColumn("movement_type", upper(trim(col("movement_type"))))
    )

    # Reference data
    products = (
        spark.read.parquet(f"{SILVER_PATH}/products")
        .select("product_id")
        .dropDuplicates()
    )

    df = df.join(
        products.withColumn("product_exists", lit(1)),
        on="product_id",
        how="left",
    )

    # Duplicate detection
    duplicate_window = Window.partitionBy("stock_entry_id")

    df = df.withColumn(
        "duplicate_count",
        count("*").over(duplicate_window),
    )

    # DQ rules
    df = df.withColumn(
        "dq_reason",
        concat_ws(
            "; ",
            when(
                col("stock_entry_id").isNull()
                | (col("stock_entry_id") == ""),
                lit("missing_stock_entry_id"),
            ),
            when(
                col("product_id").isNull()
                | (col("product_id") == ""),
                lit("missing_product_id"),
            ),
            when(
                col("product_exists").isNull(),
                lit("orphan_product_id"),
            ),
            when(
                col("warehouse").isNull()
                | (col("warehouse") == ""),
                lit("missing_warehouse"),
            ),
            when(
                col("transaction_date").isNull(),
                lit("missing_transaction_date"),
            ),
            when(
                col("quantity").isNull()
                | (col("quantity") == 0),
                lit("invalid_quantity"),
            ),
            when(
                ~col("movement_type").isin(
                    "PURCHASE",
                    "SALE",
                    "ADJUSTMENT",
                    "TRANSFER",
                ),
                lit("invalid_movement_type"),
            ),
            when(
                col("duplicate_count") > 1,
                lit("duplicate_stock_entry_id"),
            ),
        ),
    )

    df = df.withColumn(
        "dq_status",
        when(col("dq_reason") == "", lit("VALID"))
        .otherwise(lit("INVALID")),
    )

    df = df.withColumn("silver_processed_at", current_timestamp())

    valid = df.filter(col("dq_status") == "VALID").drop(
        "product_exists",
        "duplicate_count",
    )

    invalid = df.filter(col("dq_status") == "INVALID").drop(
        "product_exists",
        "duplicate_count",
    )

    valid.write.mode("overwrite").parquet(
        f"{SILVER_PATH}/inventory"
    )

    invalid.write.mode("overwrite").parquet(
        f"{QUARANTINE_PATH}/inventory"
    )

    valid_count = valid.count()
    invalid_count = invalid.count()

    print(f"Raw records        : {raw_count}")
    print(f"Valid records      : {valid_count}")
    print(f"Quarantined records: {invalid_count}")
    print(f"Accounting check   : {valid_count + invalid_count}/{raw_count}")


def main():
    spark = (
        SparkSession.builder
        .appName("TechMart-Silver-Transactions")
        .master("local[*]")
        .getOrCreate()
    )

    clean_purchases(spark)
    clean_inventory(spark)

    spark.stop()


if __name__ == "__main__":
    main()
