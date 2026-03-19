#!/usr/bin/env python3
import json
import os
import sys
from om_client import OpenMetadataClient

def get_all_ids_from_search(client, index_name, service_name=None):
    """Use search just to get IDs — lightweight, doesn't hydrate entities."""
    ids = []
    offset = 0
    size = 500
    
    # If service filter is provided, we filter by FQN prefix
    # Note: Search queries with dots/spaces might need quoting
    query = "*"
    if service_name:
        if service_name.lower() == "logical":
             query = "testSuiteType:Logical"
        else:
             query = f"fullyQualifiedName:\"{service_name}\".*"

    while True:
        resp = client._make_request("GET", f"/search/query?q={query}&index={index_name}&size={size}&from={offset}&_source=id")
        if resp is None or resp.status_code != 200:
            print(f"❌ Search error: {resp.text if resp is not None else 'Unknown'}")
            break
        hits = resp.json().get("hits", {}).get("hits", [])
        if not hits:
            break
        ids.extend(h["_source"]["id"] for h in hits if "id" in h.get("_source", {}))
        offset += size
    return ids

def fetch_by_id(client, endpoint, item_id, fields):
    resp = client._make_request("GET", f"{endpoint}/{item_id}?fields={fields}")
    if resp is not None and resp.status_code == 200:
        return resp.json()
    return None

def main():
    service_filter = sys.argv[1] if len(sys.argv) > 1 else None
    client = OpenMetadataClient()

    json_dir_base = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    dq_dir = os.path.join(json_dir_base, "dataQuality")
    os.makedirs(dq_dir, exist_ok=True)

    if service_filter:
        print(f"🔍 Filtering DQ extraction for service: {service_filter}")

    # --- Fetch all metadata ---
    print("📦 Fetching Test Suite IDs...")
    suite_ids = get_all_ids_from_search(client, "test_suite_search_index", service_filter)
    print(f"   Found {len(suite_ids)} IDs. Fetching each...")
    suites = []
    for i, sid in enumerate(suite_ids):
        result = fetch_by_id(client, "/dataQuality/testSuites", sid, "owners,tags")
        if result:
            suites.append(result)
        else:
            print(f"   ⚠️  Skipping suite {sid} (failed to fetch)")
        if (i + 1) % 50 == 0:
            print(f"   ... {i + 1}/{len(suite_ids)}")

    print("\n📦 Fetching Test Case IDs...")
    case_ids = get_all_ids_from_search(client, "test_case_search_index", service_filter)
    print(f"   Found {len(case_ids)} IDs. Fetching each...")
    cases = []
    skipped = 0
    for i, cid in enumerate(case_ids):
        result = fetch_by_id(client, "/dataQuality/testCases", cid, "testDefinition,testSuite,owners,tags,parameterValues")
        if result:
            cases.append(result)
        else:
            skipped += 1
        if (i + 1) % 50 == 0:
            print(f"   ... {i + 1}/{len(case_ids)}")
    print(f"✅ Fetched {len(cases)} test cases ({skipped} skipped)\n")

    # --- Group and Save Test Suites ---
    print("📦 Grouping Test Suites by Service...")
    suites_by_service = {}
    for suite in suites:
        # For executable suites, the FQN starts with the service name: service.db.schema.table.testSuite
        # For logical suites, the name might be a UUID or custom name without dots.
        fqn = suite.get("fullyQualifiedName", "")
        if suite.get("testSuiteType") == "Logical":
            service = "Logical"
        elif "." in fqn:
            service = fqn.split(".")[0]
        else:
            service = "Generic"
        
        if service not in suites_by_service:
            suites_by_service[service] = []
        suites_by_service[service].append(suite)

    for service, service_suites in suites_by_service.items():
        service_dir = os.path.join(dq_dir, service)
        os.makedirs(service_dir, exist_ok=True)
        suites_file = os.path.join(service_dir, "test_suites.json")
        with open(suites_file, "w") as f:
            json.dump(service_suites, f, indent=2)
        print(f"   ✅ {service}: Saved {len(service_suites)} test suites")

    # --- Group and Save Test Cases ---
    print("\n📦 Grouping Test Cases by Service...")
    cases_by_service = {}
    for tc in cases:
        # Test cases have entityFQN: service.db.schema.table.column
        # Or entityLink: <#E::table::service.db.schema.table::columns::column>
        # We'll try entityFQN first as it's cleaner.
        fqn = tc.get("entityFQN", "")
        if not fqn:
             link = tc.get("entityLink", "")
             if "::table::" in link:
                 table_fqn = link.split("::table::")[1].split("::")[0]
                 service = table_fqn.split(".")[0]
             else:
                 service = "Generic"
        elif "." in fqn:
            service = fqn.split(".")[0]
        else:
            service = "Generic"

        if service not in cases_by_service:
            cases_by_service[service] = []
        cases_by_service[service].append(tc)

    for service, service_cases in cases_by_service.items():
        service_dir = os.path.join(dq_dir, service)
        os.makedirs(service_dir, exist_ok=True)
        cases_file = os.path.join(service_dir, "test_cases.json")
        with open(cases_file, "w") as f:
            json.dump(service_cases, f, indent=2)
        print(f"   ✅ {service}: Saved {len(service_cases)} test cases")

    print(f"\n✨ Done! Data quality tests grouped by service in {dq_dir}")

if __name__ == "__main__":
    main()
