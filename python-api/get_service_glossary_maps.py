#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python get_service_glossary_maps.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    client = OpenMetadataClient()
    
    print(f"🔍 Identifying Service Type for: {service_name}...")
    
    # 1. Identify Service Type
    service_id, service_type = client.get_service_id(service_name)
    
    if not service_id:
        print(f"❌ Error: Service '{service_name}' not found as a Database or Search service.")
        sys.exit(1)
        
    endpoint = ""
    filter_key = "service"
    fields = ""
    
    if service_type == "databaseService":
        endpoint = "tables"
        fields = "tags,columns"
        print(f"✅ Found Database Service: {service_name}")
    elif service_type == "searchService":
        endpoint = "searchIndexes"
        fields = "tags,fields"
        print(f"✅ Found Search Service: {service_name}")
        
    print(f"📡 Exporting Glossary Mappings for {service_name} ({service_type})...")
    
    # 2. Fetch Entities
    encoded_svc = urllib.parse.quote(service_name)
    url = f"/{endpoint}?{filter_key}={encoded_svc}&fields={fields}&limit=1000"
    
    response = client._make_request("GET", url)
    
    if not response or response.status_code != 200:
        err = response.json().get("message", response.text) if response else "Unknown Error"
        print(f"❌ API Error: {err}")
        sys.exit(1)
        
    data = response.json().get("data", [])
    
    # 3. Process and Filter JSON
    processed_maps = []
    
    for entity in data:
        fqn = entity.get("fullyQualifiedName", "")
        
        # Ensure it actually belongs to this service (API sometimes bleeds through on wildcard matches)
        if not fqn.startswith(service_name):
            continue
            
        entity_tags = [
            {"tagFQN": t.get("tagFQN"), "source": t.get("source")} 
            for t in entity.get("tags", [])
        ]
        
        column_tags = []
        children = entity.get("columns", []) if service_type == "databaseService" else entity.get("fields", [])
        
        for child in children:
            ctags = [
                {"tagFQN": t.get("tagFQN"), "source": t.get("source")} 
                for t in child.get("tags", [])
            ]
            if ctags:
                column_tags.append({
                    "name": child.get("name"),
                    "tags": ctags
                })
                
        # Only keep entities that actually have tags at the top level or child level
        if entity_tags or column_tags:
            processed_maps.append({
                "fqn": fqn,
                "serviceType": service_type,
                "tags": entity_tags,
                "columnTags": column_tags
            })
            
    # 4. Save
    json_dir = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    os.makedirs(json_dir, exist_ok=True)
    
    file_name = f"{service_name.replace(' ', '_')}_glossary_map.json"
    file_path = os.path.join(json_dir, file_name)
    
    with open(file_path, "w") as f:
        json.dump(processed_maps, f, indent=2)
        
    print(f"✅ Saved mapping to {file_name}")
    print(f"📊 Found {len(processed_maps)} entities with tags.")

if __name__ == "__main__":
    main()
