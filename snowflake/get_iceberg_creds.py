#!/usr/bin/env python3
import snowflake.connector
import os
from cryptography.hazmat.primitives import serialization

SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
if not SNOWFLAKE_ACCOUNT or not SNOWFLAKE_USER:
    raise RuntimeError("SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER environment variables must be set.")
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

def main():
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        account=SNOWFLAKE_ACCOUNT,
        private_key=get_private_key_bytes(PRIVATE_KEY_PATH),
        warehouse="DEMO_WH",
        role="SALES_ENGINEERS"
    )

    try:
        cur = conn.cursor()
        cur.execute("DESCRIBE EXTERNAL VOLUME iceberg_external_volume")
        rows = cur.fetchall()
        for row in rows:
            print(row)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
