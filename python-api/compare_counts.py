#!/usr/bin/env python3
import sys
import requests
from om_client import OpenMetadataClient

def main():
    client = OpenMetadataClient()
    
    # 1. Fetch DB User Count
    response_db = client._make_request("GET", "/users")
    user_count_db = 0
    if response_db and response_db.status_code == 200:
        user_count_db = response_db.json().get("paging", {}).get("total", 0)
    else:
        print("❌ Error fetching User count from OpenMetadata Database.")
        sys.exit(1)

    # 2. Fetch ES User Count (assumes default local port 9200 and no auth)
    # Note: If ES requires auth, this would need to pull ES credentials from env
    try:
        response_es = requests.get("http://localhost:9200/user_search_index/_count")
        if response_es.status_code == 200:
            user_count_es = response_es.json().get("count", 0)
        else:
            print(f"❌ Error fetching User count from ElasticSearch. Status: {response_es.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to ElasticSearch on localhost:9200: {e}")
        sys.exit(1)

    # 3. Compare
    print(f"📊 Database Users: {user_count_db}")
    print(f"🔍 Search Index Users: {user_count_es}")

    if user_count_db == user_count_es:
        print("✅ System is in sync!")
    else:
        print("⚠️ Mismatch detected. Run ./reindex.sh")

if __name__ == "__main__":
    main()
