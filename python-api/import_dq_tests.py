#!/usr/bin/env python3
import sys
import json
import os
import urllib.parse
from om_client import OpenMetadataClient

def import_suites_from_file(client, suites_file, suites_endpoint, owner_id):
    if not os.path.isfile(suites_file):
        return
    
    print(f"\n📦 Importing Test Suites from {suites_file}...")
    with open(suites_file, "r") as f:
        suites_data = json.load(f)
    
    # Sort logical suites first
    suites_data.sort(key=lambda x: 0 if x.get("testSuiteType") == "Logical" else 1)

    for suite in suites_data:
        name = suite.get("name")
        print(f"  ➡️ Importing Suite: {name}")
        
        payload = {
            "name": name,
            "displayName": suite.get("displayName"),
            "description": suite.get("description"),
            "owners": [{"id": owner_id, "type": "user"}]
        }
        
        # Check for existing
        encoded_name = urllib.parse.quote(name)
        existing = client._make_request("GET", f"{suites_endpoint}/name/{encoded_name}")
        
        if existing is not None and existing.status_code == 200:
            print(f"    ℹ️  Already exists (skipping)")
        else:
            response = client._make_request("POST", suites_endpoint, json=payload)
            if response is not None and response.status_code in [200, 201]:
                print(f"    ✅ Success")
            else:
                err = response.json().get("message", response.text) if response is not None else "Unknown Error"
                print(f"    ❌ Failed: {err}")

def import_cases_from_file(client, cases_file, cases_endpoint, suites_endpoint, owner_id):
    if not os.path.isfile(cases_file):
        return
        
    print(f"\n📦 Importing Test Cases from {cases_file}...")
    with open(cases_file, "r") as f:
        cases_data = json.load(f)
    
    for tc in cases_data:
        tc_name = tc.get("name")
        test_def = tc.get("testDefinition", {})
        test_suite = tc.get("testSuite", {})
        
        if not test_def or not test_suite:
            print(f"  ⚠️ Skipping {tc_name}: Missing testDefinition or testSuite in JSON source.")
            continue
        
        print(f"  ➡️ Importing Test Case: {tc_name}")
        
        payload = {
            "name": tc_name,
            "displayName": tc.get("displayName"),
            "description": tc.get("description"),
            "testDefinition": test_def.get("fullyQualifiedName"),
            "entityLink": tc.get("entityLink"),
            "parameterValues": tc.get("parameterValues", []),
            "owners": [{"id": owner_id, "type": "user"}]
        }
        
        if suites_endpoint == "/testSuites":
             payload["testSuite"] = test_suite.get("fullyQualifiedName")
        
        encoded_tc_name = urllib.parse.quote(tc.get("fullyQualifiedName", tc_name))
        existing_tc = client._make_request("GET", f"{cases_endpoint}/name/{encoded_tc_name}")
        
        if existing_tc and existing_tc.status_code == 200:
            print(f"    ℹ️  Already exists (skipping)")
        else:
            response = client._make_request("POST", cases_endpoint, json=payload)
            if response is not None and response.status_code in [200, 201]:
                print(f"    ✅ Success")
            elif response is not None and response.status_code == 404:
                 print(f"    ❌ Failed: Entity not found (Ensure tables are ingested first)")
            else:
                err = response.json().get("message", response.text) if response is not None else "Unknown Request Error"
                print(f"    ❌ Failed: {err}")

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python import_dq_tests.py [suites|cases|all] [service_name_optional]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    service_filter = sys.argv[2] if len(sys.argv) > 2 else None
    
    client = OpenMetadataClient()
    owner_id = os.getenv("OWNER_ID")
    
    if not owner_id:
        print("❌ Error: Missing environment variable OWNER_ID.")
        sys.exit(1)

    json_dir_base = os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json"))
    dq_dir = os.path.join(json_dir_base, "dataQuality")
    
    if not os.path.isdir(dq_dir):
        print(f"❌ DQ directory not found: {dq_dir}")
        sys.exit(1)

    print("🔍 Detecting Data Quality API version on target instance...")
    suites_endpoint = "/dataQuality/testSuites"
    cases_endpoint = "/dataQuality/testCases"
    
    test_resp = client._make_request("GET", f"{suites_endpoint}?limit=1")
    if not test_resp or test_resp.status_code == 404:
        print("ℹ️  Target uses 1.11-style endpoints.")
        suites_endpoint = "/testSuites"
        cases_endpoint = "/testCases"
    else:
        print("✅ Target uses modern 1.12+ Data Quality endpoints.")

    # Collect all service directories
    subdirs = [d for d in os.listdir(dq_dir) if os.path.isdir(os.path.join(dq_dir, d))]
    
    if service_filter:
        if service_filter in subdirs:
            subdirs = [service_filter]
        else:
            # Check if it was a file in the base dq_dir
            if os.path.isfile(os.path.join(dq_dir, "test_suites.json")) or os.path.isfile(os.path.join(dq_dir, "test_cases.json")):
                print(f"ℹ️  Service filter '{service_filter}' not found as dir, but legacy files exist in base dir. Processing base dir.")
                subdirs = ["."]
            else:
                print(f"❌ Service '{service_filter}' not found in {dq_dir}")
                sys.exit(1)
    elif not subdirs:
        # Check for legacy files in base dir
        if os.path.isfile(os.path.join(dq_dir, "test_suites.json")) or os.path.isfile(os.path.join(dq_dir, "test_cases.json")):
            subdirs = ["."]
        else:
            print(f"❌ No service directories or legacy files found in {dq_dir}")
            sys.exit(1)

    for service in sorted(subdirs):
        current_dir = os.path.join(dq_dir, service)
        print(f"\n📂 Processing service: {service}")
        
        suites_file = os.path.join(current_dir, "test_suites.json")
        cases_file = os.path.join(current_dir, "test_cases.json")
        
        if mode in ["suites", "all"]:
            import_suites_from_file(client, suites_file, suites_endpoint, owner_id)
            
        if mode in ["cases", "all"]:
            import_cases_from_file(client, cases_file, cases_endpoint, suites_endpoint, owner_id)

    print("\n✨ Done! Data Quality import process finished.")

if __name__ == "__main__":
    main()
