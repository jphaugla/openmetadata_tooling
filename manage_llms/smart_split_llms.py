import urllib.request
import re
import os
import sys

DEFAULT_URL = "https://docs.getcollate.io/llms-full.txt"

# Define top 20 popular data connectors to KEEP in the main document
TOP_CONNECTORS = [
    "snowflake", "bigquery", "redshift", "postgres", "postgresql", "mysql", 
    "databricks", "athena", "s3", "gcs", "adls", "oracle", "mssql", "sql server",
    "mongodb", "kafka", "tableau", "powerbi", "looker", "airflow", "dbt", 
    "fivetran", "glue", "dynamodb", "mariadb", "salesforce"
]

def is_infrequent_connector(header):
    # Check if this header represents a connector or runner
    if ("connector |" in header.lower() or "hybrid runner |" in header.lower() or "datalake |" in header.lower()):
        # If it's a connector, check if it's in our top list
        for top_conn in TOP_CONNECTORS:
            if top_conn in header.lower():
                return False # It IS a top connector, so don't flag as infrequent
        return True # It is a connector, but not in top 20
    return False

def categorize_section(header):
    header_lower = header.lower()
    
    # 1. Exhaustive connection schemas and options
    if "connection details" in header_lower or "connection options" in header_lower:
        return 1
        
    # 2. Infrequent connectors
    if is_infrequent_connector(header):
        return 2
        
    # 3. API and template references
    if ("api" in header_lower and "reference" in header_lower) or \
       "template context reference" in header_lower or \
       "yaml config" in header_lower or \
       header_lower.startswith("# get /") or \
       header_lower.startswith("# post /") or \
       header_lower.startswith("# put /") or \
       header_lower.startswith("# delete /") or \
       "api overview" in header_lower or \
       "create an api collection" in header_lower:
        return 3
        
    # 4. Everything Else
    return 4

def main():
    args = sys.argv[1:]
    no_split = False
    if "--no-split" in args:
        no_split = True
        args.remove("--no-split")
        
    url = args[0] if len(args) > 0 else DEFAULT_URL
    
    # Determine a prefix based on the URL to avoid overwriting files
    if "open-metadata" in url:
        file_prefix = "openmetadata"
    elif "getcollate" in url:
        file_prefix = "collate"
    else:
        file_prefix = "docs"

    output_dir = os.environ.get("GOOGLE_DRIVE_LOCATION")
    if not output_dir:
        raise RuntimeError("GOOGLE_DRIVE_LOCATION environment variable must be set.")
    output_dir = os.path.expanduser(output_dir)
    
    print(f"Output directory resolved to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading {url}...")
    try:
        response = urllib.request.urlopen(url)
        content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to download the file: {e}")
        return

    if no_split:
        base, ext = os.path.splitext(url)
        name = base.replace("https://", "").replace("http://", "")
        name = name.replace(".io", "").replace(".org", "").replace(".com", "")
        name = name.replace(".", "_").replace("/", "_")
        filename = f"{name}{ext}"
        
        file_path = os.path.join(output_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r+', encoding='utf-8') as f:
                f.seek(0)
                f.write(content)
                f.truncate()
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        print(f"Saved unsplit file to {filename}")
        return

    lines = content.split('\n')
    print(f"Total lines downloaded: {len(lines)}")
    
    categories = {
        1: {"name": f"{file_prefix}-1-connection-schemas.txt", "lines": []},
        2: {"name": f"{file_prefix}-2-infrequent-connectors.txt", "lines": []},
        3: {"name": f"{file_prefix}-3-api-templates.txt", "lines": []},
        4: {"name": f"{file_prefix}-4-core-documentation.txt", "lines": []}
    }
    
    current_category = 4
    current_chunk_lines = []
    
    for line in lines:
        if line.startswith('# '):
            # When a new top-level header is found, write the accumulated lines
            if current_chunk_lines:
                categories[current_category]["lines"].append('\n'.join(current_chunk_lines))
                current_chunk_lines = []
                
            # Determine new category
            current_category = categorize_section(line.strip())
            
        current_chunk_lines.append(line)
        
    # flush the last section
    if current_chunk_lines:
        categories[current_category]["lines"].append('\n'.join(current_chunk_lines))

    MAX_WORDS = 400000

    print("\n--- Output Summary ---")
    for cat_id, cat_data in categories.items():
        # If the category is very large, split it
        chunks = []
        current_chunk = []
        current_words = 0
        
        for section in cat_data["lines"]:
            section_words = len(section.split())
            if current_words + section_words > MAX_WORDS and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_words = 0
            
            current_chunk.append(section)
            current_words += section_words
            
        if current_chunk:
            chunks.append(current_chunk)
            
        # Write chunks to disk
        base_name = cat_data["name"]
        for i, chunk_lines in enumerate(chunks):
            full_text = '\n\n'.join(chunk_lines)
            word_count = len(full_text.split())
            
            # If multiple chunks, add part suffix
            file_name = base_name if len(chunks) == 1 else base_name.replace(".txt", f"-part{i+1}.txt")
            file_path = os.path.join(output_dir, file_name)
            
            # Explicitly update in-place to preserve inodes and Google Drive File IDs
            if os.path.exists(file_path):
                with open(file_path, 'r+', encoding='utf-8') as f:
                    f.seek(0)
                    f.write(full_text)
                    f.truncate()
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                
            print(f"{file_name}: {word_count} words (Size: {len(full_text) / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    main()
