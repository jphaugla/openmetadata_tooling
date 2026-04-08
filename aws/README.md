# AWS Infrastructure

This directory documents the AWS components used for the OpenMetadata/Snowflake tooling.

## S3 Bucket: `collate-snowflake-interchange-118146679784`

This bucket serves as the landing zone for raw data exported from Snowflake. It is the primary "Source" for data lineage in the SE environment.

### Security Posture (Compliance)

| Feature | Status | Reason |
|---|---|---|
| **Versioning** | **Enabled** | Required by Drata/Compliance to prevent accidental data loss. |
| **Encryption** | **Enabled (AES256)** | Server-side encryption ensures data is encrypted at rest. |
| **Public Access** | **Blocked** | All four Public Access Block settings are enabled to prevent leaks. |
| **Least Privilege** | **Enabled** | Access is restricted to Jason's local tools and the specific Collate Ingestion IAM role. |

### Bucket Policy

The bucket grants read-only access to the Collate SaaS ingestion role:
- **Role**: `arn:aws:iam::650251687937:role/saas-jsonh-pov-ingestion`
- **Actions**: `s3:ListBucket`, `s3:GetBucketLocation`, `s3:GetObject`.

### Automation

A setup script is provided in `aws/setup_s3_bucket.sh` to replicate this exact configuration in other environments if needed.
