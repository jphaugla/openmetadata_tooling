#!/usr/bin/env python3
import sys
import json
import os
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python import_search_service.py <service_json_file_path>")
        print("Example: python import_search_service.py $JSON_DIR/ElasticsearchProd.json")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not os.path.isfile(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r") as f:
        try:
            service_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in file '{input_file}'.\n{e}")
            sys.exit(1)

    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    # Validate that we got a valid JSON with required fields
    import_name = service_data.get("name")
    import_type = service_data.get("serviceType")
    
    if not import_name or not import_type:
        print(f"❌ Error: Could not extract 'name' or 'serviceType' from {input_file}.")
        sys.exit(1)

    print(f"🚀 Importing Search Service from: {input_file}")
    print(f"👤 Assigning Owner ID: {owner_id}")

    # Build Create Payload
    create_payload = {
        "name": import_name,
        "serviceType": import_type,
        "connection": service_data.get("connection"),
        "owners": [{"id": owner_id, "type": "user"}]
    }

    if "description" in service_data:
        create_payload["description"] = service_data["description"]
        
    print(f"📡 Sending POST request for {import_name}...")

    # 3. Create Service
    response = client._make_request("POST", "/services/searchServices", json=create_payload)

    if response is not None and response.status_code in [200, 201]:
        data = response.json()
        print("✅ Search Service successfully imported!")
        print(f"🆔 New Service ID: {data.get('id')}")
        print(f"🔗 Service Name: {data.get('name')}")
    else:
        print("❌ Failed to import Search Service.")
        status = response.status_code if response is not None else "Unknown"
        text = response.text if response is not None else "No response"
        print(f"💬 Server Status: {status}")
        print(f"💬 Server Response: {text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
