# Collate SE dbt Transformation Project

This directory contains the [dbt](https://www.getdbt.com/) project used to manage data transformations in the `COLLATE_SE` schema within the Snowflake `CUSTOMERS` database. 

It replaces the legacy manual SQL scripts (`run_queries.py`) with a structured, version-controlled approach that provides automatic data lineage, testing, and documentation.

## 📁 Project Structure

```text
dbt/
├── dbt_project.yml    # Project configuration
├── macros/
│   └── load_s3_data.sql # Executes Snowflake COPY INTO from S3
├── models/
│   ├── sources.yml    # Definition of raw Snowflake tables (from S3)
│   ├── staging/       # Initial cleanup and renaming
│   └── production/    # Final business entities (Customers, Orders, etc.)
├── run_with_aws.py    # Wrapper script to securely inject AWS credentials
└── README.md          # This file
```

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+
- Use the dedicated virtual environment in this directory:
  ```bash
  cd dbt
  python3 -m venv venv
  source venv/bin/activate
  pip install dbt-snowflake
  ```

### 2. Configure Profile
dbt requires a connection profile. Create or edit `~/.dbt/profiles.yml` and add the following:

```yaml
collate_snowflake:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: [your_snowflake_account]
      user: [your_username]
      password: [your_password]
      role: SALES_ENGINEERS
      database: CUSTOMERS
      warehouse: COMPUTE_WH
      schema: COLLATE_SE
      threads: 4
```

### 3. Load S3 Data & Run dbt
Before running dbt, you must load the raw `.csv` data from S3 into the raw Snowflake tables. Because Snowflake `COPY INTO` requires AWS permissions to read the buckets, we use a wrapper script that automatically grabs your SSO credentials and feeds them to the dbt macro.

Ensure you have run `aws sso login` recently, then execute:

```bash
cd dbt
# 1. Inject AWS creds and load raw S3 data into Snowflake
./run_with_aws.py run-operation load_s3_data --target-path target_custom

# 2. Transform the raw data into finalized business entities
dbt run
```

## 🛠️ Common Commands

| Command | Description |
| :--- | :--- |
| `dbt run` | Execute all models and create/update tables in Snowflake. |
| `dbt test` | Run data quality tests defined in `.yml` files. |
| `dbt docs generate` | Generate a documentation website for the project. |
| `dbt docs serve` | Serve the documentation website locally. |
| `dbt clean` | Delete the compiled artifacts in the `target/` directory. |

## 🔗 Integration with Collate (OpenMetadata)
One of the primary benefits of using dbt in this workspace is the **Automatic Lineage** integration.

1. **Manifest Generation**: When you run `dbt run`, dbt generates a `target/manifest.json` file.
2. **Catalog Metadata**: Collate's Snowflake ingestion can be configured to consume this `manifest.json`.
3. **Perfect Lineage**: Collate will automatically draw the data flow from the raw Snowflake tables through the staging layer and into the final production models, including column-level lineage.

---
**Note:** Ensure your Snowflake user has the necessary permissions to create tables in the `COLLATE_SE` schema of the `CUSTOMERS` database.
