Here is the updated `README.md` including the new **CockroachDB Scripts** section. I’ve placed it right after the Ingestion Framework section to keep the "Script Catalog" flow consistent.

---

# 🚀 OpenMetadata & CockroachDB Automation

This repository manages the lifecycle of OpenMetadata using Docker and provides an automation layer to register CockroachDB services via API.

### 🔗 Quick Links (Collate Resources)

* **[Collate Official Documentation](https://docs.getcollate.io/)**
* **[Local Docker Deployment Guide](https://docs.getcollate.io/quick-start/local-docker-deployment)**
* **[Ingestion Framework Overview](https://docs.getcollate.io/deployment/ingestion)**
* **[Hybrid Ingestion Runner Docs](https://docs.getcollate.io/getting-started/day-1/hybrid-saas/index#hybrid-ingestion-runner-secure-metadata-workflows-in-your-cloud)** 🆕
* **[Managing Teams & Roles](https://docs.getcollate.io/how-to-guides/admin-guide/teams-and-users/add-users)**
* **[Data Mesh: Domains & Data Products](https://docs.getcollate.io/how-to-guides/data-governance/domains-&-data-products)**

---

## 📑 Table of Contents

1. [Docker Infrastructure (/docker)](https://www.google.com/search?q=%23-docker-infrastructure-)
2. [API Automation Layer (/api)](https://www.google.com/search?q=%23-api-automation-layer-)
3. [Ingestion Framework (/ingestionFramework)](https://www.google.com/search?q=%23-ingestion-framework-)
4. [CockroachDB Scripts (/cockroach_scripts)](https://www.google.com/search?q=%23-cockroachdb-scripts-)
5. [CockroachDB Setup](https://www.google.com/search?q=%23-cockroachdb-setup)
6. [Ingestion Agent Workflow](https://www.google.com/search?q=%23-run-agents)
7. [Pro-Tips](https://www.google.com/search?q=%23-the-week-one-pro-tip)

---

## 🐳 Docker Infrastructure 

(`/docker`)

Handles the lifecycle of OpenMetadata infrastructure. Includes automation to fetch official configurations and manage containers/volumes.

### Getting Started

Follow the steps documented in the [Collate Docker Deployment](https://www.google.com/search?q=https://docs.getcollate.io/deployment/docker/local-deployment) guide:

1. **Fetch Infrastructure Configs**:
Before the first run, pull the official Docker Compose files:

```bash
./getComposeFiles.sh

```

2. **Start the Stack**:

```bash
./startit.sh

```

3. **Access the UI**:

* **OpenMetadata UI**: [http://localhost:8585](https://www.google.com/search?q=http://localhost:8585)
*(Creds: `admin@open-metadata.org` / `admin`)*
* **Airflow UI**: [http://localhost:8080](https://www.google.com/search?q=http://localhost:8080)
*(Creds: `admin` / `admin`)*

### Docker Script Catalog

| Script | Purpose |
| --- | --- |
| `getComposeFiles.sh` | Downloads latest `docker-compose.yml` and env files. |
| `startit.sh` | Orchestrates `docker compose up`. |
| `stopit.sh` | Shuts down containers safely (maintains data). |
| `clean_docker.sh` | Stops and **removes** containers. |
| `clean_volumes.sh` | **Factory Reset**: Deletes all volumes (MySQL, Search, Airflow). |
| `psql.sh` | Helper to open a PostgreSQL terminal for metadata inspection. |

---

## 📡 API Automation Layer 

(`/api`)

Automation for managing CockroachDB metadata services within OpenMetadata.

### Environment Setup (Required)

Export these variables to your shell:

```bash
export TOKEN="your_jwt_token"              # Admin Bot Token
export API_BASE="http://localhost:8585/api/v1"
export MY_CRDB_USER="non_root"             # CRDB User with admin permissions
export MY_CRDB_PASS="********"             # CRDB Password
export CA_CERT="-----BEGIN..."             # Raw CA Cert text

```

### API Script Catalog

| Script | Type | Action |
| --- | --- | --- |
| `cockroach_db_add.sh` | **Bulk** | Registers 7 standard CockroachDB demo services. |
| `cockroach_db_delete.sh` | **Bulk** | Hard-deletes the entire suite of services. |
| `delete_service.sh` | **Single** | Surgically removes one service by name. |
| `checkService.sh` | **Utility** | Validates existence and connection status. |
| `get_cockroach_db.sh` | **Utility** | Fetches the full JSON definition of a service. |

---

## ⚙️ Ingestion Framework

(`/ingestionFramework`)

This directory contains the tooling required for a **Hybrid SaaS Deployment**.

### Overview: The Hybrid Ingestion Runner

The **Hybrid Ingestion Runner** bridges the gap between your private infrastructure and the Collate Cloud (SaaS). It allows you to securely execute ingestion workflows within your own environment (e.g., local Mac or private cloud) while hosting the metadata server on Collate's cloud. This architecture ensures that sensitive credentials and data access remain within your local boundary; the SaaS platform only triggers the workflows and receives the resulting metadata, without ever touching your secrets.

### Framework File Catalog

| File | Purpose |
| --- | --- |
| `install.sh` | **Environment Setup**: Creates a local Python virtual environment (`venv-collate`) and installs the specific OpenMetadata ingestion packages (v1.11.4) required to match the server version. It specifically handles the `cockroach` and `snowflake` extras. |
| `run_ingest.sh` | **Execution Wrapper**: The command-line trigger for the ingestion process. It invokes the metadata CLI using the configuration defined in the YAML file. |
| `crdb_ingest_movr.yaml` | **Configuration**: Defines the `source` (Local CockroachDB `movr` database) and `sink` (Collate SaaS API). It includes security settings (`verify-ca` SSL mode), local certificate paths, and filter patterns to only ingest the `public` schema. |

---

## 🪳 CockroachDB Scripts

(`/cockroach_scripts`)

Helper utility scripts to interact with the local secure CockroachDB instance. These wrappers simplify connecting to a secure cluster by automatically handling certificate paths and ports.

### DB Script Catalog

| File | Purpose |
| --- | --- |
| `sql.sh` | **Interactive Shell**: Opens a secure SQL terminal session to the local cluster using the configured certificates. |
| `sql_file.sh` | **File Executor**: Executes a specific `.sql` file against the database. <br>

<br> *Usage:* `./sql_file.sh <filename.sql>`. |
| `create_crdb_admin.sql` | **Initialization**: A SQL script that creates the admin user (`jhaugland`), grants default database access, and assigns admin privileges. |

---

## 🦎 CockroachDB Setup

### Create CockroachDB Admin User

Use the provided script to initialize the admin user:

```bash
cd scripts
./sql_file.sh create_crdb_admin.sql

```

### Create CockroachDB Databases (Workloads)

Follow the [Official Cockroach Workload Documentation](https://www.cockroachlabs.com/docs/stable/cockroach-workload). Available built-in workloads:

> `movr`, `bank`, `kv`, `tpcc`, `ycsb`, `intro`, `startrek`

---

## 🤖 Run Agents

First, run `cockroach_db_add.sh` to create the services. For each service (**Cockroach_movr**, **bank**, **kv**, etc.), follow this sequence:

1. **Prerequisites**: Ensure workloads are running and the admin user exists.
2. **Validation**: In the UI (localhost:8585), go to **Settings -> [Service Name] -> Connection** and click **Test Connection**.
3. **Add Agents (Order is Critical)**:

#### 1. Metadata Agent

* **Hierarchical Owner Config**: Set `Default`, `Service`, and `Database` to **admin**.
* Set `Database` and `DatabaseSchema` to **Option1**.
* Run and ensure success.

#### 2. Profiler Agent

* **Profile Sample Type**: Change to **ROWS**.
* Deploy, run, and ensure success.

#### 3. AutoClassification Agent

* **Toggle**: Enable **Store Sample Data**.
* Deploy, run, and ensure success.

---

## 💡 The "Week One" Pro-Tip

1. **The Fetch**: Use `getComposeFiles.sh` to ensure local setup matches OpenMetadata 1.11.4 requirements.
2. **The Infrastructure**: Run `startit.sh` and allow ~2 minutes for search indices and bots to initialize.
3. **The Automation**: Run `cockroach_db_add.sh`.
4. **The Handshake**: Services added via API will initially show a status of **Unknown**.
5. **Add Agents**: Navigate to the **Agents** tab in the UI and add the agents in the correct order.
