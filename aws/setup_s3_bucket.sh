#!/bin/bash
# aws/setup_s3_bucket.sh
# This script sets up the S3 bucket used for Snowflake interchange with full security compliance.
# Bucket: collate-snowflake-interchange-118146679784

BUCKET_NAME="collate-snowflake-interchange-118146679784"
REGION="us-east-2"

echo "🚀 Creating bucket $BUCKET_NAME in $REGION..."
aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION --create-bucket-configuration LocationConstraint=$REGION

# 1. Enable Versioning (Required for Drata compliance)
echo "✅ Enabling bucket versioning..."
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled

# 2. Enable Default Encryption (AES256)
echo "🔐 Enabling server-side encryption..."
aws s3api put-bucket-encryption --bucket $BUCKET_NAME --server-side-encryption-configuration '{
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
aws s3api put-public-access-block --bucket $BUCKET_NAME --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
}'

# 4. Apply Bucket Policy (Allow Collate Ingestion Role)
echo "📄 Applying bucket policy..."
cat <<EOF > bucket_policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::650251687937:role/saas-jsonh-pov-ingestion"
            },
            "Action": [
                "s3:GetBucketLocation",
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::$BUCKET_NAME"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::650251687937:role/saas-jsonh-pov-ingestion"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket_policy.json
rm bucket_policy.json

echo "✨ S3 setup complete!"
