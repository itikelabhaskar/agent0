"""
Complete setup: Upload Excel to BigQuery + Configure Dataplex
Run this ONE script to set up everything
Automatically detects GCP project from gcloud config
"""
import subprocess
import sys
import os

# Auto-detect and configure GCP project first
from detect_gcp_project import ensure_project_configured

print("=" * 70)
print("🚀 AgentX BigQuery + Dataplex Setup")
print("=" * 70)
print()

print("Step 0: Detecting GCP project...")
print("-" * 70)
PROJECT, DATASET = ensure_project_configured()

if not PROJECT:
    print("\n❌ Cannot proceed without GCP project configuration")
    print("   Run: gcloud config set project YOUR_PROJECT_ID")
    sys.exit(1)

print()

print("Step 1/3: Uploading Excel data to BigQuery...")
print("-" * 70)
result1 = subprocess.run([sys.executable, "tools/upload_excel_to_bigquery.py"])
if result1.returncode != 0:
    print("\n❌ Upload failed. Check errors above.")
    sys.exit(1)

print()
print("=" * 70)
print("Step 2/3: Setting up Dataplex profiling...")
print("-" * 70)
result2 = subprocess.run([sys.executable, "tools/setup_dataplex.py"])
if result2.returncode != 0:
    print("\n⚠️  Dataplex setup had issues, but continuing...")

print()
print("=" * 70)
print("Step 3/3: Creating auxiliary tables...")
print("-" * 70)

from google.cloud import bigquery

# Use auto-detected project
if not PROJECT or not DATASET:
    print("❌ Project detection failed")
    sys.exit(1)

try:
    client = bigquery.Client(project=PROJECT)
    
    # Rules table
    print("Creating rules table...")
    client.query(f"""
    CREATE TABLE IF NOT EXISTS `{PROJECT}.{DATASET}.rules` (
        rule_id STRING,
        created_by STRING,
        created_ts TIMESTAMP,
        rule_text STRING,
        sql_snippet STRING,
        active BOOL,
        source STRING
    )
    """).result()
    print("✅ rules table ready")
    
    # Issues table
    print("Creating issues table...")
    client.query(f"""
    CREATE TABLE IF NOT EXISTS `{PROJECT}.{DATASET}.issues` (
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
    """).result()
    print("✅ issues table ready")
    
    # Users table
    print("Creating users table...")
    client.query(f"""
    CREATE TABLE IF NOT EXISTS `{PROJECT}.{DATASET}.users` (
        user_id STRING,
        email STRING,
        full_name STRING,
        role STRING,
        created_ts TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOL
    )
    """).result()
    print("✅ users table ready")
    
    # Audit log table
    print("Creating audit_log table...")
    client.query(f"""
    CREATE TABLE IF NOT EXISTS `{PROJECT}.{DATASET}.audit_log` (
        audit_id STRING,
        user_email STRING,
        action_type STRING,
        action_target STRING,
        action_details STRING,
        timestamp TIMESTAMP,
        status STRING
    )
    """).result()
    print("✅ audit_log table ready")
    
    print()
    print("✅ All auxiliary tables created")
    
except Exception as e:
    print(f"❌ Failed to create auxiliary tables: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("🎉 SETUP COMPLETE!")
print("=" * 70)
print()
print("📊 Your data is now in BigQuery:")
print("   - week1, week2, week3, week4 (pension data)")
print("   - rules, issues, users, audit_log (system tables)")
print()
print("🔍 Dataplex is profiling your data:")
print(f"   https://console.cloud.google.com/dataplex/process/data-scans?project={PROJECT}")
print("   (Wait 2-5 minutes for profiles to complete)")
print()
print("🤖 Your agents are configured to use:")
print("   1. BigQuery for data queries")
print("   2. Dataplex for automated profiling & DQ rules")
print("   3. No local files - 100% cloud-native")
print()
print("▶️  Next: Start the application:")
print("   Terminal 1: python run_backend.py")
print("   Terminal 2: streamlit run frontend/app.py")
print()
print("📖 See DIRECT_BQ_SETUP.md for more details")
print("=" * 70)

