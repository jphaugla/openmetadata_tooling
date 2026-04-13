import boto3
import json
import sys

S3_BUCKET = "collate-snowflake-interchange-118146679784"

def inspect_bucket_security():
    s3 = boto3.client("s3")
    print(f"🕵️  Inspecting security for bucket: {S3_BUCKET}\n")

    try:
        # 1. Public Access Block
        try:
            pab = s3.get_public_access_block(Bucket=S3_BUCKET)
            print("🛡️  Public Access Block Settings:")
            print(json.dumps(pab.get("PublicAccessBlockConfiguration", {}), indent=2))
        except Exception as e:
            print(f"❌ Error fetching Public Access Block: {e}")

        # 2. Encryption
        print("\n🔐 Encryption Settings:")
        try:
            encryption = s3.get_bucket_encryption(Bucket=S3_BUCKET)
            print(json.dumps(encryption.get("ServerSideEncryptionConfiguration", {}), indent=2))
        except Exception as e:
            if "ServerSideEncryptionConfigurationNotFoundError" in str(e):
                print("⚠️  No default encryption configured (likely using default Amazon S3 managed keys).")
            else:
                print(f"❌ Error fetching Encryption: {e}")

        # 3. Bucket Policy
        print("\n📜 Bucket Policy:")
        try:
            policy = s3.get_bucket_policy(Bucket=S3_BUCKET)
            print(json.dumps(json.loads(policy.get("Policy", "{}")), indent=2))
        except Exception as e:
            if "NoSuchBucketPolicy" in str(e):
                print("⚠️  No bucket policy found.")
            else:
                print(f"❌ Error fetching Policy: {e}")

        # 4. ACL
        print("\n📋 Bucket ACL:")
        try:
            acl = s3.get_bucket_acl(Bucket=S3_BUCKET)
            print(json.dumps(acl.get("Grants", []), indent=2))
        except Exception as e:
            print(f"❌ Error fetching ACL: {e}")

    except Exception as e:
        print(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    inspect_bucket_security()
