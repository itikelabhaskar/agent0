"""
Load data from GCS bucket to BigQuery
Loads CSV files directly from gs://prod-45-hackathon-bucket to BigQuery
"""
import sys
import os
import pandas as pd
import io
from google.cloud import storage, bigquery

# Configuration
PROJECT_ID = "prod-12-335"
DATASET_ID = "dev_dataset"
GCS_BUCKET = "prod-45-hackathon-bucket_megalodon"
GCS_FOLDER = "1.1 Improving IP& Data Quality/"
CSV_FILES = {
    "sbox-Week1.csv": "week1",
    "sbox-Week2.csv": "week2",
    "sbox-Week3.csv": "week3",
    "sbox-Week4.csv": "week4"
}

print("=" * 70)
print("🚀 Loading Data from GCS to BigQuery")
print("=" * 70)
print()
print(f"Configuration:")
print(f"   Project: {PROJECT_ID}")
print(f"   Dataset: {DATASET_ID}")
print(f"   Source: gs://{GCS_BUCKET}/{GCS_FOLDER}")
print(f"   CSV Files: {list(CSV_FILES.keys())}")
print()

# Step 1: Read CSV files from GCS
print("Step 1/3: Reading CSV files from GCS...")
print("-" * 70)
try:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET)
    
    csv_data = {}
    for csv_file, table_name in CSV_FILES.items():
        file_path = GCS_FOLDER + csv_file
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            print(f"❌ File not found: gs://{GCS_BUCKET}/{file_path}")
            sys.exit(1)
        
        print(f"   Reading {csv_file}...")
        csv_content = blob.download_as_text()
        df = pd.read_csv(io.StringIO(csv_content))
        csv_data[table_name] = df
        print(f"      ✅ {len(df)} rows, {len(df.columns)} columns")
    
    print(f"✅ All CSV files loaded")
    
except Exception as e:
    print(f"❌ Failed to read from GCS: {e}")
    sys.exit(1)

print()

# Step 2: Create BigQuery dataset
print("Step 2/3: Setting up BigQuery dataset...")
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
    sys.exit(1)

print()

# Step 3: Load each CSV to BigQuery
print("Step 3/3: Loading CSV data to BigQuery...")
print("-" * 70)

for table_name, df in csv_data.items():
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    print(f"Loading → {table_name}...")
    
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
        print(f"   ❌ Failed to load {table_name}: {e}")

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

