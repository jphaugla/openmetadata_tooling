import snowflake.connector
import os
from cryptography.hazmat.primitives import serialization

# Snowflake details found in the 'Enterprise' service config
SNOWFLAKE_ACCOUNT = "FMFAHQK-GI58232"
SNOWFLAKE_USER = "JASON"
SNOWFLAKE_WAREHOUSE = "DEMO_WH"
SNOWFLAKE_DATABASE = "CUSTOMERS"
SNOWFLAKE_SCHEMA = "COLLATE_SHOP"

# File path to the unencrypted private key
PRIVATE_KEY_PATH = os.path.expanduser("~/.snowflake/snowflake_key_unencrypted.p8")

def get_private_key_bytes(path):
    with open(path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None, # Already unencrypted
        )
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

def main():
    print(f"Connecting to Snowflake account: {SNOWFLAKE_ACCOUNT}")
    
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        account=SNOWFLAKE_ACCOUNT,
        private_key=get_private_key_bytes(PRIVATE_KEY_PATH),
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )

    try:
        cur = conn.cursor()
        print("Successfully connected! Running test query...")
        
        cur.execute("SELECT CURRENT_VERSION(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        row = cur.fetchone()
        
        print("\nSnowflake Session Details:")
        print(f"--------------------------")
        print(f"Version:   {row[0]}")
        print(f"Role:      {row[1]}")
        print(f"Warehouse: {row[2]}")
        print(f"Database:  {row[3]}")
        print(f"Schema:    {row[4]}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
