# AgentX Setup Guide

## 📋 Configuration

- **Project**: `prod-12-335`
- **Dataset**: `dev_dataset`
- **GCS Bucket**: `gs://prod-45-hackathon-bucket`
- **Data Folder**: `1.1 Improving IP& Data Quality/`
- **CSV Files**: `sbox-Week1.csv`, `sbox-Week2.csv`, `sbox-Week3.csv`, `sbox-Week4.csv`

## 🚀 Quick Start (2 Steps)

### Step 1: Verify Access

```powershell
python verify_gcs_setup.py
```

**This checks:**
- ✅ GCP authentication
- ✅ Access to bucket `prod-45-hackathon-bucket`
- ✅ CSV files exist in folder
- ✅ CSV data is valid
- ✅ BigQuery dataset status

**Expected output:**
```
✅ Authenticated to GCP
   Project detected: prod-12-335

✅ Bucket found: prod-45-hackathon-bucket

✅ sbox-Week1.csv: 249.7 KB
✅ sbox-Week2.csv: 249.8 KB
✅ sbox-Week3.csv: 249.7 KB
✅ sbox-Week4.csv: 249.7 KB

✅ CSV valid: 100 rows, 27 columns

Configuration:
   • Project: prod-12-335
   • Dataset: dev_dataset
   • GCS Bucket: gs://prod-45-hackathon-bucket
   • CSV Files: sbox-Week1.csv, sbox-Week2.csv, sbox-Week3.csv, sbox-Week4.csv

Data will be loaded to:
   • prod-12-335.dev_dataset.week1
   • prod-12-335.dev_dataset.week2
   • prod-12-335.dev_dataset.week3
   • prod-12-335.dev_dataset.week4

Status: ⚠️  Data not loaded yet
Next step: python load_from_gcs.py
```

### Step 2: Load Data

```powershell
python load_from_gcs.py
```

**This will:**
1. Read CSV files from GCS
2. Create BigQuery dataset `dev_dataset`
3. Load data to tables: `week1`, `week2`, `week3`, `week4`
4. Create auxiliary tables: `rules`, `issues`, `users`, `audit_log`

**Expected output:**
```
🚀 Loading Data from GCS to BigQuery
======================================================================

Step 1/3: Reading CSV files from GCS...
   Reading sbox-Week1.csv...
      ✅ 100 rows, 27 columns
   Reading sbox-Week2.csv...
      ✅ 100 rows, 27 columns
   Reading sbox-Week3.csv...
      ✅ 100 rows, 27 columns
   Reading sbox-Week4.csv...
      ✅ 100 rows, 27 columns
✅ All CSV files loaded

Step 2/3: Setting up BigQuery dataset...
✅ Created dataset: dev_dataset

Step 3/3: Loading CSV data to BigQuery...
Loading → week1...
   ✅ Loaded 100 rows to week1
Loading → week2...
   ✅ Loaded 100 rows to week2
Loading → week3...
   ✅ Loaded 100 rows to week3
Loading → week4...
   ✅ Loaded 100 rows to week4

Creating auxiliary tables...
✅ rules table ready
✅ issues table ready
✅ users table ready
✅ audit_log table ready

======================================================================
✅ LOAD COMPLETE!
======================================================================

Tables created in prod-12-335.dev_dataset:
   • week1: 100 rows
   • week2: 100 rows
   • week3: 100 rows
   • week4: 100 rows
   • rules: 0 rows
   • issues: 0 rows
   • users: 0 rows
   • audit_log: 0 rows
```

### Step 3: Start Application

```powershell
# Terminal 1: Backend
python run_backend.py

# Terminal 2: Frontend
streamlit run frontend/app.py
```

Open: http://localhost:8501

---

## 🔍 Verification Commands

### Check bucket access:
```powershell
gsutil ls gs://prod-45-hackathon-bucket/
```

### Check CSV files:
```powershell
gsutil ls "gs://prod-45-hackathon-bucket/1.1 Improving IP& Data Quality/"
```

### Check BigQuery tables:
```powershell
bq ls prod-12-335:dev_dataset
```

### Query data:
```powershell
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`prod-12-335.dev_dataset.week1\`"
```

### Sample data:
```powershell
bq query --use_legacy_sql=false "SELECT CUS_ID, CUS_FORNAME, CUS_SURNAME, CUS_DOB FROM \`prod-12-335.dev_dataset.week1\` LIMIT 5"
```

---

## 🐛 Troubleshooting

### Error: "does not have storage.buckets.get access"

**Solution**: Authenticate to project with access:
```powershell
gcloud auth application-default login --project=prod-12-335
```

### Error: "File not found"

**Check files exist:**
```powershell
gsutil ls "gs://prod-45-hackathon-bucket/1.1 Improving IP& Data Quality/"
```

### Error: "Permission denied"

**Required roles:**
- Storage Object Viewer
- BigQuery Data Editor
- BigQuery Job User

---

## 📊 Data Schema

Each CSV file has **27 columns**:

**Customer Info:**
- CUS_ID, CUS_KEY_PARTY_ID, CUS_KEY_CUST_NO
- CUS_FORNAME, CUS_SURNAME, CUS_NI_NO
- CUS_DOB, CUS_SEX_CD, CUS_OCCUP_CD
- CUS_LIFE_STATUS, CUS_POSTCODE, CUS_SMOKER_STAT, CUS_DEATH_DATE

**Scheme Info:**
- CRL_KEY_POLICY_NO, SCM_PROJ_RET_DT, SCM_PROJ_RET_AGE
- SCM_SCH_LEAVE_DATE, SCM_MEMBER_STATUS
- SCH_SCHEME_TYP, SCH_RENEWAL_DT

**Payment Info:**
- POLID_FREQ, POLID_INCOME_TYPE, POLID_PAYMENT_DAY
- POLI_GROSS_PMT, POLI_TAX_PMT, POLI_INCOME_PMT
- UNT_TRAN_AMT

**~100 rows per week** = **~400 total records**

---

## ✅ Success Criteria

Setup is complete when:

1. ✅ `python verify_gcs_setup.py` passes all checks
2. ✅ `python load_from_gcs.py` loads 4 tables with 100 rows each
3. ✅ `bq ls prod-12-335:dev_dataset` shows 8 tables
4. ✅ Backend starts: `python run_backend.py`
5. ✅ Frontend loads: `streamlit run frontend/app.py`
6. ✅ Can select `dev_dataset.week1` and run identifier

---

## 📁 What Gets Created

```
BigQuery:
prod-12-335
└── dev_dataset
    ├── week1 (100 rows - sbox-Week1.csv)
    ├── week2 (100 rows - sbox-Week2.csv)
    ├── week3 (100 rows - sbox-Week3.csv)
    ├── week4 (100 rows - sbox-Week4.csv)
    ├── rules (system table)
    ├── issues (system table)
    ├── users (system table)
    └── audit_log (system table)

GCS (source data):
gs://prod-45-hackathon-bucket/
└── 1.1 Improving IP& Data Quality/
    ├── sbox-Week1.csv
    ├── sbox-Week2.csv
    ├── sbox-Week3.csv
    └── sbox-Week4.csv
```

---

## 🎯 Summary

**Two commands to get started:**
```powershell
python verify_gcs_setup.py    # Check access
python load_from_gcs.py         # Load data
```

**Then start the app:**
```powershell
python run_backend.py           # Terminal 1
streamlit run frontend/app.py   # Terminal 2
```

That's it! 🎉

