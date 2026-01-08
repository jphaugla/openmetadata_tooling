# 🐳 Subdirectory: `/docker` README.md

This directory handles the lifecycle of the OpenMetadata infrastructure using Docker. It includes automation to fetch the latest official configurations and manage the underlying containers and volumes.

## 🚀 Getting Started

1. **Fetch Infrastructure Configs**:
Before the first run, use the retrieval script to pull the official Docker Compose files from the OpenMetadata GitHub repository:
```bash
./getComposeFiles.sh

```


2. **Start the Stack**:
```bash
./startit.sh

```


3. **Access the UI**:
Open [http://localhost:8585](https://www.google.com/search?q=http://localhost:8585) (Default Creds: `admin` / `admin`).

## 📄 Script Catalog

| Script | Purpose |
| --- | --- |
| `getComposeFiles.sh` | Downloads the latest `docker-compose.yml` and environment files from the official OpenMetadata source. |
| `startit.sh` | Orchestrates the `docker compose up` command to bring all services online. |
| `stopit.sh` | Shuts down the containers safely while maintaining data persistence. |
| `clean_docker.sh` | Stops and **removes** the containers. |
| `clean_volumes.sh` | **Factory Reset**: Deletes all Docker volumes (MySQL data, Search indices, and Airflow logs). |
| `psql.sh` | Helper script to open a PostgreSQL terminal for direct metadata database inspection (if using Postgres). |

---

# 📡 Subdirectory: `/api` README.md

Automation layer for managing CockroachDB metadata services within the OpenMetadata framework.

## 🔐 Environment Setup (Required)

The following variables must be exported to your shell for the scripts to function:

```bash
export TOKEN="your_jwt_token"      # Admin Bot Token
export API_BASE="http://localhost:8585/api/v1"
export DB_USER="non_root"              # CockroachDB Username with admin permission on the databases
export DB_PASS="********"          # CockroachDB Password
export CA_CERT="-----BEGIN..."     # Raw CA Cert text

```

## 📄 Script Catalog

| Script | Type | Action |
| --- | --- | --- |
| `cockroach_db_add.sh` | **Bulk** | Registers the 7 standard CockroachDB demo services. |
| `cockroach_db_delete.sh` | **Bulk** | Hard-deletes the entire suite of CockroachDB services. |
| `delete_service.sh` | **Single** | Surgically removes one service by name (requires argument). |
| `checkService.sh` | **Utility** | Validates existence and returns connection status. |
| `get_cockroach_db.sh` | **Utility** | Fetches the full JSON definition of a service. |

---

## 💡 The "Week One" Pro-Tip

1. **The Fetch**: Use `getComposeFiles.sh` to ensure your local Docker setup matches the OpenMetadata 1.11.4 requirements.
2. **The Infrastructure**: Run `startit.sh` and give the system ~2 minutes to fully initialize the search indices and ingestion bot.
3. **The Automation**: Run `cockroach_db_add.sh`.
4. **The Handshake**: Services added via API will show a status of **Unknown** initially.
5. **The Blue Button**: Navigate to the **Agents** tab in the UI and click **Trigger AutoPilot**. This tells the ingestion container to start crawling your CockroachDB instances.

---
