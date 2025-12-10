"""
Enhancement features for AgentX:
- Rule versioning & rollback
- Audit trail logging
- Role-based access control
- Export capabilities
"""
from fastapi import HTTPException, Request
from google.cloud import bigquery
from agent.tools import run_bq_query, run_bq_nonquery
from datetime import datetime
import uuid
import json
import pandas as pd
import io
import os
import sys
from typing import Optional

# Load config for environment switching
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import CONFIG

PROJECT_ID = CONFIG["project_id"]
DATASET = CONFIG["dataset"]

# ============================================
# AUDIT LOGGING
# ============================================

def log_audit(user_email: str, action_type: str, action_target: str, 
              action_details: dict, status: str = "success", 
              ip_address: str = "0.0.0.0", user_id: str = "system"):
    """
    Log all actions to audit_log table
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        audit_id = str(uuid.uuid4())[:12]
        
        rows = [{
            "audit_id": audit_id,
            "user_id": user_id,
            "user_email": user_email,
            "action_type": action_type,
            "action_target": action_target,
            "action_details": json.dumps(action_details),
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "status": status
        }]
        
        table_id = f"{PROJECT_ID}.{DATASET}.audit_log"
        errors = client.insert_rows_json(table_id, rows)
        
        if errors:
            print(f"⚠️ Audit logging error: {errors}")
        
        return audit_id
    except Exception as e:
        print(f"❌ Audit logging failed: {e}")
        return None

# ============================================
# RULE VERSIONING
# ============================================

def save_rule_version(rule_id: str, sql_snippet: str, rule_text: str, 
                     created_by: str, change_reason: str = "initial"):
    """
    Save a new version of a rule to rules_history
    """
    try:
        # Get current version count
        version_query = f"""
        SELECT COALESCE(MAX(version_number), 0) as max_version
        FROM `{PROJECT_ID}.{DATASET}.rules_history`
        WHERE rule_id = '{rule_id}'
        """
        df = run_bq_query(PROJECT_ID, version_query)
        next_version = int(df.iloc[0]['max_version']) + 1 if not df.empty else 1
        
        version_id = str(uuid.uuid4())[:12]
        
        client = bigquery.Client(project=PROJECT_ID)
        rows = [{
            "version_id": version_id,
            "rule_id": rule_id,
            "version_number": next_version,
            "sql_snippet": sql_snippet,
            "rule_text": rule_text,
            "created_by": created_by,
            "created_ts": datetime.utcnow().isoformat(),
            "change_reason": change_reason,
            "is_active": True
        }]
        
        table_id = f"{PROJECT_ID}.{DATASET}.rules_history"
        errors = client.insert_rows_json(table_id, rows)
        
        if errors:
            raise Exception(f"Failed to save version: {errors}")
        
        return {"version_id": version_id, "version_number": next_version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Version save failed: {e}")

def get_rule_versions(rule_id: str):
    """
    Get all versions of a rule
    """
    query = f"""
    SELECT version_id, rule_id, version_number, sql_snippet, rule_text, 
           created_by, created_ts, change_reason, is_active
    FROM `{PROJECT_ID}.{DATASET}.rules_history`
    WHERE rule_id = '{rule_id}'
    ORDER BY version_number DESC
    """
    df = run_bq_query(PROJECT_ID, query)
    return df.to_dict(orient="records")

def rollback_rule(rule_id: str, target_version: int, rollback_by: str):
    """
    Rollback a rule to a specific version
    """
    try:
        # Get the target version
        version_query = f"""
        SELECT sql_snippet, rule_text
        FROM `{PROJECT_ID}.{DATASET}.rules_history`
        WHERE rule_id = '{rule_id}' AND version_number = {target_version}
        LIMIT 1
        """
        df = run_bq_query(PROJECT_ID, version_query)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Version not found")
        
        old_sql = df.iloc[0]['sql_snippet']
        old_text = df.iloc[0]['rule_text']
        
        # Update the main rules table
        update_sql = f"""
        UPDATE `{PROJECT_ID}.{DATASET}.rules`
        SET sql_snippet = "{old_sql}",
            rule_text = "{old_text}"
        WHERE rule_id = '{rule_id}'
        """
        run_bq_nonquery(PROJECT_ID, update_sql)
        
        # Save new version indicating rollback
        save_rule_version(
            rule_id, old_sql, old_text, rollback_by, 
            f"Rolled back to version {target_version}"
        )
        
        # Log the rollback
        log_audit(
            rollback_by, "rollback_rule", rule_id,
            {"target_version": target_version, "sql": old_sql}
        )
        
        return {"status": "success", "message": f"Rolled back to version {target_version}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {e}")

# ============================================
# RBAC - Role-Based Access Control
# ============================================

def get_user_by_email(email: str):
    """
    Get user details from users table
    """
    query = f"""
    SELECT user_id, email, full_name, role, is_active
    FROM `{PROJECT_ID}.{DATASET}.users`
    WHERE email = '{email}' AND is_active = TRUE
    LIMIT 1
    """
    df = run_bq_query(PROJECT_ID, query)
    if df.empty:
        return None
    return df.iloc[0].to_dict()

def check_permission(user_role: str, required_role: str):
    """
    Check if user has required permission
    Hierarchy: admin > engineer > business_user
    """
    role_hierarchy = {"admin": 3, "engineer": 2, "business_user": 1}
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    return user_level >= required_level

# ============================================
# METRICS HISTORY (for trend visualization)
# ============================================

def save_metrics_snapshot(metrics: dict, source: str = "manual"):
    """
    Save current metrics to history for trend tracking
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        rows = []
        
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                rows.append({
                    "metric_id": str(uuid.uuid4())[:12],
                    "metric_name": metric_name,
                    "metric_value": float(metric_value),
                    "metric_details": json.dumps({"source": source}),
                    "recorded_ts": datetime.utcnow().isoformat(),
                    "source": source
                })
        
        if rows:
            table_id = f"{PROJECT_ID}.{DATASET}.metrics_history"
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                print(f"⚠️ Metrics history save error: {errors}")
            return len(rows)
        return 0
    except Exception as e:
        print(f"❌ Metrics save failed: {e}")
        return 0

def get_metrics_trend(metric_name: str, days: int = 7):
    """
    Get historical trend for a specific metric
    """
    query = f"""
    SELECT metric_name, metric_value, recorded_ts
    FROM `{PROJECT_ID}.{DATASET}.metrics_history`
    WHERE metric_name = '{metric_name}'
      AND recorded_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
    ORDER BY recorded_ts ASC
    """
    df = run_bq_query(PROJECT_ID, query)
    return df.to_dict(orient="records")

# ============================================
# EXPORT CAPABILITIES
# ============================================

def export_issues_to_excel(issue_ids: list = None):
    """
    Export issues to Excel format
    """
    try:
        if issue_ids:
            ids_str = "','".join(issue_ids)
            where_clause = f"WHERE issue_id IN ('{ids_str}')"
            limit_clause = ""
        else:
            where_clause = ""
            limit_clause = "LIMIT 1000"
        
        query = f"""
        SELECT issue_id, rule_id, rule_text, detected_ts, 
               source_table, match_json, severity, note
        FROM `{PROJECT_ID}.{DATASET}.issues`
        {where_clause}
        ORDER BY detected_ts DESC
        {limit_clause}
        """
        df = run_bq_query(PROJECT_ID, query)
        
        # Convert timezone-aware datetime columns to timezone-naive
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Issues', index=False)
            
            # Add a summary sheet
            if not df.empty:
                summary_df = df.groupby(['rule_id', 'severity']).size().reset_index(name='count')
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

def export_remediation_patches(patch_ids: list = None):
    """
    Export remediation patches with before/after comparison
    """
    try:
        if patch_ids:
            ids_str = "','".join(patch_ids)
            where_clause = f"WHERE patch_id IN ('{ids_str}')"
            limit_clause = ""
        else:
            where_clause = ""
            limit_clause = "LIMIT 500"
        
        query = f"""
        SELECT patch_id, issue_id, rule_id, before_data, after_data,
               applied_by, applied_ts, status
        FROM `{PROJECT_ID}.{DATASET}.remediation_patches`
        {where_clause}
        ORDER BY applied_ts DESC
        {limit_clause}
        """
        df = run_bq_query(PROJECT_ID, query)
        
        # Convert timezone-aware datetime columns to timezone-naive
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Patches', index=False)
        
        output.seek(0)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patch export failed: {e}")

def export_audit_trail(start_date: str = None, end_date: str = None):
    """
    Export audit trail for compliance
    """
    try:
        date_filter = ""
        if start_date and end_date:
            date_filter = f"WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'"
        
        query = f"""
        SELECT audit_id, user_email, action_type, action_target,
               action_details, timestamp, status
        FROM `{PROJECT_ID}.{DATASET}.audit_log`
        {date_filter}
        ORDER BY timestamp DESC
        LIMIT 5000
        """
        df = run_bq_query(PROJECT_ID, query)
        
        # Convert timezone-aware datetime columns to timezone-naive
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Audit_Trail', index=False)
        
        output.seek(0)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit export failed: {e}")

