# Direct BigQuery + Dataplex Setup

## The Correct Approach (As Per Problem Statement)

The data should be:
1. Uploaded directly to BigQuery (no local CSV files)
2. Profiled using Dataplex
3. Queried by the agents from BigQuery
4. Dataplex provides automated data quality rules

## Step 1: Upload Excel → BigQuery

```powershell
# Make sure you're authenticated
gcloud auth application-default login

# Run the upload script
python tools\upload_excel_to_bigquery.py
```

This will:
- Read the Excel file
- Upload Week1, Week2, Week3, Week4 directly to BigQuery
- Create tables: `hackathon-practice-480508.dev_dataset.week1-4`
- **NO local CSV files created**

## Step 2: Set Up Dataplex Profiling

```powershell
python tools\setup_dataplex.py
```

This will:
- Create Dataplex Data Profile scans for each table
- Run initial profiling
- Enable automated data quality checks

**Dataplex provides:**
- Column statistics (null ratio, min/max, mean, stddev)
- Data type validation
- Completeness scores
- Anomaly detection baselines

## Step 3: How the Agents Use It

### Identifier Agent (`agent/identifier.py`)
```python
# Uses Dataplex integration
from agent.dataplex_integration import dataplex

# Get profile-based rules
rules = dataplex.suggest_rules_from_profile("week1")

# Get data quality score
dq_score = dataplex.calculate_dq_score_from_profile("week1")

# Query BigQuery for issues
from agent.tools import run_bq_query
issues = run_bq_query(PROJECT, "SELECT * FROM week1 WHERE CUS_DOB IS NULL")
```

### Treatment Agent (`agent/treatment.py`)
```python
# Analyzes issues from Identifier
# Queries BigQuery for patterns
# Suggests root causes and treatments
```

### Remediator Agent (`agent/remediator.py`)
```python
# Applies fixes back to BigQuery
# Creates audit trail
# No local file manipulation
```

## Step 4: Verify Setup

```powershell
# Check tables exist
bq ls hackathon-practice-480508:dev_dataset

# Query week1
bq query "SELECT COUNT(*) FROM \`hackathon-practice-480508.dev_dataset.week1\`"

# Check Dataplex scans (wait 2-5 min after setup)
# Visit: https://console.cloud.google.com/dataplex/process/data-scans?project=hackathon-practice-480508
```

## Step 5: Test the System

```powershell
# Terminal 1: Backend
python run_backend.py

# Terminal 2: Frontend  
streamlit run frontend\app.py
```

Open http://localhost:8501 and:
1. Select "dev_dataset.week1"
2. Click "Run Identifier"
3. Should see issues detected using Dataplex profile + BigQuery queries

## What's Different from Before

### ❌ Old (Wrong) Approach:
- Excel → CSV files → Upload to BigQuery
- CSV files stored locally in `data_csv/`
- Agents read from local CSV as fallback

### ✅ New (Correct) Approach:
- Excel → **Direct** BigQuery upload
- **No local CSV files**
- Dataplex profiles the BigQuery tables
- Agents query BigQuery + use Dataplex profiles
- Everything cloud-native

## Architecture Flow

```
Excel File
    ↓
BigQuery Tables (week1-4)
    ↓
Dataplex Profiling
    ├→ Column statistics
    ├→ Null ratios
    ├→ Value distributions
    └→ Automated DQ rules
    ↓
Identifier Agent
    ├→ Uses Dataplex profiles
    ├→ Queries BigQuery
    ├→ Generates custom rules (NL→SQL)
    └→ Detects issues
    ↓
Treatment Agent
    └→ Analyzes patterns in BigQuery
    ↓
Remediator Agent
    └→ Fixes data in BigQuery
```

## Files to Delete (Local CSV Cleanup)

After confirming BigQuery upload works:
```powershell
# Remove local CSV files
Remove-Item -Recurse -Force data_csv\

# Remove old scripts
Remove-Item tools\setup_actual_data.ps1
Remove-Item tools\xlsx_to_csv.py
```

## Key Benefits

1. **Dataplex Integration**: Automated profiling and rule generation
2. **BigQuery Native**: All queries run in BigQuery (scalable)
3. **No Local Files**: Cloud-native, production-ready
4. **Identifier on Top of Dataplex**: As per problem statement - Identifier sits on top of Dataplex to enable business users to create custom rules via NL

## Troubleshooting

**"Dataplex not available"**:
```powershell
pip install google-cloud-dataplex
```

**"Permission denied"**:
```powershell
gcloud auth application-default login
```

**"Table not found"**:
- Re-run: `python tools\upload_excel_to_bigquery.py`

## Expected Results

After setup:
- 4 BigQuery tables with ~100 rows each
- 4 Dataplex profile scans running
- Identifier agent detects:
  - Missing DOB (~15-20 records)
  - Missing Postcodes
  - Negative payments
  - Outlier payments (via Dataplex statistics)
  - Invalid dates

