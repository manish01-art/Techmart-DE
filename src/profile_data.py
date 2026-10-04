from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/generated")


def profile_file(file_path):
    df = pd.read_parquet(file_path)

    print(f"\n{'=' * 70}")
    print(f"FILE: {file_path.name}")
    print(f"{'=' * 70}")

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nSchema:")
    print(df.dtypes.to_string())

    print("\nNull values:")
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]

    if len(nulls) > 0:
        print(nulls.to_string())
    else:
        print("No null values")

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nUnique values:")
    for column in df.columns:
        print(f"  {column}: {df[column].nunique(dropna=True):,}")


def main():
    files = sorted(DATA_DIR.glob("*.parquet"))

    if not files:
        raise FileNotFoundError(
            f"No parquet files found in {DATA_DIR}"
        )

    for file_path in files:
        profile_file(file_path)


if __name__ == "__main__":
    main()