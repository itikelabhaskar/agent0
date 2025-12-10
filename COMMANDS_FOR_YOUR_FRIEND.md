# Commands for Your Friend to Verify Setup

## 🎯 Quick Verification (ONE COMMAND)

Tell your friend to run this:

```powershell
python verify_setup.py
```

## 📊 What They'll See

### ✅ If Everything is Detected Correctly:

```
======================================================================
🔍 AgentX Setup Verification
======================================================================

1️⃣  Checking GCP Authentication...
✅ Authenticated to GCP
   Account: User account
   Project detected: their-project-id

2️⃣  Checking Project Auto-Detection...
✅ Detected GCP project from authenticated session (ADC): their-project-id
✅ Project will be used: their-project-id

3️⃣  Checking Configuration...
✅ Config loaded from: C:\...\config.json
   Project ID: their-project-id
   Dataset: dev_dataset
   Tables:
      - week1: their-project-id.dev_dataset.week1
      - week2: their-project-id.dev_dataset.week2
      - week3: their-project-id.dev_dataset.week3
      - week4: their-project-id.dev_dataset.week4

4️⃣  Checking BigQuery Connection...
✅ Connected to BigQuery
   Project: their-project-id

5️⃣  Checking Data Tables...
❌ Dataset 'dev_dataset' does not exist yet
   Run: python setup_bigquery_dataplex.py

6️⃣  Checking Source Data...
✅ Excel file found
   Sheets: Week1, Week2, Week3, Week4
      - Week1: 100 rows, 27 columns
      - Week2: 100 rows, 27 columns
      - Week3: 100 rows, 27 columns
      - Week4: 100 rows, 27 columns

======================================================================
📋 SUMMARY
======================================================================
✅ READY TO USE

   Your setup:
   • GCP Project: their-project-id
   • Dataset: dev_dataset
   • Tables will be: their-project-id.dev_dataset.week1-4

   Status: ⚠️  Data not loaded yet

   Next step:
   1. python setup_bigquery_dataplex.py
======================================================================
```

**Key Things to Check:**
- ✅ Project detected should be THEIR project (not yours)
- ✅ All tables will use THEIR project
- ✅ Authentication working

### ❌ If Project Detection Fails:

```
❌ Not authenticated to GCP
   Run: gcloud auth application-default login
```

**Solution:**
```powershell
gcloud auth application-default login
python verify_setup.py  # Run again
```

---

## 🔍 Additional Verification Commands

### 1. Check Just the Project

```powershell
python -c "from detect_gcp_project import get_active_gcp_project; print('Project:', get_active_gcp_project())"
```

**Expected:**
```
✅ Detected GCP project from authenticated session (ADC): their-project-id
Project: their-project-id
```

### 2. Check What Tables Will Be Created

```powershell
python -c "from config_loader import CONFIG; print('Project:', CONFIG['project_id']); print('Dataset:', CONFIG['dataset']); print('Tables will be:'); [print(f'  - {CONFIG[chr(34)+chr(112)+chr(114)+chr(111)+chr(106)+chr(101)+chr(99)+chr(116)+chr(95)+chr(105)+chr(100)+chr(34)]}.{CONFIG[chr(34)+chr(100)+chr(97)+chr(116)+chr(97)+chr(115)+chr(101)+chr(116)+chr(34)]}.week{i}') for i in range(1,5)]"
```

### 3. List All Their GCP Projects

```powershell
gcloud projects list
```

**Shows all projects they have access to**

### 4. Check Current gcloud Project

```powershell
gcloud config get-value project
```

### 5. After Running Setup - Check Tables Exist

```powershell
python -c "from config_loader import CONFIG; import os; os.system(f'bq ls {CONFIG[chr(34)+chr(112)+chr(114)+chr(111)+chr(106)+chr(101)+chr(99)+chr(116)+chr(95)+chr(105)+chr(100)+chr(34)]}:{CONFIG[chr(34)+chr(100)+chr(97)+chr(116)+chr(97)+chr(115)+chr(101)+chr(116)+chr(34)]}')"
```

**Should show:**
```
        tableId         Type
 -------------------- -------
  week1                TABLE
  week2                TABLE
  week3                TABLE
  week4                TABLE
```

---

## 📋 Complete Workflow for Your Friend

### Step 1: Clone Repo
```powershell
git clone <repo-url>
cd agent0
```

### Step 2: Verify Setup (BEFORE running anything)
```powershell
python verify_setup.py
```

**Check:**
- ✅ Is the project detected THEIR project? (not yours)
- ✅ Is authentication working?

### Step 3: If Verification Passes, Run Setup
```powershell
python setup_bigquery_dataplex.py
```

**This will:**
- Upload Excel data to THEIR BigQuery project
- Create tables in THEIR project
- Set up Dataplex in THEIR project

### Step 4: Verify Again (AFTER setup)
```powershell
python verify_setup.py
```

**Should now show:**
```
5️⃣  Checking Data Tables...
✅ Dataset exists: dev_dataset
   ✅ Existing tables:
      - week1 (100 rows)
      - week2 (100 rows)
      - week3 (100 rows)
      - week4 (100 rows)
```

### Step 5: Start Application
```powershell
# Terminal 1
python run_backend.py

# Terminal 2
streamlit run frontend/app.py
```

---

## 🐛 Troubleshooting

### Problem: Wrong Project Detected

**Check what's detected:**
```powershell
python -c "from detect_gcp_project import get_active_gcp_project; print(get_active_gcp_project())"
```

**Solution 1: Re-authenticate**
```powershell
gcloud auth application-default login
```

**Solution 2: Set specific project**
```powershell
gcloud config set project correct-project-id
gcloud auth application-default login
```

**Solution 3: Use environment variable**
```powershell
$env:GCP_PROJECT = "correct-project-id"
python verify_setup.py
```

### Problem: Not Authenticated

**Error:**
```
❌ Not authenticated to GCP
```

**Solution:**
```powershell
gcloud auth application-default login
python verify_setup.py
```

### Problem: No Access to Project

**Error:**
```
❌ Cannot connect to BigQuery: 403 Permission denied
```

**Solution:**
- Make sure they have access to THEIR project
- They need these roles in THEIR project:
  - BigQuery Data Editor
  - BigQuery Job User
  - Storage Admin (for GCS)

---

## ✅ Success Indicators

Your friend's setup is correct when `python verify_setup.py` shows:

1. ✅ Project detected: **their-project-id** (not yours)
2. ✅ Authentication working
3. ✅ Config shows **their-project-id**
4. ✅ All tables use **their-project-id.dev_dataset.***
5. ✅ Excel file found with 4 sheets

**Then they can run:** `python setup_bigquery_dataplex.py`

---

## 📞 Quick Summary for Your Friend

**Copy this to your friend:**

```
Hey! To verify the setup works on your laptop:

1. Clone the repo
2. Run: python verify_setup.py
3. Check that it shows YOUR GCP project (not mine)
4. If yes, run: python setup_bigquery_dataplex.py
5. Run: python verify_setup.py (again)
6. Should show tables loaded
7. Start: python run_backend.py and streamlit run frontend/app.py

The verify_setup.py script will tell you exactly what project will be used
and whether everything is configured correctly!
```

