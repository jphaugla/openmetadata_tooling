#!/usr/bin/env python3
import requests
import os
import sys

BASE_URL = os.environ.get("API_BASE")
if not BASE_URL:
    print("❌ API_BASE environment variable not set. Run: source ~/.collate/setJson.sh")
    sys.exit(1)
# The exact bucket you used before
S3_CONTAINER_FQN = "S3-Interchange.collate-snowflake-interchange-118146679784"
SNOWFLAKE_BASE_FQN = "Enterprise_SE.CUSTOMERS.COLLATE_SE"

def get_headers():
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN environment variable not set. Run: source ~/.collate/setJson.sh")
        sys.exit(1)
    return {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

def get_entity(entity_type, fqn, fields=None):
    headers = get_headers()
    # Using include=all because it successfully bypassed the 500 error in curl
    url = f"{BASE_URL}/{entity_type}/name/{fqn}?include=all"
    if fields: url += f"&fields={fields}"
    print(f"📡 Calling: {url}")
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    print(f"⚠️  Error (Status {res.status_code}): {fqn}")
    return None

def patch_container_columns(container_id, all_columns):
    headers = {**get_headers(), "Content-Type": "application/json-patch+json"}
    payload = [{
        "op": "add", "path": "/dataModel",
        "value": {
            "isPartitioned": False,
            "columns": [{"name": c, "dataType": "VARCHAR", "dataTypeDisplay": "VARCHAR"} for c in all_columns]
        }
    }]
    requests.patch(f"{BASE_URL}/containers/{container_id}", headers=headers, json=payload)

def main():
    mappings = {
        "RAW_CUSTOMERS": ["ID", "FIRST_NAME", "LAST_NAME"],
        "RAW_ORDERS": ["ID", "USER_ID", "ORDER_DATE", "STATUS"],
        "RAW_ORDER_ITEMS": ["ORDER_ITEM_ID", "ORDER_ID", "PRODUCT_ID", "QUANTITY", "UNIT_PRICE", "TOTAL_AMOUNT"],
        "RAW_PRODUCTS": ["PRODUCT_ID", "PRODUCT_NAME", "CATEGORY", "ECO_FRIENDLY", "UNIT_PRICE"]
    }
    
    # 1. Collect all unique columns for the bucket
    all_cols = set()
    for cols in mappings.values(): all_cols.update(cols)
    
    print(f"🔍 Fetching Bucket (ignoring dataModel to avoid 500 bug): {S3_CONTAINER_FQN}...")
    # Fetch WITHOUT fields. Asking for 'dataModel' triggers the server error.
    container = get_entity("containers", S3_CONTAINER_FQN)
    if not container:
        print("❌ Could not find bucket container.")
        return

    # 2. Patch all columns onto the bucket in one shot
    print(f"🛠️  Overwriting bucket dataModel with {len(all_cols)} clean columns...")
    patch_container_columns(container["id"], sorted(list(all_cols)))
    
    # 3. Fresh check. If it still 500s here, we'll skip the check and use the table logic.
    print("✨ Schema patched. Refreshing FQNs...")
    container_full = get_entity("containers", S3_CONTAINER_FQN, fields="dataModel")
    
    # If it still 500s, we can't get the S3 column FQNs, so we'll have to build them manually.
    if not container_full:
        print("⚠️  Warning: API still 500ing on dataModel. Constructing column FQNs manually...")
        # Most Collate FQNs are "BucketFQN.ColumnName"
        s3_col_fqns = {c: f"{S3_CONTAINER_FQN}.{c}" for c in all_cols}
    else:
        s3_col_fqns = {c["name"]: c["fullyQualifiedName"] for c in container_full["dataModel"]["columns"]}

    # 4. Create lineage for each table
    headers = get_headers()
    for table_name, columns in mappings.items():
        print(f"🔗 Linking {table_name}...")
        table = get_entity("tables", f"{SNOWFLAKE_BASE_FQN}.{table_name}")
        if not table:
            print(f"⚠️  Table {table_name} not found.")
            continue
            
        tbl_col_fqns = {c["name"]: c["fullyQualifiedName"] for c in table["columns"]}
        col_lineage = []
        for c in columns:
            if c in s3_col_fqns and c in tbl_col_fqns:
                col_lineage.append({"fromColumns": [s3_col_fqns[c]], "toColumn": tbl_col_fqns[c]})
        
        payload = {
            "edge": {
                "fromEntity": {"id": container["id"], "type": "container"},
                "toEntity": {"id": table["id"], "type": "table"},
                "lineageDetails": {"columnsLineage": col_lineage}
            }
        }
        res = requests.put(f"{BASE_URL}/lineage", headers=headers, json=payload)
        if res.status_code in [200, 201]: print(f"✅ Lineage for {table_name} success!")
        else: print(f"❌ Failed: {res.text}")

if __name__ == "__main__":
    main()
