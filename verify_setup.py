"""
Verification script to check GCP project detection and BigQuery setup
Run this to see what project/dataset will be used
"""
import sys
import os

print("=" * 70)
print("🔍 AgentX Setup Verification")
print("=" * 70)
print()

# 1. Check GCP Authentication
print("1️⃣  Checking GCP Authentication...")
print("-" * 70)
try:
    from google.auth import default
    credentials, project = default()
    if project:
        print(f"✅ Authenticated to GCP")
        print(f"   Account: {credentials.service_account_email if hasattr(credentials, 'service_account_email') else 'User account'}")
        print(f"   Project detected: {project}")
    else:
        print("❌ No GCP project detected from authentication")
        print("   Run: gcloud auth application-default login")
except Exception as e:
    print(f"❌ Not authenticated to GCP: {e}")
    print("   Run: gcloud auth application-default login")
print()

# 2. Check Project Detection
print("2️⃣  Checking Project Auto-Detection...")
print("-" * 70)
try:
    from detect_gcp_project import get_active_gcp_project
    detected_project = get_active_gcp_project()
    if detected_project:
        print(f"✅ Project will be used: {detected_project}")
    else:
        print("❌ Could not detect project")
except Exception as e:
    print(f"❌ Error detecting project: {e}")
print()

# 3. Check Config
print("3️⃣  Checking Configuration...")
print("-" * 70)
try:
    from config_loader import CONFIG
    print(f"✅ Config loaded from: {CONFIG.get('__source__', 'unknown')}")
    print(f"   Project ID: {CONFIG.get('project_id', 'NOT SET')}")
    print(f"   Dataset: {CONFIG.get('dataset', 'NOT SET')}")
    print(f"   Tables:")
    print(f"      - week1: {CONFIG['project_id']}.{CONFIG['dataset']}.week1")
    print(f"      - week2: {CONFIG['project_id']}.{CONFIG['dataset']}.week2")
    print(f"      - week3: {CONFIG['project_id']}.{CONFIG['dataset']}.week3")
    print(f"      - week4: {CONFIG['project_id']}.{CONFIG['dataset']}.week4")
except Exception as e:
    print(f"❌ Error loading config: {e}")
print()

# 4. Check BigQuery Connection
print("4️⃣  Checking BigQuery Connection...")
print("-" * 70)
try:
    from google.cloud import bigquery
    from config_loader import CONFIG
    
    client = bigquery.Client(project=CONFIG['project_id'])
    print(f"✅ Connected to BigQuery")
    print(f"   Project: {client.project}")
    
    # Try to list datasets
    datasets = list(client.list_datasets())
    if datasets:
        print(f"   Datasets in this project:")
        for dataset in datasets[:5]:  # Show first 5
            print(f"      - {dataset.dataset_id}")
    else:
        print(f"   No datasets found (yet)")
    
except Exception as e:
    print(f"❌ Cannot connect to BigQuery: {e}")
    print("   Make sure you're authenticated: gcloud auth application-default login")
print()

# 5. Check if data tables exist
print("5️⃣  Checking Data Tables...")
print("-" * 70)
try:
    from google.cloud import bigquery
    from config_loader import CONFIG
    
    client = bigquery.Client(project=CONFIG['project_id'])
    dataset_id = CONFIG['dataset']
    
    try:
        dataset = client.get_dataset(f"{CONFIG['project_id']}.{dataset_id}")
        print(f"✅ Dataset exists: {dataset_id}")
        
        # Check for week tables
        tables_to_check = ['week1', 'week2', 'week3', 'week4', 'rules', 'issues']
        existing_tables = []
        missing_tables = []
        
        for table_name in tables_to_check:
            try:
                table = client.get_table(f"{CONFIG['project_id']}.{dataset_id}.{table_name}")
                existing_tables.append(f"{table_name} ({table.num_rows} rows)")
            except Exception:
                missing_tables.append(table_name)
        
        if existing_tables:
            print(f"   ✅ Existing tables:")
            for t in existing_tables:
                print(f"      - {t}")
        
        if missing_tables:
            print(f"   ⚠️  Missing tables (need to run setup):")
            for t in missing_tables:
                print(f"      - {t}")
        
    except Exception:
        print(f"❌ Dataset '{dataset_id}' does not exist yet")
        print(f"   Run: python setup_bigquery_dataplex.py")
    
except Exception as e:
    print(f"❌ Error checking tables: {e}")
print()

# 6. Check Excel file
print("6️⃣  Checking Source Data...")
print("-" * 70)
excel_file = "actualdata/1.1 Improving IP& Data Quality_BaNCs Synthetic Data - DQM AI Use Case.xlsx"
if os.path.exists(excel_file):
    import pandas as pd
    try:
        xls = pd.ExcelFile(excel_file)
        print(f"✅ Excel file found: {excel_file}")
        print(f"   Sheets: {', '.join(xls.sheet_names)}")
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            print(f"      - {sheet}: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"⚠️  Excel file found but cannot read: {e}")
else:
    print(f"❌ Excel file not found: {excel_file}")
print()

# 7. Summary
print("=" * 70)
print("📋 SUMMARY")
print("=" * 70)

try:
    from detect_gcp_project import get_active_gcp_project
    from config_loader import CONFIG
    
    project = get_active_gcp_project()
    
    if project:
        print(f"✅ READY TO USE")
        print()
        print(f"   Your setup:")
        print(f"   • GCP Project: {project}")
        print(f"   • Dataset: {CONFIG['dataset']}")
        print(f"   • Tables will be: {project}.{CONFIG['dataset']}.week1-4")
        print()
        
        # Check if setup is needed
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=project)
            dataset = client.get_dataset(f"{project}.{CONFIG['dataset']}")
            table = client.get_table(f"{project}.{CONFIG['dataset']}.week1")
            
            print(f"   Status: ✅ Data already loaded ({table.num_rows} rows in week1)")
            print()
            print(f"   Next steps:")
            print(f"   1. python run_backend.py")
            print(f"   2. streamlit run frontend/app.py")
            
        except Exception:
            print(f"   Status: ⚠️  Data not loaded yet")
            print()
            print(f"   Next step:")
            print(f"   1. python setup_bigquery_dataplex.py")
    else:
        print(f"❌ NOT READY")
        print()
        print(f"   Please authenticate first:")
        print(f"   1. gcloud auth application-default login")
        print(f"   2. python verify_setup.py  (run this again)")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 70)

