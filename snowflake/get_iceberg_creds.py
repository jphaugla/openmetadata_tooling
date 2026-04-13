#!/usr/bin/env python3
import snowflake.connector
import os
from cryptography.hazmat.primitives import serialization

SNOWFLAKE_ACCOUNT = "FMFAHQK-GI58232"
SNOWFLAKE_USER = "JASON"
PRIVATE_KEY_PATH = os.path.expanduser("~/.snowflake/snowflake_key_unencrypted.p8")

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
