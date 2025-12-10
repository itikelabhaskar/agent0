"""
Load data from GCS bucket to BigQuery
Pulls Excel file from gs://prod-45-hackathon-bucket and loads to BigQuery
"""
import sys
import os
import tempfile
import pandas as pd
from google.cloud import storage, bigquery

# Configuration
PROJECT_ID = "prod-12-313"
DATASET_ID = "12-313"
GCS_BUCKET = "prod-45-hackathon-bucket"
GCS_FILE = "1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx"

print("=" * 70)
print("🚀 Loading Data from GCS to BigQuery")
print("=" * 70)
print()
print(f"Configuration:")
print(f"   Project: {PROJECT_ID}")
print(f"   Dataset: {DATASET_ID}")
print(f"   Source: gs://{GCS_BUCKET}/{GCS_FILE}")
print()

# Step 1: Download Excel from GCS
print("Step 1/4: Downloading Excel from GCS...")
print("-" * 70)
try:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob(GCS_FILE)
    
    if not blob.exists():
        print(f"❌ File not found: gs://{GCS_BUCKET}/{GCS_FILE}")
        sys.exit(1)
    
    # Download to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        print(f"   Downloading {blob.size / (1024*1024):.2f} MB...")
        blob.download_to_filename(tmp.name)
        excel_path = tmp.name
    
    print(f"✅ Downloaded to: {excel_path}")
    
except Exception as e:
    print(f"❌ Failed to download from GCS: {e}")
    sys.exit(1)

print()

# Step 2: Read Excel sheets
print("Step 2/4: Reading Excel sheets...")
print("-" * 70)
try:
    xls = pd.ExcelFile(excel_path)
    sheets = xls.sheet_names
    print(f"✅ Found {len(sheets)} sheets: {sheets}")
    
    sheets_data = {}
    for sheet in sheets:
        df = pd.read_excel(xls, sheet_name=sheet)
        sheets_data[sheet] = df
        print(f"   - {sheet}: {len(df)} rows, {len(df.columns)} columns")
    
except Exception as e:
    print(f"❌ Failed to read Excel: {e}")
    os.unlink(excel_path)
    sys.exit(1)

print()

# Step 3: Create BigQuery dataset
print("Step 3/4: Setting up BigQuery dataset...")
print("-" * 70)
try:
    bq_client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    try:
        dataset = bq_client.get_dataset(dataset_ref)
        print(f"✅ Dataset already exists: {DATASET_ID}")
    except:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "us"
        bq_client.create_dataset(dataset)
        print(f"✅ Created dataset: {DATASET_ID}")
    
except Exception as e:
    print(f"❌ Failed to create dataset: {e}")
    os.unlink(excel_path)
    sys.exit(1)

print()

# Step 4: Load each sheet to BigQuery
print("Step 4/4: Loading sheets to BigQuery...")
print("-" * 70)

for sheet_name, df in sheets_data.items():
    # Clean table name
    table_name = sheet_name.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    print(f"Loading {sheet_name} → {table_name}...")
    
    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True
        )
        
        job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        table = bq_client.get_table(table_id)
        print(f"   ✅ Loaded {table.num_rows} rows to {table_name}")
        
    except Exception as e:
        print(f"   ❌ Failed to load {sheet_name}: {e}")

print()

# Cleanup temp file
try:
    os.unlink(excel_path)
    print("✅ Cleaned up temporary files")
except:
    pass

print()

# Create auxiliary tables
print("Creating auxiliary tables...")
print("-" * 70)

auxiliary_tables = {
    "rules": """
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.rules` (
            rule_id STRING,
            created_by STRING,
            created_ts TIMESTAMP,
            rule_text STRING,
            sql_snippet STRING,
            active BOOL,
            source STRING
        )
    """,
    "issues": """
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.issues` (
            issue_id STRING,
            rule_id STRING,
            rule_text STRING,
            detected_ts TIMESTAMP,
            source_table STRING,
            match_json STRING,
            reviewed BOOL,
            severity STRING,
            note STRING
        )
    """,
    "users": """
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.users` (
            user_id STRING,
            email STRING,
            full_name STRING,
            role STRING,
            created_ts TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOL
        )
    """,
    "audit_log": """
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.audit_log` (
            audit_id STRING,
            user_email STRING,
            action_type STRING,
            action_target STRING,
            action_details STRING,
            timestamp TIMESTAMP,
            status STRING
        )
    """
}

for table_name, sql in auxiliary_tables.items():
    try:
        query = sql.format(project=PROJECT_ID, dataset=DATASET_ID)
        bq_client.query(query).result()
        print(f"✅ {table_name} table ready")
    except Exception as e:
        print(f"⚠️  {table_name} table: {e}")

print()

# Verify all tables
print("=" * 70)
print("✅ LOAD COMPLETE!")
print("=" * 70)
print()
print(f"Tables created in {PROJECT_ID}.{DATASET_ID}:")

tables = list(bq_client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
for table in tables:
    t = bq_client.get_table(table)
    print(f"   • {table.table_id}: {t.num_rows} rows")

print()
print(f"🔗 View in BigQuery:")
print(f"   https://console.cloud.google.com/bigquery?project={PROJECT_ID}&d={DATASET_ID}")
print()
print(f"Next steps:")
print(f"   1. Update config files with project: {PROJECT_ID}, dataset: {DATASET_ID}")
print(f"   2. python run_backend.py")
print(f"   3. streamlit run frontend/app.py")
print()
print("=" * 70)

