from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    trim,
    lower,
    upper,
    when,
    lit,
    concat_ws,
    count,
)

from pyspark.sql.window import Window
BASE_PATH = "data/generated"
SILVER_PATH = "data/silver"


def clean_entity(spark, entity, id_column):
    input_path = f"{BASE_PATH}/{entity}.parquet"
    output_path = f"{SILVER_PATH}/{entity}"

    df = spark.read.parquet(input_path)

    raw_count = df.count()

    # Trim all string columns
    for column in df.columns:
        if dict(df.dtypes)[column] == "string":
            df = df.withColumn(column, trim(col(column)))

    # Standardize email
    if "email" in df.columns:
        df = df.withColumn(
            "email",
            lower(col("email"))
        )

    # Standardize common categorical columns
    for column in ["territory", "category", "item_group"]:
        if column in df.columns:
            df = df.withColumn(
                column,
                upper(col(column))
            )

    # Data quality reason
    df = df.withColumn(
        "dq_reason",
        concat_ws(
            "; ",
            when(
                col(id_column).isNull(),
                lit(f"missing_{id_column}")
            ),
            when(
                trim(col(id_column)) == "",
                lit(f"blank_{id_column}")
            ),
        )
    )

    # duplicate
    duplicate_window = Window.partitionBy(id_column)

    df = df.withColumn(
        "dq_reason",
        concat_ws(
            "; ",
            col("dq_reason"),
            when(
                (col(id_column).isNotNull())
                & (count("*").over(duplicate_window) > 1),
                lit(f"duplicate_{id_column}")
            )
        )
    )

    df = df.withColumn(
        "dq_status",
        when(
            col("dq_reason") == "",
            lit("VALID")
        ).otherwise(
            lit("INVALID")
        )
    )

    valid = (
        df
        .filter(col("dq_status") == "VALID")
    )

    invalid = df.filter(
        col("dq_status") == "INVALID"
    )

    valid.write.mode("overwrite").parquet(
        output_path
    )

    invalid.write.mode("overwrite").parquet(
        f"data/quarantine/{entity}"
    )

    valid_count = valid.count()
    invalid_count = invalid.count()

    print(f"\n========== {entity.upper()} ==========")
    print(f"Raw:          {raw_count:,}")
    print(f"Valid:        {valid_count:,}")
    print(f"Quarantined:  {invalid_count:,}")
    print(
        f"Accounted:    "
        f"{valid_count + invalid_count:,} / {raw_count:,}"
    )


def main():

    spark = (
        SparkSession.builder
        .appName("TechMart-Silver-Reference")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    clean_entity(
        spark,
        "customers",
        "customer_id"
    )

    clean_entity(
        spark,
        "products",
        "product_id"
    )

    clean_entity(
        spark,
        "suppliers",
        "supplier_id"
    )

    spark.stop()


if __name__ == "__main__":
    main()
