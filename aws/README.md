# AWS Infrastructure

This directory documents the AWS components used for the OpenMetadata/Collate tooling.

## S3 Bucket

The S3 bucket serves as the landing zone for data exported from Collate (audit logs, change events, etc.) and as the source for Snowflake lineage in the SE environment.

The bucket name and region are never hardcoded. Set them as environment variables before running any script:

```bash
export S3_BUCKET="your-bucket-name"
export AWS_REGION="us-east-2"
```

These are the same variables consumed by the Python export scripts in `python-api/`:

| Variable | Used by |
|---|---|
| `S3_BUCKET` | `setup_s3_bucket.sh`, `export_audit_logs.py`, `export_events_to_s3.py` |
| `AWS_REGION` | `setup_s3_bucket.sh` |
| `S3_KEY_PREFIX` | `export_audit_logs.py`, `export_events_to_s3.py` (optional folder prefix) |

### Security Posture (Compliance)

| Feature | Status | Reason |
|---|---|---|
| **Versioning** | **Enabled** | Required by Drata/Compliance to prevent accidental data loss. |
| **Encryption** | **Enabled (AES256)** | Server-side encryption ensures data is encrypted at rest. |
| **Public Access** | **Blocked** | All four Public Access Block settings are enabled to prevent leaks. |
| **Least Privilege** | **Enabled** | Access is restricted to the specific Collate Ingestion IAM role via bucket policy. |

### Bucket Policy

The bucket grants read-only access to the Collate SaaS ingestion role. The role ARN is supplied at runtime via:

```bash
export COLLATE_INGESTION_ROLE_ARN="arn:aws:iam::<account-id>:role/<role-name>"
```

Permitted actions: `s3:ListBucket`, `s3:GetBucketLocation`, `s3:GetObject`.

If `COLLATE_INGESTION_ROLE_ARN` is not set, `setup_s3_bucket.sh` will create the bucket with versioning, encryption, and public-access blocking but skip the policy step and print a reminder.

## Setup Script

`setup_s3_bucket.sh` replicates the full bucket configuration in any environment.

```bash
export S3_BUCKET="your-bucket-name"
export AWS_REGION="us-east-2"
export COLLATE_INGESTION_ROLE_ARN="arn:aws:iam::<account-id>:role/<role-name>"
bash aws/setup_s3_bucket.sh
```
