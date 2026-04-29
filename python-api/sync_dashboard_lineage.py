#!/usr/bin/env python3
import os
import sys
import subprocess
import urllib.parse
from om_client import OpenMetadataClient

def load_env_from_sh(file_path):
    path = os.path.expanduser(file_path)
    if not os.path.exists(path): return
    try:
        command = f"source {path} > /dev/null 2>&1 && env"
        output = subprocess.check_output(["bash", "-c", command], text=True)
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
    except: pass

def get_id(client, entity_type, fqn):
    endpoint = f"/{entity_type}s"
    if entity_type == "dashboardDataModel": endpoint = "/dashboard/datamodels"
    encoded_fqn = urllib.parse.quote(fqn)
    res = client._make_request("GET", f"{endpoint}/name/{encoded_fqn}")
    if res and res.status_code == 200:
        return res.json().get("id")
    return None

def main():
    load_env_from_sh("~/.collate/setJson.sh")
    client = OpenMetadataClient()

    service_name = "PowerBIPROD_v2"
    
    # 1. Target Model ID
    model_fqn = f"{service_name}.model.cce81653-2f69-4161-845b-237fc7cf1b7e"
    model_id = get_id(client, "dashboardDataModel", model_fqn)
    
    if not model_id:
        print(f"❌ Error: Could not find Data Model {model_fqn}")
        sys.exit(1)

    # 2. Find all Dashboards for the service
    print(f"🔍 Finding dashboards for {service_name}...")
    res = client._make_request("GET", f"/dashboards?service={service_name}&limit=100")
    if not res or res.status_code != 200:
        print("❌ Error fetching dashboards")
        sys.exit(1)
        
    dashboards = res.json().get("data", [])
    print(f"🚀 Creating lineage from {model_fqn} to {len(dashboards)} dashboards...")

    success_count = 0
    for dash in dashboards:
        dash_id = dash.get("id")
        dash_name = dash.get("displayName") or dash.get("name")
        
        payload = {
            "edge": {
                "fromEntity": {"id": model_id, "type": "dashboardDataModel"},
                "toEntity": {"id": dash_id, "type": "dashboard"}
            }
        }
        
        l_res = client._make_request("PUT", "/lineage", json=payload)
        if l_res and l_res.status_code in [200, 201]:
            print(f"   ✅ Linked: {dash_name}")
            success_count += 1
        else:
            print(f"   ❌ Failed: {dash_name}")

    print(f"\n✨ Finished! Created {success_count} lineage links.")

if __name__ == "__main__":
    main()
