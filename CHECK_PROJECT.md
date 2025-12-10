# Quick Project Verification Commands

## 🚀 One-Command Check

Run this to verify everything:

```powershell
python verify_setup.py
```

This shows:
- ✅ What GCP project is detected
- ✅ What dataset will be used
- ✅ Which tables exist (if any)
- ✅ Authentication status
- ✅ Next steps

---

## 📋 Individual Commands

### 1. Check Active GCP Project

```powershell
# Method 1: Using our detection script
python -c "from detect_gcp_project import get_active_gcp_project; print('Project:', get_active_gcp_project())"

# Method 2: Using gcloud (if available)
gcloud config get-value project

# Method 3: Check ADC
python -c "from google.auth import default; creds, proj = default(); print('Project:', proj)"
```

**Expected Output:**
```
✅ Detected GCP project from authenticated session (ADC): hackathon-practice-480508
Project: hackathon-practice-480508
```

---

### 2. Check What Tables Will Be Used

```powershell
python -c "from config_loader import CONFIG; print('Project:', CONFIG['project_id']); print('Dataset:', CONFIG['dataset']); print('Week1 table:', CONFIG['project_id'] + '.' + CONFIG['dataset'] + '.week1')"
```

**Expected Output:**
```
✅ Auto-detected GCP project: hackathon-practice-480508
Project: hackathon-practice-480508
Dataset: dev_dataset
Week1 table: hackathon-practice-480508.dev_dataset.week1
```

---

### 3. Check If Dataset Exists

```powershell
bq ls <your-project-id>:dev_dataset

# Or auto-detect project:
python -c "from config_loader import CONFIG; import os; os.system(f'bq ls {CONFIG[\"project_id\"]}:dev_dataset')"
```

**If exists, shows:**
```
        tableId         Type
 -------------------- -------
  week1                TABLE
  week2                TABLE
  week3                TABLE
  week4                TABLE
  rules                TABLE
  issues               TABLE
```

**If not exists:**
```
BigQuery error in ls operation: Not found: Dataset <project>:dev_dataset
```
→ Need to run: `python setup_bigquery_dataplex.py`

---

### 4. Check Row Counts

```powershell
# Check week1 data
bq query --use_legacy_sql=false "SELECT COUNT(*) as row_count FROM \`<project-id>.dev_dataset.week1\`"

# Or with auto-detect:
python -c "from config_loader import CONFIG; import os; os.system(f'bq query --use_legacy_sql=false \"SELECT COUNT(*) FROM \`{CONFIG[\"project_id\"]}.{CONFIG[\"dataset\"]}.week1\`\"')"
```

**Expected Output:**
```
+-------------+
| row_count   |
+-------------+
|         100 |
+-------------+
```

---

### 5. View Sample Data

```powershell
# View first 5 rows
bq query --use_legacy_sql=false "SELECT CUS_ID, CUS_FORNAME, CUS_SURNAME, CUS_DOB FROM \`<project-id>.dev_dataset.week1\` LIMIT 5"

# Or with auto-detect:
python -c "from config_loader import CONFIG; import os; query = f'SELECT CUS_ID, CUS_FORNAME, CUS_SURNAME, CUS_DOB FROM \`{CONFIG[\"project_id\"]}.{CONFIG[\"dataset\"]}.week1\` LIMIT 5'; os.system(f'bq query --use_legacy_sql=false \"{query}\"')"
```

---

### 6. Check Authentication Status

```powershell
# Check who is logged in
gcloud auth list

# Check ADC
gcloud auth application-default print-access-token
```

**Expected Output:**
```
           Credentialed Accounts
ACTIVE  ACCOUNT
*       your-email@example.com

To set the active account, run:
    $ gcloud config set account `ACCOUNT`
```

---

### 7. Check All Projects You Have Access To

```powershell
gcloud projects list
```

**Shows all projects you can access:**
```
PROJECT_ID                NAME                    PROJECT_NUMBER
hackathon-practice-480508 Hackathon Practice     123456789
another-project-123       Another Project        987654321
```

---

## 🔄 Quick Status Check (Copy-Paste)

```powershell
Write-Output "=== GCP PROJECT CHECK ==="; `
python -c "from detect_gcp_project import get_active_gcp_project; print('Detected Project:', get_active_gcp_project())"; `
Write-Output ""; `
Write-Output "=== CONFIG CHECK ==="; `
python -c "from config_loader import CONFIG; print('Config Project:', CONFIG['project_id']); print('Dataset:', CONFIG['dataset'])"; `
Write-Output ""; `
Write-Output "=== TABLES CHECK ==="; `
python -c "from config_loader import CONFIG; import os; os.system(f'bq ls {CONFIG[\"project_id\"]}:{CONFIG[\"dataset\"]} 2>&1')"
```

---

## 📖 What Your Friend Should See

### Before Setup:
```powershell
python verify_setup.py
```

**Output:**
```
🔍 AgentX Setup Verification
======================================================================

1️⃣  Checking GCP Authentication...
✅ Authenticated to GCP
   Project detected: their-project-789

2️⃣  Checking Project Auto-Detection...
✅ Detected GCP project from authenticated session (ADC): their-project-789
✅ Project will be used: their-project-789

3️⃣  Checking Configuration...
✅ Config loaded from: C:\...\config.json
   Project ID: their-project-789
   Dataset: dev_dataset
   Tables:
      - week1: their-project-789.dev_dataset.week1
      - week2: their-project-789.dev_dataset.week2
      - week3: their-project-789.dev_dataset.week3
      - week4: their-project-789.dev_dataset.week4

5️⃣  Checking Data Tables...
❌ Dataset 'dev_dataset' does not exist yet
   Run: python setup_bigquery_dataplex.py

📋 SUMMARY
======================================================================
✅ READY TO USE

   Your setup:
   • GCP Project: their-project-789
   • Dataset: dev_dataset
   • Tables will be: their-project-789.dev_dataset.week1-4

   Status: ⚠️  Data not loaded yet

   Next step:
   1. python setup_bigquery_dataplex.py
```

### After Setup:
```powershell
python verify_setup.py
```

**Output:**
```
5️⃣  Checking Data Tables...
✅ Dataset exists: dev_dataset
   ✅ Existing tables:
      - week1 (100 rows)
      - week2 (100 rows)
      - week3 (100 rows)
      - week4 (100 rows)
      - rules (0 rows)
      - issues (0 rows)

📋 SUMMARY
======================================================================
✅ READY TO USE

   Your setup:
   • GCP Project: their-project-789
   • Dataset: dev_dataset
   • Tables will be: their-project-789.dev_dataset.week1-4

   Status: ✅ Data already loaded (100 rows in week1)

   Next steps:
   1. python run_backend.py
   2. streamlit run frontend/app.py
```

---

## 🎯 Summary for Your Friend

**Before doing anything:**
```powershell
# 1. Check what project will be used
python verify_setup.py
```

**If they see their correct project:**
```powershell
# 2. Run setup
python setup_bigquery_dataplex.py

# 3. Verify again
python verify_setup.py

# 4. Start application
python run_backend.py
streamlit run frontend/app.py
```

**If wrong project detected:**
```powershell
# Set correct project
gcloud config set project their-correct-project-id
gcloud auth application-default login

# Verify again
python verify_setup.py
```

---

## 🔍 Debugging Commands

### Check what's in ADC:
```powershell
python -c "from google.auth import default; import google.auth; creds, proj = default(); print('Quota Project:', creds.quota_project_id if hasattr(creds, 'quota_project_id') else 'None'); print('Project:', proj)"
```

### Force refresh ADC:
```powershell
gcloud auth application-default login --project=your-project-id
```

### Check environment variables:
```powershell
Write-Output "GCP_PROJECT: $env:GCP_PROJECT"
Write-Output "GOOGLE_CLOUD_PROJECT: $env:GOOGLE_CLOUD_PROJECT"  
Write-Output "PROJECT_ID: $env:PROJECT_ID"
```

### List all BigQuery datasets:
```powershell
python -c "from google.cloud import bigquery; from config_loader import CONFIG; client = bigquery.Client(project=CONFIG['project_id']); print('Datasets:'); [print(f'  - {d.dataset_id}') for d in client.list_datasets()]"
```

