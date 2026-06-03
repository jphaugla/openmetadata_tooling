#!/usr/bin/env python3
"""
export_to_s3.py
Exports tables from COLLATE_SHOP to S3 so they can be loaded into COLLATE_SE via run_queries.py.
Tables exported: RAW_CUSTOMERS, RAW_ORDERS, ORDER_ITEMS (as RAW_ORDER_ITEMS), PRODUCTS (as RAW_PRODUCTS)
"""
import snowflake.connector
import os
import csv
import boto3
from cryptography.hazmat.primitives import serialization

# Snowflake connection details
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
if not SNOWFLAKE_ACCOUNT or not SNOWFLAKE_USER:
    raise RuntimeError("SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER environment variables must be set.")
SNOWFLAKE_WAREHOUSE = "DEMO_WH"
SNOWFLAKE_DATABASE = "CUSTOMERS"
SNOWFLAKE_SCHEMA = "COLLATE_SHOP"

# S3 details
SNOWFLAKE_S3_BUCKET = os.environ.get("SNOWFLAKE_S3_BUCKET")
if not SNOWFLAKE_S3_BUCKET:
    raise RuntimeError("SNOWFLAKE_S3_BUCKET environment variable must be set.")

# Tables to export: (source_table, s3_key, local_tmp)
EXPORTS = [
    ("RAW_CUSTOMERS",  "customers/raw_customers_export.csv",     "/tmp/raw_customers_export.csv"),
    ("RAW_ORDERS",     "orders/raw_orders_export.csv",           "/tmp/raw_orders_export.csv"),
    ("ORDER_ITEMS",    "order_items/raw_order_items_export.csv", "/tmp/raw_order_items_export.csv"),
    ("PRODUCTS",       "products/raw_products_export.csv",       "/tmp/raw_products_export.csv"),
]

# File path to the unencrypted private key
PRIVATE_KEY_PATH = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
if not PRIVATE_KEY_PATH:
    raise RuntimeError("SNOWFLAKE_PRIVATE_KEY_PATH environment variable must be set.")
PRIVATE_KEY_PATH = os.path.expanduser(PRIVATE_KEY_PATH)

def get_private_key_bytes(path):
    with open(path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

def export_table(cur, s3, table_name, s3_key, local_path):
    print(f"\n📡 Querying {SNOWFLAKE_SCHEMA}.{table_name}...")
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    print(f"   📊 Fetched {len(rows)} rows. Saving to {local_path}...")

    with open(local_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(colnames)
        writer.writerows(rows)

    print(f"   ☁️  Uploading to s3://{SNOWFLAKE_S3_BUCKET}/{s3_key}...")
    s3.upload_file(local_path, SNOWFLAKE_S3_BUCKET, s3_key)
    print(f"   ✅ Done: s3://{SNOWFLAKE_S3_BUCKET}/{s3_key}")

    if os.path.exists(local_path):
        os.remove(local_path)

def main():
    print(f"🚀 Connecting to Snowflake as {SNOWFLAKE_USER} / schema {SNOWFLAKE_SCHEMA}...")
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        account=SNOWFLAKE_ACCOUNT,
        private_key=get_private_key_bytes(PRIVATE_KEY_PATH),
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )
    s3 = boto3.client("s3")

    try:
        cur = conn.cursor()
        for (table_name, s3_key, local_path) in EXPORTS:
            try:
                export_table(cur, s3, table_name, s3_key, local_path)
            except Exception as e:
                print(f"   ❌ Error exporting {table_name}: {e}")

        print("\n🎉 All exports complete!")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
