#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python import_metric.py <metric_json_file_path>")
        print("Example: python import_metric.py ~/.collate/json/metric/CLV.json")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not os.path.isfile(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r") as f:
        try:
            metric_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in file '{input_file}'.\n{e}")
            sys.exit(1)

    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")

    # Build Create Payload
    name = metric_data.get("name")
    print(f"🔗 Prepping Import for Metric: {name}")

    create_payload = {
        "name": name,
        "displayName": metric_data.get("displayName"),
        "description": metric_data.get("description"),
        "metricExpression": metric_data.get("metricExpression"),
        "metricType": metric_data.get("metricType"),
        "unitOfMeasurement": metric_data.get("unitOfMeasurement"),
        "granularity": metric_data.get("granularity")
    }

    # Handle Owners - Override with OWNER_ID if set, otherwise try to reuse existing IDs
    if owner_id:
        create_payload["owners"] = [{"id": owner_id, "type": "user"}]
    elif metric_data.get("owners"):
        create_payload["owners"] = [{"id": o["id"], "type": o["type"]} for o in metric_data["owners"]]

    # Handle Tags - Reconstruct the tag references if they exist
    if metric_data.get("tags"):
        create_payload["tags"] = []
        for t in metric_data["tags"]:
             # When creating, OpenMetadata typically expects tagFQN and basic metadata
             create_payload["tags"].append({
                 "tagFQN": t.get("tagFQN"),
                 "source": t.get("source", "Classification"),
                 "labelType": t.get("labelType", "Manual"),
                 "state": t.get("state", "Confirmed")
             })

    print("----------------------------------------------------------------")
    print(f"🚀 Importing Metric: {name}")

    # Create Metric via POST
    response = client._make_request("POST", "/metrics", json=create_payload)
    
    if response is not None and response.status_code in [200, 201]:
        print(f"   ✅ Created (ID: {response.json().get('id')})")
    elif response is not None and response.status_code == 404 and "tag" in response.text.lower():
        print(f"   ⚠️ Tag not found on target instance. Retrying import WITHOUT tags...")
        # Remove tags and retry
        create_payload.pop("tags", None)
        retry_response = client._make_request("POST", "/metrics", json=create_payload)
        if retry_response and retry_response.status_code in [200, 201, 409]:
            if retry_response.status_code == 409:
                 print(f"   ⚠️ Metric already exists (ignoring tag failure).")
            else:
                 print(f"   ✅ Created without tags (ID: {retry_response.json().get('id')})")
        else:
            print(f"   ❌ Retry failed: {retry_response.text if retry_response else 'No response'}")
    elif response is not None and response.status_code == 409:
        print(f"   ⚠️ Metric '{name}' already exists. Attempting update via PUT...")
        # OpenMetadata typically supports PUT at /metrics to update existing entities
        put_response = client._make_request("PUT", "/metrics", json=create_payload)
        if put_response and put_response.status_code == 200:
             print(f"   ✅ Updated existing metric '{name}'")
        else:
             err = put_response.text if put_response else "No response"
             print(f"   ❌ Update failed: {err}")
    else:
        status = response.status_code if response is not None else "Unknown"
        text = response.text if response is not None else "No error message"
        print(f"   ❌ Failed to create metric. Status: {status}")
        print(f"      Response: {text}")

if __name__ == "__main__":
    main()
