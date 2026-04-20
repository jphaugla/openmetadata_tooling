#!/usr/bin/env python3
import boto3
import os
import subprocess
import sys

def main():
    print("🔑 Fetching local AWS credentials...")
    try:
        session = boto3.Session()
        creds = session.get_credentials().get_frozen_credentials()
        os.environ['AWS_ACCESS_KEY_ID'] = creds.access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = creds.secret_key
        os.environ['AWS_SESSION_TOKEN'] = creds.token
    except Exception as e:
        print(f"❌ Failed to get AWS creds: {e}")
        print("Make sure you run `aws sso login` first!")
        return

    # Pass any commands provided directly to dbt
    cmd = ["dbt"] + sys.argv[1:] if len(sys.argv) > 1 else ["dbt", "run-operation", "load_s3_data"]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    subprocess.run(cmd, env=os.environ)

if __name__ == "__main__":
    main()
