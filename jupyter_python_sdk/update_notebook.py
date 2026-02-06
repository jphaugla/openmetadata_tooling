import nbformat as nbf
import os

notebook_path = '/Users/jasonhaugland/gits/openmetadata_tooling/metadata_analysis/FQN research.ipynb'

# Load the notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Filter out the previous bash/setup cells we added (by ID if possible, or just re-clean)
# We look for cells we added previously. Since we use specific IDs, we can target them.
ids_to_remove = [
    "setup-env-api", "header-lineage", "api-check-lineage", "api-compare-counts",
    "header-services", "api-get-db-service", "api-get-search-service", "api-get-glossary",
    "header-pipelines", "api-get-pipelines", "api-get-owner-id",
    "header-discovery", "api-list-roles", "api-list-services"
]
nb.cells = [cell for cell in nb.cells if cell.get('id') not in ids_to_remove]

# Define the new cells
new_cells = []

# 1. Imports Cell
new_cells.append(nbf.v4.new_code_cell(
    source="""# Native Python SDK Imports
from metadata.generated.schema.entity.data.table import Table
from metadata.generated.schema.entity.services.databaseService import DatabaseService
from metadata.generated.schema.entity.services.searchService import SearchService
from metadata.generated.schema.entity.data.glossary import Glossary
from metadata.generated.schema.entity.teams.user import User
from metadata.generated.schema.entity.teams.role import Role
from metadata.generated.schema.entity.services.ingestionPipelines.ingestionPipeline import IngestionPipeline

print("✅ SDK Classes imported.")""",
    id="sdk-imports"
))

# 2. Markdown Header
new_cells.append(nbf.v4.new_markdown_cell("## Lineage & Health Checks (Python SDK)"))

# 3. checkLineage
new_cells.append(nbf.v4.new_code_cell(
    source="""# checkLineage logic
table_fqn = "Cockroach_movr.movr.public.rides"
lineage = metadata.get_lineage_by_name(entity=Table, fqn=table_fqn)
print(f"Lineage for {table_fqn}:")
print(json.dumps(lineage, indent=2, default=str))""",
    id="sdk-check-lineage"
))

# 4. compare_counts
new_cells.append(nbf.v4.new_code_cell(
    source="""# compare_counts logic
user_list = metadata.list_entities(entity=User, limit=1)
print(f"📊 Database Users (Total): {user_list.paging.total}")""",
    id="sdk-compare-counts"
))

# 5. Markdown Header
new_cells.append(nbf.v4.new_markdown_cell("## Service & Glossary Management (Python SDK)"))

# 6. getDBService
new_cells.append(nbf.v4.new_code_cell(
    source="""# getDBService logic
service_name = "Cockroach_movr"
svc = metadata.get_by_name(entity=DatabaseService, fqn=service_name, fields=["owners", "tags"])
if svc:
    print(f"✅ Found Service: {svc.name.root}")
    print(svc.model_dump_json(indent=2))""",
    id="sdk-get-db-service"
))

# 7. getSearchService
new_cells.append(nbf.v4.new_code_cell(
    source="""# getSearchService logic
service_name = "elasticsearch"
svc = metadata.get_by_name(entity=SearchService, fqn=service_name, fields=["owners", "tags"])
if svc:
    print(f"✅ Found Search Service: {svc.name.root}")
    print(svc.model_dump_json(indent=2))
else:
    print(f"❌ Search Service {service_name} not found.")""",
    id="sdk-get-search-service"
))

# 8. getGlossary
new_cells.append(nbf.v4.new_code_cell(
    source="""# getGlossary logic
glossary_name = "Business Glossary"
glossary = metadata.get_by_name(entity=Glossary, fqn=glossary_name)
if glossary:
    print(f"✅ Found Glossary: {glossary.name.root}")
    print(glossary.model_dump_json(indent=2))""",
    id="sdk-get-glossary"
))

# 9. Markdown Header
new_cells.append(nbf.v4.new_markdown_cell("## Pipelines & Users (Python SDK)"))

# 10. getPipelines
new_cells.append(nbf.v4.new_code_cell(
    source="""# getPipelines logic
service_name = "Cockroach_movr"
pipelines = metadata.list_all_entities(entity=IngestionPipeline, fields=["owners"])
filtered = [p for p in pipelines if p.service.name == service_name]

print(f"✅ Found {len(filtered)} pipelines for {service_name}:")
for p in filtered:
    print(f"- {p.name.root} ({p.pipelineType.value})")""",
    id="sdk-get-pipelines"
))

# 11. getOwnerID
new_cells.append(nbf.v4.new_code_cell(
    source="""# getOwnerID logic
owner_name = "jason.haugland"
user = metadata.get_by_name(entity=User, fqn=owner_name)
if user:
    print(f"👤 User: {user.name}")
    print(f"🆔 ID: {user.id}")""",
    id="sdk-get-owner-id"
))

# 12. Markdown Header
new_cells.append(nbf.v4.new_markdown_cell("## Discovery (Python SDK)"))

# 13. list_roles
new_cells.append(nbf.v4.new_code_cell(
    source="""# list_roles logic
roles = metadata.list_entities(entity=Role)
print("Available Roles:")
for r in roles.data:
    print(f"- {r.name.root}: {r.id}")""",
    id="sdk-list-roles"
))

# 14. list_services
new_cells.append(nbf.v4.new_code_cell(
    source="""# list_services logic
services = metadata.list_entities(entity=DatabaseService)
print("Database Services:")
for s in services.data:
    print(f"- {s.name.root} ({s.serviceType.value})")""",
    id="sdk-list-services"
))

# Append the new cells
nb.cells.extend(new_cells)

# Save the notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"✅ Successfully updated {notebook_path} with native Python SDK code.")
