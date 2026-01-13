# 🚀 OpenMetadata & CockroachDB Automation

This repository manages the lifecycle of OpenMetadata using Docker and provides an automation layer to register CockroachDB services via API.

### 🔗 Quick Links (Collate Resources)

* **[Collate Official Documentation](https://www.google.com/search?q=https://docs.getcollate.io/)**
* **[Local Docker Deployment Guide](https://docs.getcollate.io/quick-start/local-docker-deployment)**
* **[Ingestion Framework Overview](https://www.google.com/search?q=https://docs.getcollate.io/connectors/ingestion)**
* **[Managing Teams & Roles](https://www.google.com/search?q=https://docs.getcollate.io/main-concepts/metadata-standard/governance/teams-roles)**
* **[Data Mesh: Domains & Data Products](https://www.google.com/search?q=https://docs.getcollate.io/main-concepts/metadata-standard/governance/domains)**

---

## 📑 Table of Contents

1. [Docker Infrastructure (`/docker`)](https://www.google.com/search?q=%23-docker-infrastructure-docker)
* [Getting Started](https://www.google.com/search?q=%23getting-started)
* [Docker Script Catalog](https://www.google.com/search?q=%23docker-script-catalog)


2. [API Automation Layer (`/api`)](https://www.google.com/search?q=%23-api-automation-layer-api)
* [Environment Setup](https://www.google.com/search?q=%23environment-setup-required)
* [API Script Catalog](https://www.google.com/search?q=%23api-script-catalog)


3. [CockroachDB Setup](https://www.google.com/search?q=%23-cockroachdb-setup)
* [Admin User Creation](https://www.google.com/search?q=%23create-cockroachdb-admin-user)
* [Sample Data (Workloads)](https://www.google.com/search?q=%23create-cockroachdb-databases-using-the-built-in-cockroach-workload)


4. [Ingestion Agent Workflow](https://www.google.com/search?q=%23-run-agents)
5. [Pro-Tips](https://www.google.com/search?q=%23-the-week-one-pro-tip)

---

## 🐳 Docker Infrastructure (`/docker`)

Handles the lifecycle of OpenMetadata infrastructure. Includes automation to fetch official configurations and manage containers/volumes.

### Getting Started

Follow the steps documented in the [Collate Docker Deployment](https://docs.getcollate.io/quick-start/local-docker-deployment) guide:

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

## 📡 API Automation Layer (`/api`)

Automation for managing CockroachDB metadata services within OpenMetadata.

### Environment Setup (Required)

Export these variables to your shell:

```bash
export TOKEN="your_jwt_token"              # Admin Bot Token
export API_BASE="http://localhost:8585/api/v1"
export MY_CRDB_USER="non_root"             # CRDB User with admin permissions
export MY_CRDB_PASS="********"             # CRDB Password
export CA_CERT="-----BEGIN..."             # Raw CA Cert text

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
5. **Add Agents**: Navigate to the **Agents** tab in the UI and add the agents in the correct order

