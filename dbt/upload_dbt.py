#!/usr/bin/env python3
# upload_dbt.py
import boto3
import os

BUCKET = "collate-snowflake-interchange-118146679784"
FILES = ["manifest.json", "run_results.json", "catalog.json"]
DIR = "target"
PREFIX = "dbt_tgts"

print("Uploading to S3...")
session = boto3.Session()
s3 = session.client('s3')

for file in FILES:
    local_path = os.path.join(DIR, file)
    s3_key = f"{PREFIX}/{file}"
    print(f"Uploading {local_path} to s3://{BUCKET}/{s3_key}")
    s3.upload_file(local_path, BUCKET, s3_key)

print("Done!")
