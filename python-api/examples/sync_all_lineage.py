#!/usr/bin/env python3
import subprocess
import os
import sys

# Configuration for the 4 tables
TABLES = [
    {
        "fqn": "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS",
        "cols": "ID,FIRST_NAME,LAST_NAME",
        "file": "raw_customers_export.csv"
    },
    {
        "fqn": "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_ORDERS",
        "cols": "ID,USER_ID,ORDER_DATE,STATUS",
        "file": "raw_orders_export.csv"
    },
    {
        "fqn": "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_ORDER_ITEMS",
        "cols": "ORDER_ITEM_ID,ORDER_ID,PRODUCT_ID,QUANTITY,UNIT_PRICE,TOTAL_AMOUNT",
        "file": "raw_order_items_export.csv"
    },
    {
        "fqn": "Enterprise_SE.CUSTOMERS.COLLATE_SE.RAW_PRODUCTS",
        "cols": "PRODUCT_ID,PRODUCT_NAME,CATEGORY,ECO_FRIENDLY,UNIT_PRICE",
        "file": "raw_products_export.csv"
    }
]

def main():
    script_path = os.path.join(os.path.dirname(__file__), "add_s3_column_lineage.py")
    
    print(f"🚀 Starting bulk S3 lineage sync for {len(TABLES)} tables...")
    
    for table in TABLES:
        print(f"\n--- Syncing {table['fqn']} (from {table['file']}) ---")
        cmd = [sys.executable, script_path, table["fqn"], table["cols"], table["file"]]
        
        try:
            result = subprocess.run(cmd, check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error syncing {table['fqn']}: {e}")

    print("\n✨ Bulk sync complete!")

if __name__ == "__main__":
    main()
