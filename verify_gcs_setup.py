"""
Verification script for GCS bucket data
Checks access to prod-45-hackathon-bucket and validates data
"""
import sys
import os

print("=" * 70)
print("🔍 GCS Data Verification")
print("=" * 70)
print()

# Expected configuration
EXPECTED_PROJECT = "prod-12-313"
EXPECTED_BUCKET = "prod-45-hackathon-bucket"
EXPECTED_FILE = "1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx"
DATASET_ID = "12-313"  # Dataset name in BigQuery

# 1. Check GCP Authentication
print("1️⃣  Checking GCP Authentication...")
print("-" * 70)
try:
    from google.auth import default
    credentials, detected_project = default()
    if detected_project:
        print(f"✅ Authenticated to GCP")
        print(f"   Detected project: {detected_project}")
        
        if detected_project != EXPECTED_PROJECT:
            print(f"   ⚠️  WARNING: Expected project '{EXPECTED_PROJECT}' but got '{detected_project}'")
            print(f"   → Will try to use: {EXPECTED_PROJECT}")
    else:
        print("❌ No GCP project detected from authentication")
        print("   Run: gcloud auth application-default login")
        sys.exit(1)
except Exception as e:
    print(f"❌ Not authenticated to GCP: {e}")
    print("   Run: gcloud auth application-default login")
    sys.exit(1)
print()

# 2. Check GCS Bucket Access
print("2️⃣  Checking GCS Bucket Access...")
print("-" * 70)
try:
    from google.cloud import storage
    
    # Try with expected project
    client = storage.Client(project=EXPECTED_PROJECT)
    print(f"✅ Connected to GCS with project: {EXPECTED_PROJECT}")
    
    # Check bucket exists
    try:
        bucket = client.get_bucket(EXPECTED_BUCKET)
        print(f"✅ Bucket found: {EXPECTED_BUCKET}")
        print(f"   Location: {bucket.location}")
        print(f"   Created: {bucket.time_created}")
    except Exception as e:
        print(f"❌ Cannot access bucket '{EXPECTED_BUCKET}': {e}")
        print(f"   Make sure:")
        print(f"   1. Bucket exists")
        print(f"   2. You have permission to access it")
        print(f"   3. Project '{EXPECTED_PROJECT}' is correct")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Cannot connect to GCS: {e}")
    sys.exit(1)
print()

# 3. Check Excel File in Bucket
print("3️⃣  Checking Excel File in Bucket...")
print("-" * 70)
try:
    from google.cloud import storage
    
    client = storage.Client(project=EXPECTED_PROJECT)
    bucket = client.bucket(EXPECTED_BUCKET)
    blob = bucket.blob(EXPECTED_FILE)
    
    if blob.exists():
        print(f"✅ Excel file found: {EXPECTED_FILE}")
        print(f"   Size: {blob.size / (1024*1024):.2f} MB")
        print(f"   Updated: {blob.updated}")
        print(f"   Full path: gs://{EXPECTED_BUCKET}/{EXPECTED_FILE}")
    else:
        print(f"❌ Excel file not found: {EXPECTED_FILE}")
        print(f"   Looking in: gs://{EXPECTED_BUCKET}/")
        print()
        print("   Files in bucket (first 20):")
        blobs = list(bucket.list_blobs(max_results=20))
        for b in blobs:
            print(f"      - {b.name}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error checking file: {e}")
    sys.exit(1)
print()

# 4. Download and Verify Excel Structure
print("4️⃣  Downloading and Verifying Excel Structure...")
print("-" * 70)
try:
    import pandas as pd
    from google.cloud import storage
    import tempfile
    
    client = storage.Client(project=EXPECTED_PROJECT)
    bucket = client.bucket(EXPECTED_BUCKET)
    blob = bucket.blob(EXPECTED_FILE)
    
    # Download to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        print(f"   Downloading to temp file...")
        blob.download_to_filename(tmp.name)
        tmp_path = tmp.name
    
    print(f"✅ Downloaded successfully")
    
    # Read Excel
    xls = pd.ExcelFile(tmp_path)
    print(f"✅ Excel file valid")
    print(f"   Sheets: {', '.join(xls.sheet_names)}")
    
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        print(f"      - {sheet}: {len(df)} rows, {len(df.columns)} columns")
    
    # Cleanup
    os.unlink(tmp_path)
    
except Exception as e:
    print(f"❌ Error reading Excel: {e}")
    sys.exit(1)
print()

# 5. Check BigQuery Dataset
print("5️⃣  Checking BigQuery Dataset...")
print("-" * 70)
try:
    from google.cloud import bigquery
    
    client = bigquery.Client(project=EXPECTED_PROJECT)
    dataset_id = f"{EXPECTED_PROJECT}.{DATASET_ID}"
    
    try:
        dataset = client.get_dataset(dataset_id)
        print(f"✅ Dataset exists: {DATASET_ID}")
        print(f"   Full path: {dataset_id}")
        print(f"   Location: {dataset.location}")
        
        # List tables
        tables = list(client.list_tables(dataset))
        if tables:
            print(f"   Existing tables:")
            for table in tables:
                t = client.get_table(table)
                print(f"      - {table.table_id} ({t.num_rows} rows)")
        else:
            print(f"   No tables yet (need to run setup)")
        
    except Exception:
        print(f"❌ Dataset '{DATASET_ID}' does not exist in project '{EXPECTED_PROJECT}'")
        print(f"   Will be created during setup")
    
except Exception as e:
    print(f"❌ Cannot connect to BigQuery: {e}")
print()

# 6. Summary
print("=" * 70)
print("📋 SUMMARY")
print("=" * 70)
print()
print(f"✅ GCS Bucket Verification Complete")
print()
print(f"Configuration:")
print(f"   • Project: {EXPECTED_PROJECT}")
print(f"   • Dataset: {DATASET_ID}")
print(f"   • GCS Bucket: gs://{EXPECTED_BUCKET}")
print(f"   • Excel File: {EXPECTED_FILE}")
print()
print(f"Data will be loaded to:")
print(f"   • {EXPECTED_PROJECT}.{DATASET_ID}.week1")
print(f"   • {EXPECTED_PROJECT}.{DATASET_ID}.week2")
print(f"   • {EXPECTED_PROJECT}.{DATASET_ID}.week3")
print(f"   • {EXPECTED_PROJECT}.{DATASET_ID}.week4")
print()

# Check if tables exist
try:
    from google.cloud import bigquery
    client = bigquery.Client(project=EXPECTED_PROJECT)
    dataset_id = f"{EXPECTED_PROJECT}.{DATASET_ID}"
    dataset = client.get_dataset(dataset_id)
    
    tables_exist = False
    for table_name in ['week1', 'week2', 'week3', 'week4']:
        try:
            table = client.get_table(f"{dataset_id}.{table_name}")
            tables_exist = True
            break
        except:
            pass
    
    if tables_exist:
        print(f"Status: ✅ Data already loaded")
        print()
        print(f"Next steps:")
        print(f"   1. python run_backend.py")
        print(f"   2. streamlit run frontend/app.py")
    else:
        print(f"Status: ⚠️  Data not loaded yet")
        print()
        print(f"Next step:")
        print(f"   python load_from_gcs.py")
except:
    print(f"Status: ⚠️  Dataset not created yet")
    print()
    print(f"Next step:")
    print(f"   python load_from_gcs.py")

print("=" * 70)

