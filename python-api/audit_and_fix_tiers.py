#!/usr/bin/env python3
import requests
import os
import sys
import json

BASE_URL = os.environ.get("API_BASE")
if not BASE_URL:
    print("❌ API_BASE environment variable not set. Run: source ~/.collate/setJson.sh")
    sys.exit(1)

SCHEMA_FQN = "Enterprise_SE.CUSTOMERS.COLLATE_SE"

def get_headers():
    jwt = os.environ.get("TOKEN")
    if not jwt:
        print("❌ TOKEN environment variable not set.")
        sys.exit(1)
    return {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

def list_all_tables_in_schema(schema_fqn):
    """Fetch all tables in the specific schema."""
    print(f"📡 Fetching all tables in {schema_fqn}...")
    # Search is more efficient for this
    query = f"databaseSchema.fullyQualifiedName:\"{schema_fqn}\""
    url = f"{BASE_URL}/search/query?q={query}&index=table_search_index&size=100"
    res = requests.get(url, headers=get_headers())
    if res.status_code != 200:
        print(f"❌ Failed to search tables: {res.text}")
        return []
    
    hits = res.json().get("hits", {}).get("hits", [])
    return [hit["_source"] for hit in hits]

def patch_tier_if_needed(table):
    """Apply a Tier tag based on naming convention."""
    fqn = table["fullyQualifiedName"]
    name = table["name"].upper()
    
    # Determine Tier
    target_tier = None
    if name.startswith("STG_") or name.startswith("RAW_"):
        target_tier = "Tier3"
    elif "CUSTOMER" in name or "ORDER" in name or "PRODUCT" in name:
        target_tier = "Tier1"
    
    if not target_tier:
        return

    # Check current tags
    existing_tags = table.get("tags", [])
    for tag in existing_tags:
        if tag['tagFQN'].startswith("Tier.Tier"):
            if tag['tagFQN'] == f"Tier.{target_tier}":
                print(f"  - {name}: Already has {tag['tagFQN']}. OK.")
                return
            else:
                # Different tier exists? We'll overwrite it for consistency in the demo
                pass

    print(f"  🚀 {name}: Applying {target_tier}...")
    
    headers = {**get_headers(), "Content-Type": "application/json-patch+json"}
    
    # We use a REPLACE or ADD approach
    # To be safe, we'll strip existing Tiers first in the patch
    new_tags = [t for t in existing_tags if not t['tagFQN'].startswith("Tier.Tier")]
    new_tags.append({
        "tagFQN": f"Tier.{target_tier}",
        "labelType": "Automated",
        "state": "Confirmed",
        "source": "Classification"
    })
    
    payload = [{
        "op": "replace",
        "path": "/tags",
        "value": new_tags
    }]
    
    res = requests.patch(f"{BASE_URL}/tables/{table['id']}", headers=headers, json=payload)
    if res.status_code in [200, 201]:
        print(f"    ✅ Done.")
    else:
        print(f"    ❌ Failed: {res.text}")

def main():
    tables = list_all_tables_in_schema(SCHEMA_FQN)
    if not tables:
        print("❌ No tables found to process.")
        return

    print(f"📋 Found {len(tables)} tables. Processing Tiers...\n")
    
    for tbl in tables:
        patch_tier_if_needed(tbl)

    print("\n✨ All tables processed. Your demo environment is ready!")

if __name__ == "__main__":
    main()
