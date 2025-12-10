# Multi-User / Multi-Project Setup Guide

## 🎯 Problem Solved

Your friend can pull this code and run it on **their own GCP project** without any manual configuration changes. The code automatically detects which GCP project is active.

## 🔍 How Auto-Detection Works

### Method 1: gcloud config (Primary)
```powershell
# Your laptop
gcloud config set project your-project-123

# Your friend's laptop
gcloud config set project their-project-456
```

The code automatically detects and uses the active project!

### Method 2: Environment Variable
```powershell
# Alternative if gcloud not available
$env:GCP_PROJECT = "your-project-id"
```

### Method 3: Application Default Credentials
The code can also detect project from ADC if available.

## 📋 Setup for Each User

### You (on your laptop):
```powershell
# 1. Set your GCP project
gcloud config set project hackathon-practice-480508
gcloud auth application-default login

# 2. Run setup (will use YOUR project automatically)
python setup_bigquery_dataplex.py

# 3. Start application
python run_backend.py
streamlit run frontend/app.py
```

### Your Friend (on their laptop):
```powershell
# 1. Clone the repo
git clone <repo-url>
cd agent0

# 2. Set THEIR GCP project
gcloud config set project their-project-789
gcloud auth application-default login

# 3. Run the SAME setup script (will use THEIR project automatically)
python setup_bigquery_dataplex.py

# 4. Start application (uses THEIR project automatically)
python run_backend.py
streamlit run frontend/app.py
```

## ✅ What Happens Automatically

### When You Run:
```
🔍 Auto-detected GCP project: hackathon-practice-480508
📊 Dataset: dev_dataset
✅ Uploading to hackathon-practice-480508.dev_dataset.week1
```

### When Your Friend Runs:
```
🔍 Auto-detected GCP project: their-project-789
📊 Dataset: dev_dataset
✅ Uploading to their-project-789.dev_dataset.week1
```

**Same code, different projects** - NO manual changes needed!

## 🔧 How It Works Internally

### 1. Config Files (config.json)
```json
{
  "project_id": "AUTO_DETECT",
  "dataset": "dev_dataset",
  "_comment": "AUTO_DETECT triggers automatic project detection"
}
```

### 2. Auto-Detection Logic (detect_gcp_project.py)
```python
# Tries these methods in order:
1. gcloud config get-value project     # Primary method
2. $env:GCP_PROJECT                    # Environment variable
3. Application Default Credentials     # ADC metadata
4. config.json (if manually set)       # Fallback
```

### 3. All Scripts Use Auto-Detection
- `tools/upload_excel_to_bigquery.py`
- `tools/setup_dataplex.py`
- `setup_bigquery_dataplex.py`
- `backend/main.py`
- `config_loader.py`

## 📊 Example: Multiple Team Members

### Scenario:
- **You**: Working on `hackathon-practice-480508`
- **Friend 1**: Working on `team-sandbox-001`
- **Friend 2**: Working on `dev-environment-xyz`

### Each Person:
```powershell
# Set their own project
gcloud config set project <their-project-id>

# Run setup (same commands for everyone)
python setup_bigquery_dataplex.py

# Tables created in THEIR project:
# <their-project-id>.dev_dataset.week1
# <their-project-id>.dev_dataset.week2
# <their-project-id>.dev_dataset.week3
# <their-project-id>.dev_dataset.week4
```

**Result**: Everyone has their own isolated environment!

## 🔒 What Gets Created Per User

### In YOUR GCP Project:
```
hackathon-practice-480508
└── dev_dataset
    ├── week1
    ├── week2
    ├── week3
    ├── week4
    ├── rules
    ├── issues
    └── users
```

### In YOUR FRIEND'S GCP Project:
```
their-project-789
└── dev_dataset
    ├── week1
    ├── week2
    ├── week3
    ├── week4
    ├── rules
    ├── issues
    └── users
```

**Completely isolated!** No conflicts, no shared resources.

## 🎓 Advanced: Override Project Manually

If someone wants to use a specific project (not their active gcloud project):

### Option 1: Environment Variable
```powershell
$env:GCP_PROJECT = "specific-project-id"
python setup_bigquery_dataplex.py
```

### Option 2: Edit config.json
```json
{
  "project_id": "specific-project-id",
  "dataset": "dev_dataset"
}
```

### Option 3: Command Line
```powershell
$env:PROJECT_ID = "specific-project-id"
python setup_bigquery_dataplex.py
```

## 🧪 Testing Auto-Detection

Run this to see what project will be used:

```powershell
python detect_gcp_project.py
```

Output:
```
🔍 GCP Project Auto-Detection
======================================================================

✅ Detected GCP project from gcloud: hackathon-practice-480508

======================================================================
✅ Configuration Complete!
======================================================================
   Project: hackathon-practice-480508
   Dataset: dev_dataset

The application will now use this GCP project automatically.

Your friend can run the same code on their laptop and it will
automatically detect THEIR GCP project from their gcloud config.
```

## ⚠️ Troubleshooting

### "Could not detect GCP project"

**Solution 1**: Set gcloud project
```powershell
gcloud config set project YOUR_PROJECT_ID
```

**Solution 2**: Set environment variable
```powershell
$env:GCP_PROJECT = "YOUR_PROJECT_ID"
```

**Solution 3**: Check authentication
```powershell
gcloud auth list
gcloud auth application-default login
```

### "Permission denied"

Each user needs access to THEIR OWN GCP project:
```powershell
# User should have these roles in their project:
- BigQuery Data Editor
- BigQuery Job User
- Dataplex Editor (optional)
```

### "Table already exists"

This is fine! The setup script uses `WRITE_TRUNCATE` which replaces existing tables.

## 📝 Summary

### ✅ What Works Automatically:
- Project detection from gcloud config
- Each user uses their own GCP project
- No code changes needed between users
- Complete environment isolation

### ❌ What Doesn't Work:
- ❌ Sharing the same BigQuery tables between users (by design - each has their own)
- ❌ Automatic cross-project queries (by design - security)

### 💡 Key Benefit:
**Your friend can:**
1. Clone the repo
2. Set their gcloud project: `gcloud config set project their-project`
3. Run `python setup_bigquery_dataplex.py`
4. Everything works in THEIR project automatically!

**No hardcoded project IDs anywhere!** 🎉

## 🔗 Related Files

- `detect_gcp_project.py` - Auto-detection logic
- `config_loader.py` - Config loading with auto-detection
- `tools/upload_excel_to_bigquery.py` - Uses auto-detection
- `tools/setup_dataplex.py` - Uses auto-detection
- `setup_bigquery_dataplex.py` - Main setup with auto-detection

All of these automatically detect and use the active GCP project.

