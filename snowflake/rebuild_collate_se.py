#!/usr/bin/env python3
"""
rebuild_collate_se.py

Full teardown and rebuild of COLLATE_SE schema as JASON (SYSADMIN role).
Run this ONCE before running export_to_s3.py + run_queries.py.

Steps:
  1. Drop and recreate COLLATE_SE schema
  2. Create all tables (RAW + production) with correct DDL
  3. Create all views pointing to COLLATE_SE (not COLLATE_SHOP)
  4. Grant USAGE/SELECT to SALES_ENGINEERS role

After this script, the expected run order is:
  1. python3 rebuild_collate_se.py     (this script - one time setup)
  2. python3 export_to_s3.py           (export COLLATE_SHOP tables to S3)
  3. python3 run_queries.py            (load S3 -> RAW -> PROD + compute derived columns)
"""
import snowflake.connector
import os
import re
from cryptography.hazmat.primitives import serialization

SNOWFLAKE_ACCOUNT = "FMFAHQK-GI58232"
SNOWFLAKE_USER = "JASON"
PRIVATE_KEY_PATH = os.path.expanduser("~/.snowflake/snowflake_key_unencrypted.p8")
SQL_FILE = os.path.join(os.path.dirname(__file__), "rebuild_collate_se.sql")

def get_private_key_bytes(path):
    with open(path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

def split_sql(sql_content):
    """Split on semicolons, skipping blank/comment-only blocks."""
    raw = re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)', sql_content)
    statements = []
    for s in raw:
        stripped = s.strip()
        non_comment = "\n".join(
            line for line in stripped.splitlines()
            if not line.strip().startswith("--")
        ).strip()
        if non_comment:
            statements.append(stripped)
    return statements

def main():
    if not os.path.exists(SQL_FILE):
        print(f"❌ SQL file not found: {SQL_FILE}")
        return

    print(f"📖 Reading: {SQL_FILE}")
    with open(SQL_FILE, "r") as f:
        sql_content = f.read()

    statements = split_sql(sql_content)
    print(f"   Found {len(statements)} statements.\n")

    print(f"⚡ Connecting as {SNOWFLAKE_USER}...")
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        account=SNOWFLAKE_ACCOUNT,
        private_key=get_private_key_bytes(PRIVATE_KEY_PATH),
        warehouse="DEMO_WH",
        database="CUSTOMERS",
    )

    try:
        cur = conn.cursor()
        for i, stmt in enumerate(statements, 1):
            preview = stmt.replace("\n", " ")[:120]
            print(f"⚙️  [{i}/{len(statements)}] {preview}...")
            try:
                cur.execute(stmt)
                result = cur.fetchone()
                if result:
                    print(f"   ✅ {result[0]}")
                else:
                    print(f"   ✅ OK")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                raise

        print("\n🎉 COLLATE_SE rebuilt successfully!")
        print("\nNext steps:")
        print("  python3 export_to_s3.py    # export source tables from COLLATE_SHOP to S3")
        print("  python3 run_queries.py     # load data + compute derived columns")

    except Exception as e:
        print(f"\n❌ Aborted at statement {i}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
