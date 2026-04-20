#!/usr/bin/env python3
import sys
import os
from om_client import OpenMetadataClient

def main():
    service_name = "S3-Datalake"
    client = OpenMetadataClient()
    
    print(f"📊 Checking status for {service_name} ingestion...")
    
    pipelines = client.get_pipelines_for_service(service_name)
    
    if not pipelines:
        print(f"❌ No pipelines found for {service_name}.")
        sys.exit(1)
        
    for pipeline in pipelines:
        p_name = pipeline.get("name")
        p_status = pipeline.get("pipelineStatus")
        
        print("-" * 64)
        print(f"Pipeline: {p_name}")
        
        if p_status:
            state = p_status.get("pipelineState", "Unknown")
            start = p_status.get("startDate")
            end = p_status.get("endDate")
            
            print(f"Status: {state}")
            if start: print(f"Started: {start}")
            if end: print(f"Ended: {end}")
            
            # Print metrics if available
            records = p_status.get("status")
            if records:
                print(f"Metrics: {records}")
        else:
            print("Status: No run history yet.")
            
    print("-" * 64)

if __name__ == "__main__":
    main()
