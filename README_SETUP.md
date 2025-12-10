# AgentX Setup - BigQuery + Dataplex Integration

## 🎯 Quick Setup (3 Commands)

```powershell
# 1. Authenticate to GCP
gcloud auth application-default login

# 2. Run complete setup
python setup_bigquery_dataplex.py

# 3. Start the application
python run_backend.py              # Terminal 1
streamlit run frontend/app.py       # Terminal 2
```

That's it! Your data is in BigQuery, Dataplex is profiling it, and agents are ready.

---

## 📚 What This Does

### ✅ Correct Architecture (As Per Problem Statement)

```
Excel File
    ↓
Direct Upload to BigQuery
    ↓
Dataplex Profiling (Automated)
    ├→ Column statistics
    ├→ Null ratios & completeness
    ├→ Value distributions
    └→ Auto-generated DQ rules
    ↓
Identifier Agent (sits on top of Dataplex)
    ├→ Uses Dataplex profiles
    ├→ Queries BigQuery
    ├→ Enables business users to create custom rules via NL
    └→ Detects data quality issues
    ↓
Treatment Agent
    └→ Analyzes patterns in BigQuery
    ↓
Remediator Agent
    └→ Fixes data in BigQuery
```

### ❌ What We DON'T Do

- ❌ Store CSV files locally
- ❌ Read from local files
- ❌ Have hardcoded test data
- ❌ Use file-based fallbacks

### ✅ What We DO

- ✅ Upload directly to BigQuery (cloud-native)
- ✅ Use Dataplex for automated profiling
- ✅ Agents query BigQuery only
- ✅ Identifier sits on top of Dataplex (as per problem statement)
- ✅ Production-ready architecture

---

## 📊 Data Overview

**Source**: `actualdata/1.1 Improving IP& Data Quality_BaNCs Synthetic Data - DQM AI Use Case.xlsx`

**Tables Created in BigQuery**:
- `week1` - ~100 records (Week 1 snapshot)
- `week2` - ~100 records (Week 2 snapshot)
- `week3` - ~100 records (Week 3 snapshot)
- `week4` - ~100 records (Week 4 snapshot)

**System Tables**:
- `rules` - Data quality rules
- `issues` - Detected issues
- `users` - User management (RBAC)
- `audit_log` - Action tracking

**Schema** (27 fields per record):
- Customer: `CUS_ID`, `CUS_FORNAME`, `CUS_SURNAME`, `CUS_DOB`, `CUS_NI_NO`, `CUS_POSTCODE`
- Life Status: `CUS_LIFE_STATUS`, `CUS_DEATH_DATE`, `CUS_SMOKER_STAT`
- Scheme: `SCM_MEMBER_STATUS`, `SCH_SCHEME_TYP`, `SCH_RENEWAL_DT`
- Payments: `POLI_GROSS_PMT`, `POLI_TAX_PMT`, `UNT_TRAN_AMT`
- ... and more

---

## 🐛 Known Data Quality Issues (Planted for Testing)

1. **Missing DOB** (~15-20 records): `CUS_DOB` is NULL
2. **Missing Postcode** (several records): `CUS_POSTCODE` is empty
3. **Invalid Dates**: "31/11/1997", "30/02/2007" (impossible dates)
4. **Deceased with Active Policies**: `CUS_LIFE_STATUS='DEC'` but `SCM_MEMBER_STATUS='Active'`
5. **Negative Payments**: Some `POLI_GROSS_PMT < 0`
6. **Payment Outliers**: Detected via Dataplex Z-score statistics

---

## 🔍 How Dataplex Integration Works

### Identifier Agent Uses Dataplex

```python
from agent.dataplex_integration import dataplex

# 1. Get automated rule suggestions from Dataplex profile
rules = dataplex.suggest_rules_from_profile("week1")
# Returns:
# - Completeness rules (high null ratios)
# - Accuracy rules (outliers via IQR)
# - Validity rules (string length anomalies)

# 2. Get data quality scores
dq_score = dataplex.calculate_dq_score_from_profile("week1")
# Returns:
# - Completeness score
# - Consistency score
# - Overall DQ score

# 3. Query BigQuery for actual issues
from agent.tools import run_bq_query
issues = run_bq_query(PROJECT, "SELECT * FROM week1 WHERE CUS_DOB IS NULL")
```

### Benefits of Dataplex Integration

1. **Automated Profiling**: Dataplex scans data and provides statistics
2. **Rule Generation**: Identifier generates rules based on profile insights
3. **Business User Friendly**: NL → SQL on top of Dataplex profiles
4. **Scalable**: Works with any BigQuery table size
5. **Production Ready**: Google-managed service

---

## 🧪 Testing the Setup

### 1. Verify Tables Exist

```powershell
bq ls hackathon-practice-480508:dev_dataset
```

Expected output:
```
week1
week2
week3
week4
rules
issues
users
audit_log
```

### 2. Check Data

```powershell
bq query "SELECT COUNT(*) as count FROM \`hackathon-practice-480508.dev_dataset.week1\`"
```

Expected: ~100 rows

### 3. View Dataplex Profiles

Visit: https://console.cloud.google.com/dataplex/process/data-scans?project=hackathon-practice-480508

You should see:
- `profile_week1`
- `profile_week2`
- `profile_week3`
- `profile_week4`

Wait 2-5 minutes for first profiles to complete.

### 4. Test Identifier Agent

1. Open frontend: http://localhost:8501
2. Select "dev_dataset.week1"
3. Click "Run Identifier"
4. Should detect ~15-20 customers with missing DOB

### 5. Test NL → SQL with Dataplex

In frontend, go to "NL → SQL" section:
- Enter: "Find customers with missing date of birth"
- Click "Generate SQL"
- Should generate: `SELECT CUS_ID, CUS_FORNAME, CUS_SURNAME, CUS_DOB FROM week1 WHERE CUS_DOB IS NULL`

---

## 🔧 Troubleshooting

### "Permission denied"
```powershell
gcloud auth application-default login
```

### "Dataplex not available"
```powershell
pip install google-cloud-dataplex
```

### "Table not found"
Re-run setup:
```powershell
python setup_bigquery_dataplex.py
```

### "No Dataplex profiles"
Wait 2-5 minutes after setup, then check:
https://console.cloud.google.com/dataplex/process/data-scans?project=hackathon-practice-480508

---

## 📁 Project Structure (After Setup)

```
agent0/
├── actualdata/
│   └── 1.1 Improving...xlsx          # Source data (stays here)
├── agent/
│   ├── identifier.py                  # Uses Dataplex + BigQuery
│   ├── treatment.py                   # Analyzes BigQuery patterns
│   ├── remediator.py                  # Fixes BigQuery data
│   └── dataplex_integration.py        # Dataplex client
├── backend/
│   └── main.py                        # FastAPI with BQ + Dataplex endpoints
├── frontend/
│   └── app.py                         # Streamlit UI
├── tools/
│   ├── upload_excel_to_bigquery.py    # Direct Excel → BQ
│   └── setup_dataplex.py              # Dataplex profiling setup
├── setup_bigquery_dataplex.py         # ⭐ ONE-COMMAND SETUP
├── DIRECT_BQ_SETUP.md                 # Detailed guide
└── README_SETUP.md                    # This file
```

---

## 🎓 Key Differences from Wrong Approach

| Aspect | ❌ Wrong | ✅ Correct |
|--------|---------|-----------|
| **Data Storage** | Local CSV files | BigQuery tables |
| **Agent Queries** | Read CSV files | Query BigQuery |
| **DQ Rules** | Hardcoded in code | Dataplex profiles + NL→SQL |
| **Architecture** | File-based | Cloud-native |
| **Scalability** | Limited to local files | Unlimited (BigQuery) |
| **Identifier Role** | Standalone agent | Sits on top of Dataplex |

---

## 🚀 Next Steps After Setup

1. ✅ Data in BigQuery
2. ✅ Dataplex profiling
3. ✅ Agents configured
4. **TODO**: Run end-to-end test
5. **TODO**: Generate rules for all 4 weeks
6. **TODO**: Track DQ improvement across weeks
7. **TODO**: Prepare hackathon demo

---

## 📞 Quick Reference

- **BigQuery Console**: https://console.cloud.google.com/bigquery?project=hackathon-practice-480508
- **Dataplex Console**: https://console.cloud.google.com/dataplex?project=hackathon-practice-480508
- **Frontend**: http://localhost:8501 (after starting)
- **Backend API**: http://localhost:8080 (after starting)

---

**Ready? Run:** `python setup_bigquery_dataplex.py` 🚀

