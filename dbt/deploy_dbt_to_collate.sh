#!/bin/bash
# deploy_dbt_to_collate.sh
# Generates the dbt documentation artifacts (catalog.json, manifest.json)
# and uploads them along with run_results.json to the S3 bucket for Collate ingestion.

set -e

echo "=========================================="
echo "🚀 1. Generating dbt documentation targets"
echo "=========================================="
# Ensure we are in the dbt venv
source venv/bin/activate

# Use the wrapper to inject AWS credentials and build into dbt_tgts
./run_with_aws.py docs generate --target-path dbt_tgts

echo ""
echo "=========================================="
echo "☁️  2. Uploading dbt targets to S3"
echo "=========================================="
# Run the python script to securely push to S3 using boto3
./upload_dbt.py

echo ""
echo "=========================================="
echo "✅ Deployment to Collate S3 Storage Complete!"
echo "=========================================="
