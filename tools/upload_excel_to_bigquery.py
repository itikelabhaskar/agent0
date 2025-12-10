"""
Upload Excel sheets directly to BigQuery
No local CSV files - direct upload using pandas and BigQuery client
Automatically detects GCP project from gcloud config
"""
import pandas as pd
from google.cloud import bigquery
import os
import sys

# Auto-detect GCP project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detect_gcp_project import get_active_gcp_project

# Configuration
PROJECT_ID = get_active_gcp_project() or os.getenv("GCP_PROJECT", "hackathon-practice-480508")
DATASET_ID = os.getenv("DATASET", "dev_dataset")
EXCEL_FILE = "actualdata/1.1 Improving IP& Data Quality_BaNCs Synthetic Data - DQM AI Use Case.xlsx"

print(f"🔍 Auto-detected GCP project: {PROJECT_ID}")
print(f"📊 Dataset: {DATASET_ID}")
print()

def upload_excel_to_bigquery():
    """Upload all sheets from Excel directly to BigQuery"""
    
    print("🚀 Starting Excel → BigQuery upload...")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Excel: {EXCEL_FILE}")
    print()
    
    # Check file exists
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ ERROR: Excel file not found: {EXCEL_FILE}")
        sys.exit(1)
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
    except Exception as e:
        print(f"❌ Failed to connect to BigQuery: {e}")
        print("   Run: gcloud auth application-default login")
        sys.exit(1)
    
    # Create dataset if not exists
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset exists: {DATASET_ID}")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "us"
        client.create_dataset(dataset)
        print(f"✅ Created dataset: {DATASET_ID}")
    
    print()
    
    # Read Excel file
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        sheets = xls.sheet_names
        print(f"📊 Found {len(sheets)} sheets: {sheets}")
        print()
    except Exception as e:
        print(f"❌ Failed to read Excel: {e}")
        sys.exit(1)
    
    # Upload each sheet
    for sheet_name in sheets:
        print(f"📤 Processing sheet: {sheet_name}")
        
        try:
            # Read sheet
            df = pd.read_excel(xls, sheet_name=sheet_name)
            print(f"   → Read {len(df)} rows, {len(df.columns)} columns")
            
            # Clean table name
            table_name = sheet_name.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
            table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
            
            # Configure load job
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace if exists
                autodetect=True  # Auto-detect schema
            )
            
            # Upload to BigQuery
            print(f"   → Uploading to {table_id}...")
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for completion
            
            # Verify
            table = client.get_table(table_id)
            print(f"   ✅ Uploaded {table.num_rows} rows to {table_name}")
            print()
            
        except Exception as e:
            print(f"   ❌ Failed to upload {sheet_name}: {e}")
            print()
    
    print("=" * 60)
    print("🎉 Upload complete!")
    print()
    print("Tables created:")
    tables = client.list_tables(dataset_ref)
    for table in tables:
        print(f"  - {table.table_id}")
    print()
    print("Next steps:")
    print("1. Set up Dataplex profiling: python tools/setup_dataplex.py")
    print("2. Start backend: python run_backend.py")
    print("3. Start frontend: streamlit run frontend/app.py")

if __name__ == "__main__":
    upload_excel_to_bigquery()

