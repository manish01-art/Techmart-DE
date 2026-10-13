from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    lit,
    when,
    concat_ws,
    count,
)
from pyspark.sql.window import Window


BRONZE_PATH = "data/source_batches"
CUSTOMER_PATH = "data/generated/customers.parquet"
PRODUCT_PATH = "data/generated/products.parquet"

SILVER_PATH = "data/silver/sales"
QUARANTINE_PATH = "data/quarantine/sales"


def main():

    spark = (
        SparkSession.builder
        .appName("TechMart-Silver-Sales")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    # --------------------------------------------------
    # READ BRONZE SALES
    # --------------------------------------------------

    sales_path = f"{BRONZE_PATH}/batch_id=*/sales.parquet"

    sales = (
        spark.read
        .option("mergeSchema", "true")
        .parquet(sales_path)
    )

    raw_count = sales.count()

    print(f"Raw sales records: {raw_count:,}")

    # --------------------------------------------------
    # READ MASTER DATA
    # --------------------------------------------------

    customers = (
        spark.read
        .parquet(CUSTOMER_PATH)
        .select("customer_id")
        .dropDuplicates()
        .withColumn("customer_exists", lit(True))
    )

    products = (
        spark.read
        .parquet(PRODUCT_PATH)
        .select("product_id")
        .dropDuplicates()
        .withColumn("product_exists", lit(True))
    )

    # --------------------------------------------------
    # DUPLICATE DETECTION
    # --------------------------------------------------

    duplicate_window = Window.partitionBy("order_id")

    sales_checked = (
        sales
        .join(customers, on="customer_id", how="left")
        .join(products, on="product_id", how="left")
        .withColumn(
            "dq_reason",
            concat_ws(
                "; ",

                when(
                    col("order_id").isNull(),
                    lit("missing_order_id")
                ),

                when(
                    col("customer_id").isNull(),
                    lit("missing_customer_id")
                ),

                when(
                    col("customer_id").isNotNull()
                    & col("customer_exists").isNull(),
                    lit("orphan_customer_id")
                ),

                when(
                    col("product_id").isNull(),
                    lit("missing_product_id")
                ),

                when(
                    col("product_id").isNotNull()
                    & col("product_exists").isNull(),
                    lit("orphan_product_id")
                ),

                when(
                    col("quantity") <= 0,
                    lit("invalid_quantity")
                ),

                when(
                    col("unit_price") <= 0,
                    lit("invalid_unit_price")
                ),

                when(
                    ~col("currency").isin("INR", "USD"),
                    lit("unsupported_currency")
                ),

                when(
                    col("order_date").isNull(),
                    lit("invalid_order_date")
                ),

                when(
                    (col("order_id").isNotNull())
                    & (count("*").over(duplicate_window) > 1),
                    lit("duplicate_order_id")
                ),
            ),
        )
        .withColumn(
            "dq_status",
            when(
                col("dq_reason") == "",
                lit("VALID")
            ).otherwise(
                lit("INVALID")
            )
        )
    )

    # --------------------------------------------------
    # SPLIT VALID / INVALID
    # --------------------------------------------------

    valid_sales = (
        sales_checked
        .filter(col("dq_status") == "VALID")
        .drop("customer_exists", "product_exists")
    )

    invalid_sales = (
        sales_checked
        .filter(col("dq_status") == "INVALID")
        .drop("customer_exists", "product_exists")
    )

    # --------------------------------------------------
    # WRITE SILVER
    # --------------------------------------------------

    valid_sales.write.mode("overwrite").parquet(
        SILVER_PATH
    )

    invalid_sales.write.mode("overwrite").parquet(
        QUARANTINE_PATH
    )

    # --------------------------------------------------
    # DATA QUALITY RESULTS
    # --------------------------------------------------

    valid_count = valid_sales.count()
    invalid_count = invalid_sales.count()

    print("\n========== SALES DQ RESULTS ==========")
    print(f"Raw records:        {raw_count:,}")
    print(f"Valid records:      {valid_count:,}")
    print(f"Quarantined:        {invalid_count:,}")
    print("--------------------------------------")
    print(
        f"Accounting check:   "
        f"{valid_count + invalid_count:,} / {raw_count:,}"
    )
    print("=======================================")

    spark.stop()


if __name__ == "__main__":
    main()