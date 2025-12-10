# Setup Guide for GCS Bucket Data

## 📋 Configuration

**Your friend's setup:**
- **Project**: `prod-12-313`
- **Dataset**: `12-313`
- **GCS Bucket**: `gs://prod-45-hackathon-bucket`
- **Excel File**: `1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx`

## ✅ Step-by-Step Setup

### Step 1: Verify Access to GCS Bucket

Your friend should run this first:

```powershell
python verify_gcs_setup.py
```

**Expected Output:**
```
🔍 GCS Data Verification
======================================================================

1️⃣  Checking GCP Authentication...
✅ Authenticated to GCP
   Detected project: prod-12-313

2️⃣  Checking GCS Bucket Access...
✅ Connected to GCS with project: prod-12-313
✅ Bucket found: prod-45-hackathon-bucket
   Location: us
   Created: 2025-XX-XX

3️⃣  Checking Excel File in Bucket...
✅ Excel file found: 1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx
   Size: X.XX MB
   Full path: gs://prod-45-hackathon-bucket/1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx

4️⃣  Downloading and Verifying Excel Structure...
✅ Downloaded successfully
✅ Excel file valid
   Sheets: Week1, Week2, Week3, Week4
      - Week1: 100 rows, 27 columns
      - Week2: 100 rows, 27 columns
      - Week3: 100 rows, 27 columns
      - Week4: 100 rows, 27 columns

📋 SUMMARY
======================================================================
✅ GCS Bucket Verification Complete

Configuration:
   • Project: prod-12-313
   • Dataset: 12-313
   • GCS Bucket: gs://prod-45-hackathon-bucket
   • Excel File: 1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx

Data will be loaded to:
   • prod-12-313.12-313.week1
   • prod-12-313.12-313.week2
   • prod-12-313.12-313.week3
   • prod-12-313.12-313.week4

Status: ⚠️  Data not loaded yet

Next step:
   python load_from_gcs.py
```

### Step 2: Load Data from GCS to BigQuery

Once verification passes, run:

```powershell
python load_from_gcs.py
```

**This will:**
1. Download Excel from GCS bucket
2. Read all 4 sheets (Week1-4)
3. Create BigQuery dataset `12-313`
4. Load each sheet as a table
5. Create auxiliary tables (rules, issues, users, audit_log)

**Expected Output:**
```
🚀 Loading Data from GCS to BigQuery
======================================================================

Configuration:
   Project: prod-12-313
   Dataset: 12-313
   Source: gs://prod-45-hackathon-bucket/1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx

Step 1/4: Downloading Excel from GCS...
✅ Downloaded to: /tmp/xxx.xlsx

Step 2/4: Reading Excel sheets...
✅ Found 4 sheets: ['Week1', 'Week2', 'Week3', 'Week4']
   - Week1: 100 rows, 27 columns
   - Week2: 100 rows, 27 columns
   - Week3: 100 rows, 27 columns
   - Week4: 100 rows, 27 columns

Step 3/4: Setting up BigQuery dataset...
✅ Created dataset: 12-313

Step 4/4: Loading sheets to BigQuery...
Loading Week1 → week1...
   ✅ Loaded 100 rows to week1
Loading Week2 → week2...
   ✅ Loaded 100 rows to week2
Loading Week3 → week3...
   ✅ Loaded 100 rows to week3
Loading Week4 → week4...
   ✅ Loaded 100 rows to week4

Creating auxiliary tables...
✅ rules table ready
✅ issues table ready
✅ users table ready
✅ audit_log table ready

======================================================================
✅ LOAD COMPLETE!
======================================================================

Tables created in prod-12-313.12-313:
   • week1: 100 rows
   • week2: 100 rows
   • week3: 100 rows
   • week4: 100 rows
   • rules: 0 rows
   • issues: 0 rows
   • users: 0 rows
   • audit_log: 0 rows

Next steps:
   1. Update config files with project: prod-12-313, dataset: 12-313
   2. python run_backend.py
   3. streamlit run frontend/app.py
```

### Step 3: Start the Application

```powershell
# Terminal 1: Backend
python run_backend.py

# Terminal 2: Frontend
streamlit run frontend/app.py
```

## 🔍 Verification Commands

### Check GCS Bucket Access
```powershell
gsutil ls gs://prod-45-hackathon-bucket/
```

### Check if Excel File Exists
```powershell
gsutil ls "gs://prod-45-hackathon-bucket/1.1 Improving IP& Data Quality/"
```

### Download File Manually (for testing)
```powershell
gsutil cp "gs://prod-45-hackathon-bucket/1.1 Improving IP& Data Quality/BaNCs Synthetic Data - DQM AI Use Case.xlsx" .
```

### Check BigQuery Tables After Load
```powershell
bq ls prod-12-313:12-313
```

### Query Sample Data
```powershell
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`prod-12-313.12-313.week1\`"
```

## 🐛 Troubleshooting

### Error: "does not have storage.buckets.get access"

**Problem**: No access to GCS bucket

**Solution**: Your friend needs to:
1. Make sure they're authenticated to the correct project:
   ```powershell
   gcloud auth application-default login --project=prod-12-313
   ```

2. Verify they have access:
   ```powershell
   gsutil ls gs://prod-45-hackathon-bucket/
   ```

3. If no access, they need these roles in project `prod-12-313`:
   - Storage Object Viewer (to read from bucket)
   - BigQuery Data Editor (to write to BigQuery)
   - BigQuery Job User (to run queries)

### Error: "Bucket not found"

**Check bucket name:**
```powershell
gsutil ls
```

This lists all buckets they have access to.

### Error: "File not found in bucket"

**List files in bucket:**
```powershell
gsutil ls -r gs://prod-45-hackathon-bucket/
```

This shows all files and their paths.

### Error: "Dataset name contains invalid characters"

BigQuery dataset names can contain hyphens. The dataset `12-313` is valid.

To check:
```powershell
bq ls prod-12-313:
```

## 📝 For Your Friend

**Quick Commands:**

```powershell
# 1. Verify access and check data
python verify_gcs_setup.py

# 2. If verification passes, load data
python load_from_gcs.py

# 3. Verify tables created
bq ls prod-12-313:12-313

# 4. Start application
python run_backend.py              # Terminal 1
streamlit run frontend/app.py       # Terminal 2
```

## 🔐 Required Permissions

Your friend needs these permissions in project `prod-12-313`:

1. **GCS Permissions:**
   - `storage.buckets.get`
   - `storage.objects.get`
   - `storage.objects.list`

2. **BigQuery Permissions:**
   - `bigquery.datasets.create`
   - `bigquery.datasets.get`
   - `bigquery.tables.create`
   - `bigquery.tables.updateData`
   - `bigquery.jobs.create`

**Standard Roles that include these:**
- Storage Object Viewer
- BigQuery Data Editor
- BigQuery Job User

## ✅ Success Criteria

The setup is successful when:

1. ✅ `python verify_gcs_setup.py` shows all checks passing
2. ✅ `python load_from_gcs.py` loads all 4 weeks
3. ✅ `bq ls prod-12-313:12-313` shows 8 tables (week1-4, rules, issues, users, audit_log)
4. ✅ Backend and frontend start without errors
5. ✅ Can select `12-313.week1` in frontend and run identifier

## 🔄 If Friend Shares Access with You

If your friend gives you access to the bucket, you can test with:

```powershell
# Set project
gcloud config set project prod-12-313
gcloud auth application-default login

# Verify access
python verify_gcs_setup.py

# Load data
python load_from_gcs.py
```

## 📂 File Structure After Setup

```
BigQuery:
prod-12-313
└── 12-313 (dataset)
    ├── week1 (100 rows)
    ├── week2 (100 rows)
    ├── week3 (100 rows)
    ├── week4 (100 rows)
    ├── rules (empty)
    ├── issues (empty)
    ├── users (empty)
    └── audit_log (empty)

GCS:
gs://prod-45-hackathon-bucket/
└── 1.1 Improving IP& Data Quality/
    └── BaNCs Synthetic Data - DQM AI Use Case.xlsx
```

