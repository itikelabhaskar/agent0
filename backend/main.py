from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.agent_wrapper import run_identifier, suggest_treatments_for_missing_dob, apply_fix
from agent.tools import run_bq_query, run_bq_nonquery
from backend.enhancements import (
    log_audit, save_rule_version, get_rule_versions, rollback_rule,
    get_user_by_email, check_permission, save_metrics_snapshot,
    get_metrics_trend, export_issues_to_excel, export_remediation_patches,
    export_audit_trail
)
from agent.dataplex_integration import dataplex
from datetime import datetime
import uuid
import google.generativeai as genai
import os

# Load config for environment switching (dev/sandbox)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import CONFIG

PROJECT_ID = CONFIG["project_id"]
DATASET = CONFIG["dataset"]
RULES_TABLE = f"{PROJECT_ID}.{DATASET}.rules"
ISSUES_TABLE = f"{PROJECT_ID}.{DATASET}.issues"
CUSTOMERS_TABLE = f"{PROJECT_ID}.{DATASET}.customers"
HOLDINGS_TABLE = f"{PROJECT_ID}.{DATASET}.holdings"
USERS_TABLE = f"{PROJECT_ID}.{DATASET}.users"

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "service": "agentx-backend"}

@app.post("/run-identifier")
async def run_identifier_route(payload: dict):
    project = payload.get("project") or PROJECT_ID  # Use config if not provided
    table = payload.get("table")
    result = run_identifier(project, table)
    return {"result": result}

@app.post("/run-treatment")
async def run_treatment_route(payload: dict):
    """
    Get treatment suggestions for a specific data quality issue
    """
    issue = payload.get("issue", {})
    suggestions = suggest_treatments_for_missing_dob(issue)
    return {"result": {"status": "success", "suggestions": suggestions}}

@app.post("/apply-fix")
async def apply_fix_route(payload: dict):
    """
    Apply a selected remediation fix
    """
    result = apply_fix(payload)
    return {"result": result}


@app.post("/create-rule")
async def create_rule(payload: dict):
    """
    Create a new rule in BigQuery with versioning and audit logging
    payload: { "created_by": "name", "rule_text": "NL text or SQL", "sql_snippet": "optional SQL" }
    """
    created_by = payload.get("created_by", "anonymous")
    rule_text = payload.get("rule_text")
    sql_snippet = payload.get("sql_snippet") or ""  # allow NL only; we may generate SQL later

    if not rule_text:
        raise HTTPException(status_code=400, detail="rule_text required")

    rule_id = str(uuid.uuid4())[:8]
    
    # Escape special characters for SQL safety
    created_by_escaped = created_by.replace("'", "\\'")
    rule_text_escaped = rule_text.replace("'", "\\'").replace('"', '\\"')
    sql_snippet_escaped = sql_snippet.replace("'", "\\'").replace('"', '\\"')

    insert_sql = f"""
    INSERT INTO `{RULES_TABLE}`
    (rule_id, created_by, created_ts, rule_text, sql_snippet, active, source)
    VALUES(
        '{rule_id}', 
        '{created_by_escaped}', 
        CURRENT_TIMESTAMP(), 
        '''{rule_text_escaped}''', 
        '''{sql_snippet_escaped}''', 
        TRUE, 
        'ui'
    )
    """

    # run insert
    run_bq_nonquery(PROJECT_ID, insert_sql)
    
    # Save initial version
    save_rule_version(rule_id, sql_snippet, rule_text, created_by, "initial")
    
    # Log audit
    log_audit(created_by, "create_rule", rule_id, {"rule_text": rule_text, "sql_snippet": sql_snippet})
    
    return {"result": {"status": "success", "rule_id": rule_id}}


@app.get("/list-rules")
async def list_rules():
    """
    List all rules from BigQuery
    """
    q = f"SELECT rule_id, created_by, created_ts, rule_text, sql_snippet, active FROM `{RULES_TABLE}` ORDER BY created_ts DESC LIMIT 100"
    df = run_bq_query(PROJECT_ID, q)
    return {"result": {"status":"success", "rules": df.to_dict(orient="records")}}


@app.post("/run-rule-preview")
async def run_rule_preview(payload: dict):
    """
    Preview rule results by running SQL
    payload: { "sql": "<sql to run, SELECT ... LIMIT 100>"}
    """
    sql = payload.get("sql")
    if not sql:
        raise HTTPException(status_code=400, detail="sql required")

    # IMPORTANT: be careful with destructive SQL — only allow SELECT
    if not sql.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries allowed for preview")

    try:
        df = run_bq_query(PROJECT_ID, sql)
        return {"result": {"status":"success", "count": len(df), "preview": df.to_dict(orient="records")}}
    except Exception as e:
        error_msg = str(e)
        # Return a more helpful error message
        raise HTTPException(status_code=400, detail=f"SQL Error: {error_msg}")


def parse_nl_to_sql(nl_text: str, project: str) -> str:
    """
    Parse natural language to SQL using pattern matching and AI.
    This function handles common data quality queries intelligently.
    
    ACTUAL SCHEMA:
    - customers: customer_id, customer_name, date_of_birth, email, status
    - holdings: customer_id, fund_id, holding_amount, holding_date
    """
    nl_lower = nl_text.lower().strip()
    table_customers = f"`{project}.dev_dataset.customers`"
    table_holdings = f"`{project}.dev_dataset.holdings`"
    
    # Pattern matching for common data quality queries
    
    # DOB/Date of Birth related queries
    if any(word in nl_lower for word in ['dob', 'date of birth', 'birth', 'birthday']):
        if any(word in nl_lower for word in ['missing', 'null', 'empty', 'no ', 'without', "doesn't have", "doesnt have", "dont have", "don't have", 'not have', 'delete', 'remove', 'find']):
            return f"SELECT customer_id, customer_name, date_of_birth, email FROM {table_customers} WHERE date_of_birth IS NULL LIMIT 200"
        elif any(word in nl_lower for word in ['has', 'have', 'with', 'exist']):
            return f"SELECT customer_id, customer_name, date_of_birth, email FROM {table_customers} WHERE date_of_birth IS NOT NULL LIMIT 200"
        elif any(word in nl_lower for word in ['invalid', 'wrong', 'future', 'bad']):
            return f"SELECT customer_id, customer_name, date_of_birth FROM {table_customers} WHERE date_of_birth > CURRENT_DATE() OR date_of_birth < '1900-01-01' LIMIT 200"
    
    # Email-related queries
    if any(word in nl_lower for word in ['email', 'e-mail']):
        if any(word in nl_lower for word in ['missing', 'null', 'empty', 'no ', 'without', "doesn't have", "doesnt have"]):
            return f"SELECT customer_id, customer_name, email FROM {table_customers} WHERE email IS NULL OR email = '' LIMIT 200"
        elif any(word in nl_lower for word in ['invalid', 'wrong', 'bad', 'incorrect']):
            return f"SELECT customer_id, customer_name, email FROM {table_customers} WHERE email NOT LIKE '%@%.%' OR email IS NULL LIMIT 200"
        elif any(word in nl_lower for word in ['duplicate', 'dup', 'same']):
            return f"SELECT email, COUNT(*) as cnt FROM {table_customers} GROUP BY email HAVING COUNT(*) > 1 LIMIT 200"
    
    # Name-related queries
    if any(word in nl_lower for word in ['name', 'customer name']):
        if any(word in nl_lower for word in ['missing', 'null', 'empty', 'no ', 'without']):
            return f"SELECT customer_id, customer_name FROM {table_customers} WHERE customer_name IS NULL OR customer_name = '' LIMIT 200"
        elif any(word in nl_lower for word in ['duplicate', 'dup', 'same']):
            return f"SELECT customer_name, COUNT(*) as cnt FROM {table_customers} GROUP BY customer_name HAVING COUNT(*) > 1 LIMIT 200"
    
    # Status-related queries
    if 'status' in nl_lower:
        if any(word in nl_lower for word in ['inactive', 'not active']):
            return f"SELECT customer_id, customer_name, status FROM {table_customers} WHERE status = 'inactive' LIMIT 200"
        elif any(word in nl_lower for word in ['active']):
            return f"SELECT customer_id, customer_name, status FROM {table_customers} WHERE status = 'active' LIMIT 200"
        elif any(word in nl_lower for word in ['missing', 'null', 'empty']):
            return f"SELECT customer_id, customer_name, status FROM {table_customers} WHERE status IS NULL OR status = '' LIMIT 200"
    
    # Holdings/Amount-related queries
    if any(word in nl_lower for word in ['holding', 'amount', 'balance', 'payment', 'value', 'fund']):
        if any(word in nl_lower for word in ['negative', 'minus', 'less than zero', '< 0', '<0']):
            return f"SELECT customer_id, fund_id, holding_amount, holding_date FROM {table_holdings} WHERE holding_amount < 0 LIMIT 200"
        elif any(word in nl_lower for word in ['zero', '= 0', '=0', 'no value']):
            return f"SELECT customer_id, fund_id, holding_amount, holding_date FROM {table_holdings} WHERE holding_amount = 0 LIMIT 200"
        elif any(word in nl_lower for word in ['missing', 'null', 'empty']):
            return f"SELECT customer_id, fund_id, holding_amount, holding_date FROM {table_holdings} WHERE holding_amount IS NULL LIMIT 200"
        elif any(word in nl_lower for word in ['high', 'large', 'big', 'outlier', 'anomal']):
            return f"SELECT customer_id, fund_id, holding_amount, holding_date FROM {table_holdings} WHERE holding_amount > 100000 ORDER BY holding_amount DESC LIMIT 200"
    
    # Duplicate-related queries
    if any(word in nl_lower for word in ['duplicate', 'dup', 'same', 'repeated']):
        if 'customer' in nl_lower:
            return f"SELECT customer_name, COUNT(*) as cnt FROM {table_customers} GROUP BY customer_name HAVING COUNT(*) > 1 LIMIT 200"
        elif 'holding' in nl_lower or 'fund' in nl_lower:
            return f"SELECT customer_id, fund_id, COUNT(*) as cnt FROM {table_holdings} GROUP BY customer_id, fund_id HAVING COUNT(*) > 1 LIMIT 200"
    
    # All customers/holdings queries
    if 'all customer' in nl_lower or 'every customer' in nl_lower or 'list customer' in nl_lower or 'show customer' in nl_lower:
        return f"SELECT customer_id, customer_name, date_of_birth, email, status FROM {table_customers} LIMIT 200"
    
    if 'all holding' in nl_lower or 'every holding' in nl_lower or 'list holding' in nl_lower or 'show holding' in nl_lower:
        return f"SELECT customer_id, fund_id, holding_amount, holding_date FROM {table_holdings} LIMIT 200"
    
    # Default: if nothing matched, try to be smart about it
    # Check if it mentions customers or holdings
    if 'customer' in nl_lower:
        return f"SELECT customer_id, customer_name, date_of_birth, email, status FROM {table_customers} LIMIT 200"
    elif 'holding' in nl_lower or 'fund' in nl_lower:
        return f"SELECT customer_id, fund_id, holding_amount, holding_date FROM {table_holdings} LIMIT 200"
    
    # Ultimate fallback - customers with missing DOB (common DQ issue)
    return f"SELECT customer_id, customer_name, date_of_birth FROM {table_customers} WHERE date_of_birth IS NULL LIMIT 200"


def vertex_generate_sql(prompt, project_id, location="us-central1", model="gemini-1.5-flash", temperature=0.0, max_output_tokens=1024):
    """
    Generate SQL from NL using Vertex AI Generative AI (Gemini).
    Falls back to pattern matching if AI is not available.
    """
    try:
        # Try to get API key from environment
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        
        if api_key:
            genai.configure(api_key=api_key)
        # If no API key, it will try to use Application Default Credentials
        
        # Initialize the model - use gemini-1.5-flash for speed
        model_instance = genai.GenerativeModel(model_name=model)

        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        # Generate response
        response = model_instance.generate_content(
            prompt,
            generation_config=generation_config
        )

        if response and hasattr(response, 'text') and response.text:
            sql = response.text.strip()
            # Clean up any markdown formatting
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.startswith("```"):
                sql = sql[3:]
            if sql.endswith("```"):
                sql = sql[:-3]
            return sql.strip()
    except Exception as e:
        print(f"Vertex AI generation failed: {e}")
    
    # Fallback - return None to trigger pattern matching
    return None


@app.post("/generate-rule-sql")
async def generate_rule_sql(payload: dict):
    """
    Generate SQL from natural language with PENDING approval status
    payload:
      { "project": "<project>", "nl_text": "Find customers with missing DOB", "created_by": "user@email.com" }
    """
    project = payload.get("project", PROJECT_ID)
    nl_text = payload.get("nl_text", "")
    created_by = payload.get("created_by", "system")
    
    if not nl_text:
        raise HTTPException(status_code=400, detail="nl_text required")

    # First, try pattern matching (fast and reliable)
    sql_candidate = parse_nl_to_sql(nl_text, project)
    
    # If we want to try AI as well (optional - can be enabled with API key)
    ai_attempted = False
    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        prompt = f"""
You are an assistant that translates a plain English data quality request into a single safe BigQuery SELECT statement.

Rules:
- Return only a single SELECT statement (no DML, no CREATE, no UPDATE, no DELETE).
- The SELECT must return raw identifiers and the problematic column(s) and should include LIMIT 200.
- Use the EXACT table names: `{project}.dev_dataset.customers` (columns: CUS_ID, CUS_FORNAME, CUS_SURNAME, CUS_DOB, CUS_GENDER, CUS_EMAIL, CUS_PHONE, CUS_ADDRESS) and `{project}.dev_dataset.holdings` (columns: holding_id, customer_id, holding_amount)
- Do not include comments, explanations, or additional text — return only the SQL statement.

English request:
\"\"\"{nl_text}\"\"\"

SQL:
"""
        try:
            ai_sql = vertex_generate_sql(prompt, project_id=project, location="us-central1", model="gemini-1.5-flash", temperature=0.0)
            if ai_sql and ai_sql.lower().strip().startswith("select"):
                sql_candidate = ai_sql
                ai_attempted = True
        except Exception as e:
            print(f"AI SQL generation failed, using pattern matching: {e}")

    sql_candidate = sql_candidate.strip().strip('`').strip()

    # basic safety: only allow SELECT
    if not sql_candidate.lower().lstrip().startswith("select"):
        raise HTTPException(status_code=400, detail="Generated SQL not allowed (must be SELECT).")

    # Generate rule ID
    rule_id = str(uuid.uuid4())[:8]
    
    # Escape single quotes in text fields for SQL safety
    nl_text_escaped = nl_text.replace("'", "\\'").replace('"', '\\"')
    sql_candidate_escaped = sql_candidate.replace("'", "\\'").replace('"', '\\"')
    created_by_escaped = created_by.replace("'", "\\'")
    
    # Store in rules table with PENDING status (active=FALSE until approved)
    # Using triple quotes and proper escaping for BigQuery
    insert_sql = f"""
    INSERT INTO `{RULES_TABLE}`
    (rule_id, created_by, created_ts, rule_text, sql_snippet, active, source)
    VALUES(
        '{rule_id}', 
        '{created_by_escaped}', 
        CURRENT_TIMESTAMP(), 
        '''{nl_text_escaped}''', 
        '''{sql_candidate_escaped}''', 
        FALSE, 
        'nl_generated_pending'
    )
    """

    # run insert
    try:
        run_bq_nonquery(PROJECT_ID, insert_sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save rule: {e}")
    
    # Also store in knowledge bank with pending status
    from backend.knowledge_bank import kb
    kb.add_rule({
        "rule_id": rule_id,
        "rule_text": nl_text,
        "sql_snippet": sql_candidate,
        "created_by": created_by
    }, category="completeness", approval_status="pending")
    
    # Log audit
    from backend.enhancements import log_audit
    log_audit(created_by, "generate_rule", rule_id, {
        "nl_text": nl_text,
        "sql": sql_candidate,
        "status": "pending_approval"
    })

    return {
        "result": {
            "status": "success",
            "rule_id": rule_id,
            "sql": sql_candidate,
            "approval_status": "pending",
            "message": "Rule generated and awaiting approval"
        }
    }


@app.post("/approve-rule")
async def approve_rule(payload: dict):
    """
    Approve a pending rule
    payload: { "rule_id": "xxx", "approved_by": "user@email.com", "notes": "optional" }
    """
    rule_id = payload.get("rule_id")
    approved_by = payload.get("approved_by", "system")
    notes = payload.get("notes", "")
    
    if not rule_id:
        raise HTTPException(status_code=400, detail="rule_id required")
    
    # Update rule to active
    update_sql = f"""
    UPDATE `{RULES_TABLE}`
    SET active = TRUE, source = 'nl_generated_approved'
    WHERE rule_id = '{rule_id}'
    """
    
    try:
        run_bq_nonquery(PROJECT_ID, update_sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve rule: {e}")
    
    # Update knowledge bank
    from backend.knowledge_bank import kb
    kb.approve_rule(rule_id, approved_by)
    
    # Save version
    from backend.enhancements import save_rule_version
    # Get rule details
    rule_query = f"SELECT rule_text, sql_snippet FROM `{RULES_TABLE}` WHERE rule_id = '{rule_id}' LIMIT 1"
    df = run_bq_query(PROJECT_ID, rule_query)
    if not df.empty:
        save_rule_version(
            rule_id,
            df.iloc[0]['sql_snippet'],
            df.iloc[0]['rule_text'],
            approved_by,
            "approved_from_pending"
        )
    
    # Log audit
    from backend.enhancements import log_audit
    log_audit(approved_by, "approve_rule", rule_id, {"notes": notes})
    
    return {
        "result": {
            "status": "success",
            "rule_id": rule_id,
            "message": "Rule approved and activated"
        }
    }


@app.post("/reject-rule")
async def reject_rule(payload: dict):
    """
    Reject a pending rule
    payload: { "rule_id": "xxx", "rejected_by": "user@email.com", "reason": "required" }
    """
    rule_id = payload.get("rule_id")
    rejected_by = payload.get("rejected_by", "system")
    reason = payload.get("reason", "No reason provided")
    
    if not rule_id:
        raise HTTPException(status_code=400, detail="rule_id required")
    
    # Mark rule as inactive and update source
    update_sql = f"""
    UPDATE `{RULES_TABLE}`
    SET active = FALSE, source = 'nl_generated_rejected'
    WHERE rule_id = '{rule_id}'
    """
    
    try:
        run_bq_nonquery(PROJECT_ID, update_sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject rule: {e}")
    
    # Log audit
    from backend.enhancements import log_audit
    log_audit(rejected_by, "reject_rule", rule_id, {"reason": reason})
    
    return {
        "result": {
            "status": "success",
            "rule_id": rule_id,
            "message": "Rule rejected"
        }
    }


@app.get("/pending-rules")
async def get_pending_rules():
    """
    Get all rules pending approval
    """
    query = f"""
    SELECT rule_id, rule_text, sql_snippet, created_by, created_ts, source
    FROM `{RULES_TABLE}`
    WHERE active = FALSE AND source LIKE '%pending%'
    ORDER BY created_ts DESC
    """
    
    df = run_bq_query(PROJECT_ID, query)
    pending_rules = df.to_dict(orient="records")
    
    return {
        "result": {
            "status": "success",
            "count": len(pending_rules),
            "pending_rules": pending_rules
        }
    }


@app.post("/run-rule")
async def run_rule(payload: dict):
    """
    payload: { "rule_id": "<rule_id>", "limit": 200 }
    """
    rule_id = payload.get("rule_id")
    if not rule_id:
        raise HTTPException(status_code=400, detail="rule_id required")

    # fetch rule from BQ
    q_rule = f"SELECT rule_id, rule_text, sql_snippet FROM `{RULES_TABLE}` WHERE rule_id = '{rule_id}' LIMIT 1"
    df_rule = run_bq_query(PROJECT_ID, q_rule)
    if df_rule.empty:
        raise HTTPException(status_code=404, detail="rule not found")

    sql_snippet = df_rule.iloc[0]['sql_snippet']
    rule_text = df_rule.iloc[0]['rule_text']

    # Basic safety: only allow SELECT
    if not sql_snippet.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Rule SQL is not a SELECT")

    # Enforce a result limit
    limit = int(payload.get("limit", 200))
    # Try to append LIMIT if not present (simple approach)
    sql_to_run = sql_snippet
    if "limit" not in sql_snippet.lower():
        sql_to_run = f"{sql_snippet.rstrip(';')} LIMIT {limit}"

    # Execute query
    df_matches = run_bq_query(PROJECT_ID, sql_to_run)

    # Insert matches into issues table
    from google.cloud import bigquery
    import json
    client = bigquery.Client(project=PROJECT_ID)
    table_id = ISSUES_TABLE

    rows_to_insert = []
    for _, row in df_matches.iterrows():
        issue_id = str(uuid.uuid4())[:12]
        match_json = json.dumps(row.dropna().to_dict(), default=str)
        rows_to_insert.append({
            "issue_id": issue_id,
            "rule_id": rule_id,
            "rule_text": rule_text,
            "detected_ts": datetime.utcnow().isoformat(),
            "source_table": row.get("source_table", ""),
            "match_json": match_json,
            "reviewed": False,
            "severity": None,
            "note": None
        })

    if rows_to_insert:
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            raise HTTPException(status_code=500, detail=f"Failed to write issues: {errors}")

    return {"result": {"status": "success", "rule_id": rule_id, "inserted": len(rows_to_insert)}}


@app.get("/list-issues")
async def list_issues(limit: int = 200):
    """
    List all detected issues from the issues table
    """
    q = f"SELECT * FROM `{ISSUES_TABLE}` ORDER BY detected_ts DESC LIMIT {int(limit)}"
    df = run_bq_query(PROJECT_ID, q)
    issues = df.to_dict(orient="records")
    return {"result": {"status":"success", "issues": issues}}


@app.get("/run-anomaly")
async def run_anomaly(limit: int = 20):
    """
    Run anomaly detection using statistical methods (Z-score)
    """
    # Use Z-score based anomaly detection (simple but effective)
    sql = f"""
    WITH stats AS (
      SELECT
        AVG(holding_amount) AS mean_amount,
        STDDEV(holding_amount) AS stddev_amount
      FROM `{HOLDINGS_TABLE}`
      WHERE holding_amount IS NOT NULL
    ),
    scored AS (
      SELECT
        h.*,
        ABS((h.holding_amount - s.mean_amount) / NULLIF(s.stddev_amount, 0)) AS z_score
      FROM `{HOLDINGS_TABLE}` h
      CROSS JOIN stats s
      WHERE h.holding_amount IS NOT NULL
    )
    SELECT *,
      IF(z_score > 2.0, 'HIGH', IF(z_score > 1.5, 'MEDIUM', 'LOW')) AS anomaly_flag
    FROM scored
    WHERE z_score > 1.5
    ORDER BY z_score DESC
    LIMIT {limit}
    """

    df = run_bq_query(PROJECT_ID, sql)

    # Insert anomalies into issues table
    from google.cloud import bigquery
    import json
    client = bigquery.Client(project=PROJECT_ID)

    rows_to_insert = []
    for _, row in df.iterrows():
        anomaly_dict = row.dropna().to_dict()
        # Convert any special types to JSON-serializable format
        for key, val in anomaly_dict.items():
            if hasattr(val, 'isoformat'):
                anomaly_dict[key] = val.isoformat()
        
        anomaly_json = json.dumps(anomaly_dict, default=str)
        z_score = float(row.get("z_score", 0))
        
        rows_to_insert.append({
            "issue_id": str(uuid.uuid4())[:12],
            "rule_id": "ANOMALY_ZSCORE",
            "rule_text": "Statistical anomaly detection (Z-score)",
            "detected_ts": datetime.utcnow().isoformat(),
            "source_table": "holdings",
            "match_json": anomaly_json,
            "reviewed": False,
            "severity": "high" if z_score > 2.0 else "medium",
            "note": f"Z-score: {z_score:.2f}"
        })

    if rows_to_insert:
        errors = client.insert_rows_json(ISSUES_TABLE, rows_to_insert)
        if errors:
            raise HTTPException(status_code=500, detail=f"Failed to write anomalies: {errors}")

    return {
        "result": {
            "status": "success",
            "inserted": len(rows_to_insert),
            "top_anomalies": df.to_dict(orient="records")
        }
    }


@app.get("/metrics")
async def get_metrics():
    """
    Get data quality metrics and KPIs
    """
    metrics = {}

    # 1. DOB completeness
    q1 = f"""
    SELECT
      COUNT(*) AS total,
      COUNTIF(date_of_birth IS NULL) AS missing
    FROM `{CUSTOMERS_TABLE}`
    """
    df1 = run_bq_query(PROJECT_ID, q1)
    total = int(df1.iloc[0]["total"])
    missing = int(df1.iloc[0]["missing"])
    metrics["dob_completeness"] = float(1 - (missing / total)) if total > 0 else 0
    metrics["total_customers"] = total
    metrics["missing_dob_count"] = missing

    # 2. Issues count by rule
    q2 = f"""
    SELECT rule_id, COUNT(*) AS cnt, 
           COUNTIF(severity = 'high') AS high_severity,
           COUNTIF(reviewed = TRUE) AS reviewed_count
    FROM `{ISSUES_TABLE}`
    GROUP BY rule_id
    ORDER BY cnt DESC
    LIMIT 20
    """
    try:
        df2 = run_bq_query(PROJECT_ID, q2)
        metrics["issues_by_rule"] = df2.to_dict(orient="records")
        metrics["total_issues"] = int(df2["cnt"].sum())
    except Exception:
        metrics["issues_by_rule"] = []
        metrics["total_issues"] = 0

    # 3. Holdings statistics
    q3 = f"""
    SELECT
      COUNT(*) AS total_holdings,
      AVG(holding_amount) AS avg_amount,
      MIN(holding_amount) AS min_amount,
      MAX(holding_amount) AS max_amount
    FROM `{HOLDINGS_TABLE}`
    """
    df3 = run_bq_query(PROJECT_ID, q3)
    metrics["holdings_stats"] = df3.iloc[0].to_dict()

    return {"result": metrics}


# ============================================
# RULE VERSIONING & ROLLBACK ENDPOINTS
# ============================================

@app.get("/rule-versions/{rule_id}")
async def get_versions(rule_id: str):
    """
    Get all versions of a specific rule
    """
    try:
        versions = get_rule_versions(rule_id)
        return {"result": {"status": "success", "versions": versions}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rollback-rule")
async def rollback_rule_endpoint(payload: dict):
    """
    Rollback a rule to a previous version
    payload: { "rule_id": "xxx", "target_version": 2, "rollback_by": "user@email.com" }
    """
    rule_id = payload.get("rule_id")
    target_version = payload.get("target_version")
    rollback_by = payload.get("rollback_by", "system")
    
    if not rule_id or not target_version:
        raise HTTPException(status_code=400, detail="rule_id and target_version required")
    
    result = rollback_rule(rule_id, target_version, rollback_by)
    return {"result": result}


# ============================================
# AUDIT TRAIL ENDPOINTS
# ============================================

@app.get("/audit-trail")
async def get_audit_trail(limit: int = 100, action_type: str = None):
    """
    Get audit trail with optional filtering
    """
    where_clause = ""
    if action_type:
        where_clause = f"WHERE action_type = '{action_type}'"
    
    query = f"""
    SELECT audit_id, user_email, action_type, action_target, 
           action_details, timestamp, status
    FROM `{PROJECT_ID}.{DATASET}.audit_log`
    {where_clause}
    ORDER BY timestamp DESC
    LIMIT {limit}
    """
    
    df = run_bq_query(PROJECT_ID, query)
    audit_records = df.to_dict(orient="records")
    
    return {"result": {"status": "success", "records": audit_records, "count": len(audit_records)}}


# ============================================
# RBAC ENDPOINTS
# ============================================

@app.get("/user/{email}")
async def get_user(email: str):
    """
    Get user details and role
    """
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"result": user}


@app.post("/check-permission")
async def check_user_permission(payload: dict):
    """
    Check if user has required permission
    payload: { "user_email": "x@y.com", "required_role": "engineer" }
    """
    user_email = payload.get("user_email")
    required_role = payload.get("required_role", "business_user")
    
    user = get_user_by_email(user_email)
    if not user:
        return {"result": {"has_permission": False, "reason": "User not found"}}
    
    has_perm = check_permission(user['role'], required_role)
    return {"result": {"has_permission": has_perm, "user_role": user['role']}}


@app.post("/create-user")
async def create_user(payload: dict):
    """
    Create a new user (admin only)
    payload: { "email": "x@y.com", "full_name": "John Doe", "role": "business_user" }
    """
    email = payload.get("email")
    full_name = payload.get("full_name")
    role = payload.get("role", "business_user")
    
    if not email or not full_name:
        raise HTTPException(status_code=400, detail="email and full_name required")
    
    if role not in ["business_user", "engineer", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user_id = str(uuid.uuid4())[:12]
    
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)
    rows = [{
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "role": role,
        "created_ts": datetime.utcnow().isoformat(),
        "last_login": None,
        "is_active": True
    }]
    
    errors = client.insert_rows_json(USERS_TABLE, rows)
    
    if errors:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {errors}")
    
    log_audit("admin", "create_user", email, {"role": role, "user_id": user_id})
    
    return {"result": {"status": "success", "user_id": user_id}}


# ============================================
# METRICS HISTORY & TRENDS
# ============================================

@app.post("/save-metrics-snapshot")
async def save_metrics_endpoint():
    """
    Manually save current metrics snapshot for trend tracking
    """
    # DOB completeness
    q1 = f"""
    SELECT COUNT(*) AS total, COUNTIF(date_of_birth IS NULL) AS missing
    FROM `{CUSTOMERS_TABLE}`
    """
    df1 = run_bq_query(PROJECT_ID, q1)
    dob_completeness = 1 - (df1.iloc[0]["missing"] / df1.iloc[0]["total"]) if df1.iloc[0]["total"] > 0 else 0
    
    # Total issues
    q2 = f"SELECT COUNT(*) AS cnt FROM `{ISSUES_TABLE}`"
    df2 = run_bq_query(PROJECT_ID, q2)
    total_issues = df2.iloc[0]["cnt"]
    
    metrics = {
        "dob_completeness": dob_completeness,
        "total_issues": total_issues
    }
    
    count = save_metrics_snapshot(metrics, "manual")
    
    return {"result": {"status": "success", "metrics_saved": count}}


@app.get("/metrics-trend/{metric_name}")
async def get_trend(metric_name: str, days: int = 7):
    """
    Get historical trend for a specific metric
    """
    trend_data = get_metrics_trend(metric_name, days)
    return {"result": {"status": "success", "metric_name": metric_name, "trend": trend_data}}


# ============================================
# EXPORT ENDPOINTS
# ============================================

@app.get("/export/issues")
async def export_issues(format: str = "excel"):
    """
    Export issues to Excel format
    """
    try:
        excel_file = export_issues_to_excel()
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=agentx_issues_{datetime.now().strftime('%Y%m%d')}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/patches")
async def export_patches():
    """
    Export remediation patches to Excel
    """
    try:
        excel_file = export_remediation_patches()
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=agentx_patches_{datetime.now().strftime('%Y%m%d')}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/audit")
async def export_audit(start_date: str = None, end_date: str = None):
    """
    Export audit trail to Excel
    """
    try:
        excel_file = export_audit_trail(start_date, end_date)
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=agentx_audit_{datetime.now().strftime('%Y%m%d')}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DATAPLEX INTEGRATION ENDPOINTS
# ============================================

@app.get("/dataplex/status")
async def dataplex_status():
    """Check if Dataplex is available and configured"""
    return {
        "result": {
            "available": dataplex.is_available(),
            "message": "Dataplex is configured and ready" if dataplex.is_available() 
                      else "Dataplex not configured - using fallback methods"
        }
    }


@app.post("/dataplex/suggest-rules")
async def suggest_rules_from_dataplex(payload: dict):
    """Generate rule suggestions based on Dataplex profile"""
    table_name = payload.get("table_name")
    
    if not table_name:
        raise HTTPException(status_code=400, detail="table_name required")
    
    suggestions = dataplex.suggest_rules_from_profile(table_name)
    
    return {
        "result": {
            "status": "success",
            "count": len(suggestions),
            "suggestions": suggestions,
            "source": "dataplex" if dataplex.is_available() else "fallback"
        }
    }
