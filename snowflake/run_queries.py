#!/usr/bin/env python3
import boto3
import os
import re
import snowflake.connector
from cryptography.hazmat.primitives import serialization

SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER")
if not SNOWFLAKE_ACCOUNT or not SNOWFLAKE_USER:
    raise RuntimeError("SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER environment variables must be set.")
PRIVATE_KEY_PATH = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
if not PRIVATE_KEY_PATH:
    raise RuntimeError("SNOWFLAKE_PRIVATE_KEY_PATH environment variable must be set.")
PRIVATE_KEY_PATH = os.path.expanduser(PRIVATE_KEY_PATH)
SQL_FILE = os.path.join(os.path.dirname(__file__), "import_and_transform.sql")

def get_private_key_bytes(path):
    with open(path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return p_key.private_bytes(serialization.Encoding.DER, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())

def get_aws_creds():
    """Fetch temporary AWS credentials from the current SSO session."""
    try:
        session = boto3.Session()
        creds = session.get_credentials().get_frozen_credentials()
        return {
            "key": creds.access_key,
            "secret": creds.secret_key,
            "token": creds.token
        }
    except Exception as e:
        print(f"⚠️  Could not fetch AWS credentials: {e}")
        return None

def main():
    if not os.path.exists(SQL_FILE):
        print(f"❌ SQL file not found: {SQL_FILE}")
        return

    aws = get_aws_creds()
    if not aws:
        print("❌ Failed to get AWS credentials. Did you run 'aws sso login'?")
        return

    SNOWFLAKE_S3_BUCKET = os.environ.get("SNOWFLAKE_S3_BUCKET")
    if not SNOWFLAKE_S3_BUCKET:
        print("❌ SNOWFLAKE_S3_BUCKET environment variable must be set.")
        return

    print(f"📖 Reading SQL from: {SQL_FILE}")
    with open(SQL_FILE, "r") as f:
        sql_content = f.read()
        
    sql_content = sql_content.replace("{SNOWFLAKE_S3_BUCKET}", SNOWFLAKE_S3_BUCKET)

    # Split statements
    statements = [s.strip() for s in re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)', sql_content) if s.strip()]

    print(f"🚀 Connecting to Snowflake as {SNOWFLAKE_USER}...")
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER, account=SNOWFLAKE_ACCOUNT,
        private_key=get_private_key_bytes(PRIVATE_KEY_PATH),
        warehouse="DEMO_WH", database="CUSTOMERS", schema="COLLATE_SE",
        role="SALES_ENGINEERS"
    )

    try:
        cur = conn.cursor()
        for i, stmt in enumerate(statements, 1):
            # If it's a COPY INTO from S3, inject the credentials
            if "COPY INTO" in stmt.upper() and "S3://" in stmt.upper():
                # Remove trailing semicolon if any, inject creds, re-add semicolon (if needed, but execute() doesn't need it)
                cred_str = f"\nCREDENTIALS = (AWS_KEY_ID='{aws['key']}' AWS_SECRET_KEY='{aws['secret']}' AWS_TOKEN='{aws['token']}')"
                # Insert before FILE_FORMAT or at the end
                if "FILE_FORMAT" in stmt.upper():
                    stmt = stmt.replace("FILE_FORMAT", f"{cred_str}\nFILE_FORMAT")
                else:
                    stmt = f"{stmt}\n{cred_str}"

            print(f"⚙️  [{i}/{len(statements)}] {stmt[:60]}...")
            cur.execute(stmt)
            
        print("\n🎉 Data load and transformation complete!")
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
