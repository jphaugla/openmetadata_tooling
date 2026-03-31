#!/usr/bin/env python3
import json
import os
import sys
import urllib.parse
from om_client import OpenMetadataClient

def get_entities_from_search(client, index_name, service_name, filter_pattern=None):
    """Find all entity IDs and types for a given service."""
    entities = []
    offset = 0
    size = 100
    
    if filter_pattern:
        # Combined query: Exact service name AND partial FQN match
        query = f"service.name:\"{service_name}\" AND fullyQualifiedName:*{filter_pattern}*"
    else:
        query = f"service.name:\"{service_name}\""
    
    while True:
        encoded_query = urllib.parse.quote(query)
        url = f"/search/query?q={encoded_query}&index={index_name}&size={size}&from={offset}&_source=id,entityType,fullyQualifiedName"
        resp = client._make_request("GET", url)
        
        if resp is None or resp.status_code != 200:
            # Fallback if service.name query fails, try FQN prefix
            if offset == 0:
                 if filter_pattern:
                      query = f"fullyQualifiedName:*{service_name}*{filter_pattern}*"
                 else:
                      query = f"fullyQualifiedName:\"{service_name}\".*"
                 continue
            break
            
        hits = resp.json().get("hits", {}).get("hits", [])
        if not hits:
            # If we got no hits but it's our first attempt, try the fallback
            if offset == 0 and "service.name" in query:
                if filter_pattern:
                    query = f"fullyQualifiedName:*{service_name}*{filter_pattern}*"
                else:
                    query = f"fullyQualifiedName:\"{service_name}\".*"
                continue
            break
            
        for hit in hits:
            source = hit.get("_source", {})
            if "id" in source:
                entities.append({
                    "id": source["id"],
                    "type": source.get("entityType", "table"),
                    "fqn": source.get("fullyQualifiedName")
                })
        
        offset += size
        if len(hits) < size:
            break
            
    return entities

def main():
    if len(sys.argv) < 2:
        print("❌ Error: No service name provided.")
        print("Usage: python export_lineage.py <service_name> [database_or_schema_filter]")
        print("Example: python export_lineage.py \"redshift prod\" \"marketing.public\"")
        sys.exit(1)

    service_name = sys.argv[1]
    # Join all subsequent arguments with dots (e.g. dev dbt_jaffle -> dev.dbt_jaffle)
    filter_pattern = ".".join(sys.argv[2:]) if len(sys.argv) > 2 else None
    
    client = OpenMetadataClient()
    
    print(f"🔍 Finding tables for service: {service_name}...")
    if filter_pattern:
        print(f"   (Applying filter: {filter_pattern})")

    entities = get_entities_from_search(client, "table_search_index", service_name, filter_pattern)
    
    if not entities:
        print(f"⚠️ No tables found for service '{service_name}' with filter '{filter_pattern or ''}'.")
        sys.exit(0)
        
    print(f"✅ Found {len(entities)} tables.")
    print(f"ℹ️  Note: We will check each table for lineage edges. This may take time for large services.")

    all_edges = {} # Use dict to store unique edges based on FQN pairs
    node_map = {} # Map ID to FQN for resolution
    processed_with_lineage = 0

    print(f"🚀 Fetching lineage for {len(entities)} entities...")
    
    for i, entity in enumerate(entities):
        if (i+1) % 50 == 0:
            print(f"   ... Processed {i+1}/{len(entities)} (Found {len(all_edges)} unique edges)")
            
        # We use the ID to fetch lineage
        url = f"/lineage/{entity['type']}/{entity['id']}?upstreamDepth=1&downstreamDepth=1"
        resp = client._make_request("GET", url)
        
        if resp and resp.status_code == 200:
            data = resp.json()
            
            # Extract nodes and edges
            nodes = data.get("nodes", [])
            edges = data.get("edges", []) or data.get("upstreamEdges", []) + data.get("downstreamEdges", [])
            
            if edges:
                processed_with_lineage += 1
                
                # Map nodes in this response to their FQNs
                for node in nodes:
                    node_map[node["id"]] = {
                        "fqn": node.get("fullyQualifiedName"),
                        "type": node.get("type") or node.get("entityType")
                    }
                
                # Add current entity to node_map if not there
                if entity["id"] not in node_map:
                    node_map[entity["id"]] = {"fqn": entity["fqn"], "type": entity["type"]}

                for edge in edges:
                    from_id = edge.get("fromEntity")
                    to_id = edge.get("toEntity")
                    
                    if from_id in node_map and to_id in node_map:
                        from_info = node_map[from_id]
                        to_info = node_map[to_id]
                        
                        edge_key = f"{from_info['fqn']}|{to_info['fqn']}"
                        if edge_key not in all_edges:
                            all_edges[edge_key] = {
                                "fromEntity": {"fqn": from_info["fqn"], "type": from_info["type"]},
                                "toEntity": {"fqn": to_info["fqn"], "type": to_info["type"]},
                                "lineageDetails": edge.get("lineageDetails")
                            }

    # Convert to list
    lineage_list = list(all_edges.values())
    
    # Save to JSON
    json_dir = os.path.join(os.environ.get("JSON_DIR", os.path.join(os.path.dirname(__file__), "..", "json")), "lineage")
    os.makedirs(json_dir, exist_ok=True)
    
    output_file = os.path.join(json_dir, f"{service_name.replace(' ', '_')}_lineage.json")
    with open(output_file, "w") as f:
        json.dump(lineage_list, f, indent=2)
        
    print(f"\n✨ Export Complete!")
    print(f"   - Total Tables Checked: {len(entities)}")
    print(f"   - Tables with Lineage: {processed_with_lineage}")
    print(f"   - Unique Edges Exported: {len(lineage_list)}")
    print(f"   - Saved to: {output_file}")

if __name__ == "__main__":
    main()
