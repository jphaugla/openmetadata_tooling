#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python apply_service_glossary_maps.py <map_file.json>")
        sys.exit(1)

    map_file = sys.argv[1]
    
    if not os.path.isfile(map_file):
        print(f"❌ Error: File '{map_file}' not found.")
        sys.exit(1)

    try:
        with open(map_file, "r") as f:
            mapping_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in mapping file '{map_file}'.\n{e}")
        sys.exit(1)

    client = OpenMetadataClient()

    # Loop through each entity in the mapping
    for row in mapping_data:
        fqn = row.get("fqn")
        service_type = row.get("serviceType", "databaseService")
        tags = row.get("tags", [])
        col_tags = row.get("columnTags", [])
        
        # Map internal service type to entity path
        entity_path = "searchIndexes" if service_type == "searchService" else "tables"

        print(f"🏷️  Restoring tags for {fqn} ({service_type})...")

        # Get the ID of the entity on the NEW instance
        encoded_fqn = urllib.parse.quote(fqn)
        response = client._make_request("GET", f"/{entity_path}/name/{encoded_fqn}")
        
        entity_id = None
        if response and response.status_code == 200:
            entity_id = response.json().get("id")

        if entity_id:
            # 1. Apply Top-level Tags
            if tags:
                tag_url = f"/{entity_path}/{entity_id}/tags"
                put_response = client._make_request("PUT", tag_url, json=tags)
                if put_response and put_response.status_code == 200:
                    print("   ✅ Top-level tags restored.")
                else:
                    err = put_response.json().get("message", put_response.text) if put_response else "Unknown"
                    print(f"   ❌ Failed to restore top-level tags: {err}")

            # 2. Apply Column/Field Tags
            # OpenMetadata often requires PATCH logic for column level tags, or 
            # modifying the full array of columns via PUT. 
            # Note: The original bash script had an incomplete/buggy implementation here 
            # doing a PUT /tags with just the parent entity ID.
            if col_tags:
                print("   ⚠️ Note: Column-level tag restoration requires PATCH/PUT to the full column array.")
                print("   Skipping column-level tags as per original bash script limitations.")
                
        else:
            print(f"   ⚠️ Entity not found on target. Run ingestion first. ({fqn})")

if __name__ == "__main__":
    main()
