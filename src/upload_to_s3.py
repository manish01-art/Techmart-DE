import os
from pathlib import Path

import boto3
from dotenv import load_dotenv


load_dotenv()

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

SOURCE_DIR = Path("data/source_batches")


def upload_directory(s3_client, local_dir):
    files = [
        file
        for file in local_dir.rglob("*")
        if file.is_file()
    ]

    for file in files:
        relative_path = file.relative_to(SOURCE_DIR)

        s3_key = (
            f"bronze/source_batches/"
            f"{relative_path.as_posix()}"
        )

        print(f"Uploading: {file}")

        s3_client.upload_file(
            str(file),
            BUCKET_NAME,
            s3_key,
        )

        print(f"Uploaded → s3://{BUCKET_NAME}/{s3_key}")


def main():
    if not BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME is missing")

    if not AWS_REGION:
        raise ValueError("AWS_REGION is missing")

    if not SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Source directory not found: {SOURCE_DIR}"
        )

    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
    )

    upload_directory(
        s3_client,
        SOURCE_DIR,
    )

    print("\nBronze upload completed.")


if __name__ == "__main__":
    main()