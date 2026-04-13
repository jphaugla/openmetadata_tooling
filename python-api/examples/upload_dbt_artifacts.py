import boto3
import os
import sys

S3_BUCKET = "collate-snowflake-interchange-118146679784"
FOLDER = "dbt_tgts"
FILES = ["manifest.json", "catalog.json", "run_results.json"]
LOCAL_DIR = "dbt/target"

def upload_files():
    # Attempt to use the existing AWS session/credentials
    try:
        s3 = boto3.client("s3")
        
        # Test connection by listing bucket
        s3.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=1)
        print(f"✅ Connected to S3 bucket: {S3_BUCKET}")
        
        for file_name in FILES:
            local_path = os.path.join(LOCAL_DIR, file_name)
            s3_key = f"{FOLDER}/{file_name}"
            
            if os.path.exists(local_path):
                print(f"🚀 Uploading {local_path} to s3://{S3_BUCKET}/{s3_key}...")
                s3.upload_file(local_path, S3_BUCKET, s3_key)
                print(f"   ✅ Done: {file_name}")
            else:
                print(f"❌ Error: {local_path} not found!")
                
        print("\n🎉 All dbt artifacts uploaded to S3.")
        print(f"   Prefix: s3://{S3_BUCKET}/{FOLDER}/")
        
    except Exception as e:
        print(f"❌ Error connecting to S3 or uploading: {e}")
        sys.exit(1)

if __name__ == "__main__":
    upload_files()
