"""
Set up Dataplex data profiling for BigQuery tables
This enables automated data quality checks and profiling
Automatically detects GCP project from gcloud config
"""
from google.cloud import dataplex_v1, bigquery
import sys
import os

# Auto-detect GCP project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detect_gcp_project import get_active_gcp_project

# Configuration
PROJECT_ID = get_active_gcp_project() or os.getenv("GCP_PROJECT", "hackathon-practice-480508")
DATASET_ID = os.getenv("DATASET", "dev_dataset")
LOCATION = os.getenv("REGION", "us-central1")  # Dataplex location

print(f"🔍 Auto-detected GCP project: {PROJECT_ID}")
print(f"📊 Dataset: {DATASET_ID}")
print(f"🌍 Location: {LOCATION}")
print()

# Tables to profile
TABLES = ["week1", "week2", "week3", "week4"]

def setup_dataplex_profiling():
    """Set up Dataplex data profiling scans for all tables"""
    
    print("🔍 Setting up Dataplex data profiling...")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Tables: {TABLES}")
    print()
    
    try:
        # Initialize clients
        dataplex_client = dataplex_v1.DataScanServiceClient()
        bq_client = bigquery.Client(project=PROJECT_ID)
        print("✅ Connected to Dataplex and BigQuery")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        print("   Ensure google-cloud-dataplex is installed:")
        print("   pip install google-cloud-dataplex")
        sys.exit(1)
    
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    
    # Create profile scan for each table
    for table_name in TABLES:
        print(f"📊 Setting up profile scan for: {table_name}")
        
        try:
            # Check table exists
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
            table = bq_client.get_table(table_ref)
            print(f"   → Table found: {table.num_rows} rows")
            
            scan_id = f"profile_{table_name}"
            
            # Create DataProfileSpec
            data_profile_spec = dataplex_v1.DataProfileSpec(
                sampling_percent=100.0,  # Profile all data
                row_filter=""  # No filter
            )
            
            # Create DataSource pointing to BigQuery table
            data_source = dataplex_v1.DataSource(
                resource=f"//bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/{DATASET_ID}/tables/{table_name}"
            )
            
            # Create DataScan
            data_scan = dataplex_v1.DataScan(
                data=data_source,
                data_profile_spec=data_profile_spec,
                description=f"Automated data quality profiling for {table_name}",
                labels={"team": "megalodon", "hackathon": "2025"}
            )
            
            # Check if scan already exists
            try:
                existing_scan = dataplex_client.get_data_scan(
                    name=f"{parent}/dataScans/{scan_id}"
                )
                print(f"   → Scan already exists: {scan_id}")
                
                # Run the scan
                print(f"   → Running profile scan...")
                run_request = dataplex_v1.RunDataScanRequest(
                    name=existing_scan.name
                )
                job_response = dataplex_client.run_data_scan(request=run_request)
                print(f"   ✅ Scan job started: {job_response.job.name}")
                
            except Exception:
                # Create new scan
                create_request = dataplex_v1.CreateDataScanRequest(
                    parent=parent,
                    data_scan=data_scan,
                    data_scan_id=scan_id
                )
                
                print(f"   → Creating new scan: {scan_id}")
                operation = dataplex_client.create_data_scan(request=create_request)
                response = operation.result()  # Wait for completion
                print(f"   ✅ Created scan: {response.name}")
                
                # Run the scan
                print(f"   → Running initial profile scan...")
                run_request = dataplex_v1.RunDataScanRequest(name=response.name)
                job_response = dataplex_client.run_data_scan(request=run_request)
                print(f"   ✅ Scan job started: {job_response.job.name}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Failed to setup scan for {table_name}: {e}")
            print()
    
    print("=" * 60)
    print("🎉 Dataplex profiling setup complete!")
    print()
    print("📋 Next steps:")
    print("1. Wait 2-5 minutes for profile scans to complete")
    print("2. View results in GCP Console:")
    print(f"   https://console.cloud.google.com/dataplex/process/data-scans?project={PROJECT_ID}")
    print()
    print("3. The Identifier agent will now use Dataplex profiles to:")
    print("   - Auto-generate data quality rules")
    print("   - Detect missing values, outliers, format issues")
    print("   - Calculate completeness scores")
    print()
    print("4. Start testing:")
    print("   python run_backend.py")
    print("   streamlit run frontend/app.py")

if __name__ == "__main__":
    setup_dataplex_profiling()

