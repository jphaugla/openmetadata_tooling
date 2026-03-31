#!/usr/bin/env python3
import json
import os
import sys
import urllib.parse
from om_client import OpenMetadataClient

# Cache for FQN to ID lookups
id_cache = {}

def get_entity_id(client, entity_type, fqn):
    """Resolves an FQN and type to a current UUID."""
    cache_key = f"{entity_type}|{fqn}"
    if cache_key in id_cache:
        return id_cache[cache_key]
    
    # Mapping of common entity types to their plural API endpoints
    type_to_endpoint = {
        "table": "/tables",
        "dashboard": "/dashboards",
        "pipeline": "/pipelines",
        "topic": "/topics",
        "mlmodel": "/mlmodels",
        "searchIndex": "/searchIndexes",
        "container": "/containers",
        "databaseService": "/services/databaseServices",
        "searchService": "/services/searchServices"
    }
    
    endpoint = type_to_endpoint.get(entity_type, f"/{entity_type}s")
    encoded_fqn = urllib.parse.quote(fqn)
    
    resp = client._make_request("GET", f"{endpoint}/name/{encoded_fqn}")
    if resp and resp.status_code == 200:
        entity_id = resp.json().get("id")
        id_cache[cache_key] = entity_id
        return entity_id
        
    return None

def main():
    if len(sys.argv) < 2:
        print("❌ Error: No service name or file path provided.")
        print("Usage: python import_lineage.py <service_name_or_json_file>")
        sys.exit(1)

    input_arg = sys.argv[1]
    client = OpenMetadataClient()
    
    # Determine the file path
    if input_arg.endswith(".json"):
        file_path = input_arg
    else:
        json_dir = os.path.join(os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json")), "lineage")
        file_path = os.path.join(json_dir, f"{input_arg}_lineage.json")

    if not os.path.isfile(file_path):
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)

    print(f"📂 Reading lineage data from {file_path}...")
    with open(file_path, "r") as f:
        lineage_data = json.load(f)

    print(f"🚀 Processing {len(lineage_data)} lineage edges...")
    
    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, edge in enumerate(lineage_data):
        from_info = edge.get("fromEntity")
        to_info = edge.get("toEntity")
        
        if not from_info or not to_info:
            print(f"  ⚠️ Skipping edge {i}: Missing entity info.")
            skip_count += 1
            continue
            
        from_fqn = from_info.get("fqn")
        from_type = from_info.get("type")
        to_fqn = to_info.get("fqn")
        to_type = to_info.get("type")
        
        # Resolve IDs
        from_id = get_entity_id(client, from_type, from_fqn)
        to_id = get_entity_id(client, to_type, to_fqn)
        
        if not from_id or not to_id:
            missing = []
            if not from_id: missing.append(f"from:{from_fqn}")
            if not to_id: missing.append(f"to:{to_fqn}")
            print(f"  ❌ Skipping edge: Could not resolve IDs for {', '.join(missing)}")
            fail_count += 1
            continue
            
        # Create lineage edge
        payload = {
            "edge": {
                "fromEntity": {"id": from_id, "type": from_type},
                "toEntity": {"id": to_id, "type": to_type}
            }
        }
        
        # Include lineage details if they exist (e.g. column lineage)
        if edge.get("lineageDetails"):
            payload["edge"]["lineageDetails"] = edge["lineageDetails"]
            
        res = client._make_request("PUT", "/lineage", json=payload)
        
        if res and res.status_code in [200, 201]:
            success_count += 1
            if (i+1) % 10 == 0:
                print(f"   Processed {i+1}/{len(lineage_data)}... ({success_count} success)")
        else:
            err = res.json().get("message", res.text) if res else "Unknown HTTP Error"
            print(f"  ❌ Failed to create edge {from_fqn} -> {to_fqn}: {err}")
            fail_count += 1

    print(f"\n✨ Import Complete!")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed:     {fail_count}")
    print(f"   ℹ️  Skipped:    {skip_count}")

if __name__ == "__main__":
    main()
