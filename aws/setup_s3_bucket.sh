#!/bin/bash
# aws/setup_s3_bucket.sh
# Sets up the S3 bucket used for Snowflake interchange with full security compliance.
#
# Required environment variables:
#   S3_BUCKET    - Name of the S3 bucket to create
#   AWS_REGION   - AWS region (e.g. us-east-2)
#
# Optional environment variables:
#   S3_KEY_PREFIX - Folder prefix inside the bucket (default: "")
#
# Example:
#   export S3_BUCKET="my-collate-bucket"
#   export AWS_REGION="us-east-2"
#   bash setup_s3_bucket.sh

set -euo pipefail

if [[ -z "${S3_BUCKET:-}" ]]; then
    echo "❌ S3_BUCKET is not set. Export it before running this script."
    exit 1
fi

if [[ -z "${AWS_REGION:-}" ]]; then
    echo "❌ AWS_REGION is not set. Export it before running this script."
    exit 1
fi

echo "🚀 Creating bucket $S3_BUCKET in $AWS_REGION..."
aws s3api create-bucket \
    --bucket "$S3_BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"

# 1. Enable Versioning (Required for Drata compliance)
echo "✅ Enabling bucket versioning..."
aws s3api put-bucket-versioning \
    --bucket "$S3_BUCKET" \
    --versioning-configuration Status=Enabled

# 2. Enable Default Encryption (AES256)
echo "🔐 Enabling server-side encryption..."
aws s3api put-bucket-encryption \
    --bucket "$S3_BUCKET" \
    --server-side-encryption-configuration '{
    "Rules": [
        {
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }
    ]
}'

# 3. Block All Public Access
echo "🛡️  Blocking all public access..."
aws s3api put-public-access-block \
    --bucket "$S3_BUCKET" \
    --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
}'

# 4. Apply Bucket Policy (Allow Collate Ingestion Role)
#    Set COLLATE_INGESTION_ROLE_ARN to the IAM role ARN that needs read access.
if [[ -n "${COLLATE_INGESTION_ROLE_ARN:-}" ]]; then
    echo "📄 Applying bucket policy for role: $COLLATE_INGESTION_ROLE_ARN..."
    POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "${COLLATE_INGESTION_ROLE_ARN}"
            },
            "Action": [
                "s3:GetBucketLocation",
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::${S3_BUCKET}"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "${COLLATE_INGESTION_ROLE_ARN}"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
        }
    ]
}
EOF
)
    echo "$POLICY" > /tmp/bucket_policy.json
    aws s3api put-bucket-policy --bucket "$S3_BUCKET" --policy file:///tmp/bucket_policy.json
    rm /tmp/bucket_policy.json
else
    echo "⚠️  COLLATE_INGESTION_ROLE_ARN not set — skipping bucket policy."
    echo "   Re-run with COLLATE_INGESTION_ROLE_ARN exported to apply access policy."
fi

echo "✨ S3 setup complete for bucket: $S3_BUCKET"
