#!/usr/bin/env python3
import os
import subprocess
import sys

# Mappings for the demo: (Table Name, Columns, CSV File Name)
MAPPINGS = [
    ("RAW_CUSTOMERS",   "ID,FIRST_NAME,LAST_NAME",                 "raw_customers_export.csv"),
    ("RAW_ORDERS",      "ID,USER_ID,ORDER_DATE,STATUS",            "raw_orders_export.csv"),
    ("RAW_ORDER_ITEMS", "ORDER_ITEM_ID,ORDER_ID,PRODUCT_ID,QUANTITY,UNIT_PRICE,TOTAL_AMOUNT", "raw_order_items_export.csv"),
    ("RAW_PRODUCTS",    "PRODUCT_ID,PRODUCT_NAME,CATEGORY,ECO_FRIENDLY,UNIT_PRICE", "raw_products_export.csv")
]

BASE_FQN = "Enterprise_SE.CUSTOMERS.COLLATE_SE"

def main():
    print("🎨 Transforming S3 Files into Iceberg Containers & Drawing Lineage...")
    
    # Ensure we are in the root directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, "../../"))
    os.chdir(root_dir)

    for table_name, cols, file_name in MAPPINGS:
        table_fqn = f"{BASE_FQN}.{table_name}"
        print(f"\n📦 Processing {file_name} -> {table_name}...")
        
        # Call the base script with arguments
        # Note: We use the absolute path to ensure it 
        cmd = [
            sys.executable, "python-api/examples/add_s3_column_lineage.py",
            table_fqn, cols, file_name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"❌ Error (Code {result.returncode}):")
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())

    print("\n✅ All S3 sources are now linked and formatted as Iceberg tables!")

if __name__ == "__main__":
    main()
