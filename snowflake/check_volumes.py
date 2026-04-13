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
    print(f"⚡ Connecting to Snowflake as {SNOWFLAKE_USER} to check volumes...")
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        account=SNOWFLAKE_ACCOUNT,
        private_key=get_private_key_bytes(PRIVATE_KEY_PATH),
        warehouse="DEMO_WH",
        database="CUSTOMERS",
    )

    try:
        cur = conn.cursor()
        print("🔍 Checking for accessible EXTERNAL VOLUMES...")
        cur.execute("SHOW EXTERNAL VOLUMES")
        rows = cur.fetchall()
        
        if not rows:
            print("❌ No EXTERNAL VOLUMES found or accessible.")
        else:
            print(f"✅ Found {len(rows)} volume(s):")
            for row in rows:
                print(f"   - Name: {row[1]}, Status: {row[4]}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
