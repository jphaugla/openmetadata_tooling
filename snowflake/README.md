# Snowflake Scripts

This directory contains the core scripts to build and maintain the `COLLATE_SE` schema. The logic has been unified into a single "Drop, Rebuild, and Load" workflow.

---

## Quick Start

```bash
cd snowflake/

# 1. Export source data from COLLATE_SHOP to S3
# This ensures s3://collate-snowflake-interchange-118146679784/ has fresh data
python3 export_to_s3.py

# 2. Drop and Rebuild COLLATE_SE (DDL only)
python3 rebuild_collate_se.py

# 3. Load data and compute columns (Lineage!)
python3 run_queries.py
```

---

## Workflow Explanation

### Step 1: `export_to_s3.py` (Extract)
This script reads the production tables from `COLLATE_SHOP` and uploads them as CSVs to S3.

### Step 2: `rebuild_collate_se.py` (Structure)
This script executes `rebuild_collate_se.sql` to drop and recreate the schema and all table/view structures (DDL). It ensures a clean slate with correct ownership.

### Step 3: `run_queries.py` (Load & Lineage)
This script executes `import_and_transform.sql` to perform the actual data movement:
1.  **S3 → RAW**: `COPY INTO` commands generate the S3-to-RAW lineage.
2.  **RAW → PROD**: `INSERT` and `UPDATE` commands generate the RAW-to-PROD lineage and calculate computed columns.

---

## Core File Reference

| File | Purpose |
|---|---|
| `rebuild_collate_se.py` | Orchestrator: Runs the master SQL script as JASON. |
| `rebuild_collate_se.sql` | Master SQL: DDL + DML + Grants for the entire schema. |
| `export_to_s3.py` | Data Pump: COLLATE_SHOP → S3. |
| `query_snowflake.py` | Utility: Tests connection and role status. |
| `requirements.txt` | Python dependencies (snowflake-connector-python, boto3, cryptography). |

---

## Schema Architecture: COLLATE_SE

The schema mirrors `COLLATE_SHOP` but is independently owned by `JASON` and optimized for Sales Engineering demos.

### Lineage Graph in Collate
```
S3 Bucket ──► RAW Tables ──► Production Tables ──► Analytics Views
```

### Table: CUSTOMERS (Computed Columns)
Collate profiles this table to show data distributions. The rebuild script automatically calculates:
- `FIRST_ORDER` / `MOST_RECENT_ORDER`
- `NUMBER_OF_ORDERS`
- `CUSTOMER_LIFETIME_VALUE`

---

## Troubleshooting

- **Permissions**: If the scripts fail, run `python3 query_snowflake.py` to verify your current role. JASON should have his default role set to `SALES_ENGINEERS`.
- **S3 Access**: `export_to_s3.py` requires local AWS credentials valid for the interchange bucket.
- **Why not CLONE?**: We avoid `CLONE` because View DDL doesn't update schema references automatically, and it doesn't generate the query history needed for Collate lineage. The "Drop and Rebuild" method is cleaner.
