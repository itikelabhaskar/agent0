# AgentX - Quick Reference Guide

## 🚀 Quick Start Commands

### Start Local Development
```bash
# Backend
cd agentx
.\.venv\Scripts\Activate.ps1  # Windows
python run_backend.py

# Frontend (new terminal)
streamlit run frontend/app.py
```

### Deploy to Cloud Run
```bash
cd "C:\Users\mylil\AppData\Local\Google\Cloud SDK"
.\google-cloud-sdk\bin\gcloud.cmd run deploy agentx-backend \
  --project hackathon-practice-480508 \
  --source "C:\Users\mylil\Desktop\agentx" \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account agentx-backend-sa@hackathon-practice-480508.iam.gserviceaccount.com \
  --set-env-vars "PROJECT_ID=hackathon-practice-480508,DATASET=dev_dataset" \
  --max-instances=1 \
  --quiet
```

---

## 📡 API Endpoints Reference

### Core Features
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/` | GET | Health check | `curl https://agentx-backend-783063936000.us-central1.run.app/` |
| `/run-identifier` | POST | Detect DQ issues | `{"project":"...", "table":"..."}` |
| `/run-treatment` | POST | Get fix suggestions | `{"issue": {...}}` |
| `/apply-fix` | POST | Apply remediation | `{"fix": {...}, "apply_mode": "dryrun"}` |

### Rule Management
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/create-rule` | POST | Create rule | `{"created_by":"user", "rule_text":"...", "sql_snippet":"..."}` |
| `/list-rules` | GET | List all rules | - |
| `/run-rule` | POST | Execute rule | `{"rule_id":"abc", "limit":200}` |
| `/generate-rule-sql` | POST | NL→SQL | `{"nl_text":"Find missing DOB"}` |
| `/rule-versions/{id}` | GET | Get versions | - |
| `/rollback-rule` | POST | Rollback | `{"rule_id":"abc", "target_version":1}` |

### Issues & Anomalies
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/list-issues` | GET | List issues | `?limit=100` |
| `/run-anomaly` | GET | Detect anomalies | `?limit=20` |

### Governance
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/audit-trail` | GET | Get audit log | `?limit=50&action_type=create_rule` |
| `/user/{email}` | GET | Get user info | - |
| `/create-user` | POST | Create user | `{"email":"...", "full_name":"...", "role":"engineer"}` |
| `/check-permission` | POST | Check access | `{"user_email":"...", "required_role":"engineer"}` |

### Metrics & Trends
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/metrics` | GET | Current metrics | - |
| `/save-metrics-snapshot` | POST | Save snapshot | - |
| `/metrics-trend/{name}` | GET | Historical data | `?days=7` |

### Export
| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/export/issues` | GET | Export issues Excel | - |
| `/export/patches` | GET | Export patches Excel | - |
| `/export/audit` | GET | Export audit Excel | `?start_date=...&end_date=...` |

---

## 🗄️ Database Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `customers` | Source data | CUS_ID, CUS_DOB, CUS_FORNAME |
| `holdings` | Holdings data | customer_id, holding_amount |
| `rules` | Active rules | rule_id, sql_snippet, rule_text |
| `rules_history` | Version tracking | version_id, version_number |
| `issues` | Detected problems | issue_id, rule_id, match_json |
| `audit_log` | Action tracking | audit_id, user_email, action_type |
| `users` | User management | user_id, email, role |
| `metrics_history` | Trend data | metric_name, metric_value |
| `remediation_patches` | Applied fixes | patch_id, before_data, after_data |

---

## 🎨 Frontend UI Sections

### Main Tabs
1. **Run Identifier** - Detect issues
2. **Select Issue** - Choose for treatment
3. **Apply Fix** - Remediate with approval
4. **Rules Management** - CRUD operations
5. **NL→SQL Generator** - AI rule creation
6. **Run/Activate Rule** - Execute rules
7. **Issues Review** - Track findings
8. **Anomaly Detection** - Statistical analysis
9. **Metrics Dashboard** - KPI tracking

### Enhanced Tabs
1. **📜 Rule Versioning** - History and rollback
2. **📋 Audit Trail** - Activity logs
3. **👥 User Management** - RBAC controls
4. **📈 Trend Analytics** - Charts and visualizations
5. **📥 Export Data** - Download reports

---

## 👥 User Roles

| Role | Capabilities |
|------|--------------|
| **admin** | Everything: rules, users, rollback, audit |
| **engineer** | Technical: rules, fixes, metrics |
| **business_user** | Read-only: view issues, metrics, exports |

### Default Users
- **Admin**: mylilbeast1823@gmail.com (created by default)

---

## 🧪 Quick Tests

### Test Health
```bash
curl https://agentx-backend-783063936000.us-central1.run.app/
```

### Test Metrics
```powershell
$resp = Invoke-WebRequest -Uri "https://agentx-backend-783063936000.us-central1.run.app/metrics"
$resp.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

### Test Export
```powershell
Invoke-WebRequest -Uri "https://agentx-backend-783063936000.us-central1.run.app/export/issues" -OutFile "issues.xlsx"
```

### Test Audit Trail
```powershell
$resp = Invoke-WebRequest -Uri "https://agentx-backend-783063936000.us-central1.run.app/audit-trail?limit=10"
$resp.Content | ConvertFrom-Json
```

---

## 📊 BigQuery Queries

### Check Issues
```sql
SELECT rule_id, COUNT(*) as cnt, severity
FROM `hackathon-practice-480508.dev_dataset.issues`
GROUP BY rule_id, severity
ORDER BY cnt DESC
```

### Check Audit Log
```sql
SELECT user_email, action_type, COUNT(*) as actions
FROM `hackathon-practice-480508.dev_dataset.audit_log`
GROUP BY user_email, action_type
ORDER BY actions DESC
```

### Check Rule Versions
```sql
SELECT rule_id, version_number, created_by, change_reason
FROM `hackathon-practice-480508.dev_dataset.rules_history`
ORDER BY created_ts DESC
LIMIT 20
```

### Check Metrics History
```sql
SELECT metric_name, AVG(metric_value) as avg_value, COUNT(*) as snapshots
FROM `hackathon-practice-480508.dev_dataset.metrics_history`
GROUP BY metric_name
```

---

## 🔧 Troubleshooting

### Backend Issues
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agentx-backend" --project hackathon-practice-480508 --limit 50
```

### Local Dev Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check imports
python -c "from backend.enhancements import log_audit; print('✅ OK')"
```

### BigQuery Issues
```bash
# List tables
bq --project_id=hackathon-practice-480508 ls hackathon-practice-480508:dev_dataset

# Query test
bq query --use_legacy_sql=false --project_id=hackathon-practice-480508 "SELECT COUNT(*) FROM \`hackathon-practice-480508.dev_dataset.issues\`"
```

---

## 📦 Dependencies

```
fastapi
uvicorn[standard]
google-cloud-bigquery
google-cloud-aiplatform
google-generativeai
pandas
db-dtypes
streamlit
adk
requests
plotly
openpyxl
xlsxwriter
python-multipart
```

---

## 🔗 Important Links

- **Backend API**: https://agentx-backend-783063936000.us-central1.run.app
- **API Docs**: https://agentx-backend-783063936000.us-central1.run.app/docs
- **GitHub**: https://github.com/itikelabhaskar/agentx
- **GCP Console**: https://console.cloud.google.com/run?project=hackathon-practice-480508
- **BigQuery**: https://console.cloud.google.com/bigquery?project=hackathon-practice-480508

---

## 🎯 Demo Script (3 Minutes)

### 1. Problem (30s)
- Show sample data with missing DOB
- Explain data quality issues impact

### 2. Solution (90s)
- **Identifier**: Run on customers table → shows missing DOB
- **NL→SQL**: Type "Find customers with missing DOB" → generates SQL
- **Run Rule**: Execute rule → captures issues
- **Treatment**: Select issue → get 3 suggestions
- **Apply Fix**: Choose suggestion → apply with approval

### 3. Impact (60s)
- **Metrics**: Show completeness improved from 80% to 95%
- **Audit**: Display complete action trail
- **Export**: Download Excel report
- **Trend**: Show 7-day improvement chart

---

## 💡 Pro Tips

1. **Save metrics snapshots daily** for trend analysis
2. **Use dryrun mode first** before applying fixes
3. **Export audit trail regularly** for compliance
4. **Set up Cloud Scheduler** for automated monitoring
5. **Create business_user accounts** for stakeholders
6. **Rollback rules** if SQL has errors
7. **Use version numbers** for tracking changes

---

## 📈 Hackathon Pitch Points

1. **Multi-Agent Architecture** - 4 specialized agents
2. **AI-Powered** - NL→SQL generation
3. **Complete Governance** - Versioning, audit, RBAC
4. **Production-Ready** - Cloud Run deployment
5. **Compliance-Friendly** - Full audit trail
6. **Self-Service** - Business users can create rules
7. **Automated** - Scheduled monitoring
8. **Visual Analytics** - Interactive charts
9. **Enterprise Features** - Exports, trends, rollback
10. **Scalable** - BigQuery + Cloud native

---

*Last Updated: 2025-12-09*  
*Version: 2.0 (Enhanced Edition)*

