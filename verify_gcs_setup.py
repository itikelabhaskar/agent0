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
EXPECTED_PROJECT = "prod-12-335"
EXPECTED_BUCKET = "prod-45-hackathon-bucket"
EXPECTED_FOLDER = "1.1 Improving IP& Data Quality/"
EXPECTED_CSV_FILES = ["sbox-Week1.csv", "sbox-Week2.csv", "sbox-Week3.csv", "sbox-Week4.csv"]
DATASET_ID = "dev_dataset"  # Dataset name in BigQuery

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

# 3. Check CSV Files in Bucket
print("3️⃣  Checking CSV Files in Bucket...")
print("-" * 70)
try:
    from google.cloud import storage
    
    client = storage.Client(project=EXPECTED_PROJECT)
    bucket = client.bucket(EXPECTED_BUCKET)
    
    all_found = True
    for csv_file in EXPECTED_CSV_FILES:
        file_path = EXPECTED_FOLDER + csv_file
        blob = bucket.blob(file_path)
        
        if blob.exists():
            print(f"✅ {csv_file}: {blob.size / 1024:.1f} KB")
        else:
            print(f"❌ {csv_file}: NOT FOUND")
            all_found = False
    
    if not all_found:
        print()
        print(f"   Files in folder '{EXPECTED_FOLDER}':")
        blobs = list(bucket.list_blobs(prefix=EXPECTED_FOLDER))
        for b in blobs:
            print(f"      - {b.name}")
        sys.exit(1)
    
    print(f"   Full path: gs://{EXPECTED_BUCKET}/{EXPECTED_FOLDER}")
        
except Exception as e:
    print(f"❌ Error checking files: {e}")
    sys.exit(1)
print()

# 4. Verify CSV Structure (sample one file)
print("4️⃣  Verifying CSV Structure...")
print("-" * 70)
try:
    import pandas as pd
    from google.cloud import storage
    import io
    
    client = storage.Client(project=EXPECTED_PROJECT)
    bucket = client.bucket(EXPECTED_BUCKET)
    
    # Sample the first CSV
    sample_file = EXPECTED_FOLDER + EXPECTED_CSV_FILES[0]
    blob = bucket.blob(sample_file)
    
    print(f"   Sampling: {EXPECTED_CSV_FILES[0]}")
    csv_data = blob.download_as_text()
    df = pd.read_csv(io.StringIO(csv_data))
    
    print(f"✅ CSV valid: {len(df)} rows, {len(df.columns)} columns")
    print(f"   Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
    
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
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
print(f"   • Folder: {EXPECTED_FOLDER}")
print(f"   • CSV Files: {', '.join(EXPECTED_CSV_FILES)}")
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

