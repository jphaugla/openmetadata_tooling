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

    # Source: Snowflake View (Case sensitive FQN)
    source_fqn = "Enterprise_SE.CUSTOMERS.COLLATE_SE.CUSTOMER360"
    
    # Target: PowerBI Model (Includes .model. prefix in FQN)
    target_fqn = "PowerBIPROD_v2.model.cce81653-2f69-4161-845b-237fc7cf1b7e"

    print(f"🔗 Establishing Lineage:")
    print(f"   From: {source_fqn}")
    print(f"   To:   {target_fqn}")

    from_id = get_id(client, "table", source_fqn)
    to_id = get_id(client, "dashboardDataModel", target_fqn)

    if not from_id or not to_id:
        print(f"❌ Error: Could not resolve IDs.")
        if not from_id: print(f"   - Missing Source: {source_fqn}")
        if not to_id: print(f"   - Missing Target: {target_fqn}")
        sys.exit(1)

    payload = {
        "edge": {
            "fromEntity": {"id": from_id, "type": "table"},
            "toEntity": {"id": to_id, "type": "dashboardDataModel"}
        }
    }

    res = client._make_request("PUT", "/lineage", json=payload)
    if res and res.status_code in [200, 201]:
        print("✅ Success! Lineage edge created.")
    else:
        print(f"❌ Failed: {res.status_code if res else 'No response'}")
        if res: print(res.text)

if __name__ == "__main__":
    main()
