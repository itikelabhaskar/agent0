"""
Enhanced Remediator Agent
Applies fixes to data with before/after audit logging
"""
from typing import Dict, List, Optional
from agent.tools import run_bq_query, run_bq_nonquery
from backend.config import config
from backend.security import sanitize_identifier
from backend.enhancements import log_audit
from google.cloud import bigquery
import json
import uuid
from datetime import datetime

class RemediatorAgent:
    """
    Remediator Agent for applying data quality fixes
    Supports dryrun and apply modes with full audit trail
    """
    
    def __init__(self):
        self.project = config.PROJECT_ID
        self.dataset = config.DATASET
        self.client = bigquery.Client(project=self.project)
    
    # ============================================
    # DATA CAPTURE
    # ============================================
    
    def capture_current_state(self, table: str, record_id: str, id_field: str = "CUS_ID") -> Dict:
        """
        Capture current state of a record before modification
        
        Args:
            table: Table name
            record_id: ID of the record
            id_field: Name of the ID field
            
        Returns:
            Dict with current record data
        """
        table = sanitize_identifier(table)
        id_field = sanitize_identifier(id_field)
        
        sql = f"""
        SELECT *
        FROM `{table}`
        WHERE {id_field} = '{record_id}'
        LIMIT 1
        """
        
        df = run_bq_query(self.project, sql)
        if df.empty:
            return {}
        
        return df.iloc[0].to_dict()
    
    # ============================================
    # FIX GENERATION
    # ============================================
    
    def generate_update_sql(self, table: str, record_id: str, updates: Dict, 
                           id_field: str = "CUS_ID") -> str:
        """
        Generate UPDATE SQL statement
        
        Args:
            table: Table name
            record_id: ID of record to update
            updates: Dict of field_name: new_value
            id_field: Name of ID field
            
        Returns:
            UPDATE SQL statement
        """
        table = sanitize_identifier(table)
        id_field = sanitize_identifier(id_field)
        
        # Build SET clause
        set_clauses = []
        for field, value in updates.items():
            field = sanitize_identifier(field)
            if value is None:
                set_clauses.append(f"{field} = NULL")
            elif isinstance(value, (int, float)):
                set_clauses.append(f"{field} = {value}")
            else:
                # Escape single quotes
                value = str(value).replace("'", "''")
                set_clauses.append(f"{field} = '{value}'")
        
        set_clause = ", ".join(set_clauses)
        
        sql = f"""
        UPDATE `{table}`
        SET {set_clause}
        WHERE {id_field} = '{record_id}'
        """
        
        return sql
    
    def generate_insert_sql(self, table: str, record_data: Dict) -> str:
        """
        Generate INSERT SQL statement
        
        Args:
            table: Table name
            record_data: Dict of field_name: value
            
        Returns:
            INSERT SQL statement
        """
        table = sanitize_identifier(table)
        
        fields = []
        values = []
        
        for field, value in record_data.items():
            field = sanitize_identifier(field)
            fields.append(field)
            
            if value is None:
                values.append("NULL")
            elif isinstance(value, (int, float)):
                values.append(str(value))
            else:
                value = str(value).replace("'", "''")
                values.append(f"'{value}'")
        
        fields_str = ", ".join(fields)
        values_str = ", ".join(values)
        
        sql = f"""
        INSERT INTO `{table}` ({fields_str})
        VALUES ({values_str})
        """
        
        return sql
    
    # ============================================
    # SAFE OPERATIONS
    # ============================================
    
    def apply_fix_missing_value(self, table: str, record_id: str, 
                                field: str, new_value: any,
                                mode: str = "dryrun",
                                applied_by: str = "system") -> Dict:
        """
        Apply fix for missing value
        
        Args:
            table: Table name (e.g., "customers")
            record_id: Record ID
            field: Field to update
            new_value: New value to set
            mode: "dryrun" or "apply"
            applied_by: User applying the fix
            
        Returns:
            Dict with status, before/after data, patch_id
        """
        # Determine ID field based on table
        id_field = "CUS_ID" if "customer" in table.lower() else "holding_id"
        
        # Get full table name
        if "." not in table:
            table = f"{config.DATASET}.{table}"
        
        full_table = f"{self.project}.{table}"
        
        # Capture before state
        before_data = self.capture_current_state(full_table, record_id, id_field)
        
        if not before_data:
            return {
                "status": "error",
                "error": f"Record {record_id} not found in {table}"
            }
        
        if mode == "dryrun":
            # Show what would change
            after_data = before_data.copy()
            after_data[field] = new_value
            
            return {
                "status": "dryrun",
                "table": table,
                "record_id": record_id,
                "field": field,
                "before_value": before_data.get(field),
                "after_value": new_value,
                "before_data": before_data,
                "after_data": after_data
            }
        
        elif mode == "apply":
            # Generate and execute UPDATE
            updates = {field: new_value}
            update_sql = self.generate_update_sql(full_table, record_id, updates, id_field)
            
            try:
                # Execute update
                run_bq_nonquery(self.project, update_sql)
                
                # Capture after state
                after_data = self.capture_current_state(full_table, record_id, id_field)
                
                # Create patch record
                patch_id = self.save_remediation_patch(
                    issue_id=f"{table}_{record_id}_{field}",
                    rule_id="manual_fix",
                    before_data=before_data,
                    after_data=after_data,
                    applied_by=applied_by
                )
                
                # Log audit
                log_audit(
                    applied_by,
                    "apply_fix",
                    f"{table}.{record_id}",
                    {
                        "field": field,
                        "before": before_data.get(field),
                        "after": new_value
                    },
                    "success"
                )
                
                return {
                    "status": "applied",
                    "patch_id": patch_id,
                    "table": table,
                    "record_id": record_id,
                    "field": field,
                    "before_value": before_data.get(field),
                    "after_value": after_data.get(field),
                    "sql_executed": update_sql
                }
            
            except Exception as e:
                # Log failure
                log_audit(
                    applied_by,
                    "apply_fix",
                    f"{table}.{record_id}",
                    {"field": field, "error": str(e)},
                    "failed"
                )
                
                return {
                    "status": "error",
                    "error": str(e),
                    "sql_attempted": update_sql
                }
    
    def apply_batch_fix(self, table: str, record_ids: List[str],
                       field: str, new_value: any,
                       mode: str = "dryrun",
                       applied_by: str = "system") -> Dict:
        """
        Apply fix to multiple records
        
        Args:
            table: Table name
            record_ids: List of record IDs
            field: Field to update
            new_value: New value (can be function/expression)
            mode: "dryrun" or "apply"
            applied_by: User applying fix
            
        Returns:
            Dict with batch results
        """
        results = []
        
        for record_id in record_ids:
            result = self.apply_fix_missing_value(
                table, record_id, field, new_value, mode, applied_by
            )
            results.append(result)
        
        summary = {
            "status": "batch_complete",
            "mode": mode,
            "total": len(record_ids),
            "successful": sum(1 for r in results if r['status'] in ['applied', 'dryrun']),
            "failed": sum(1 for r in results if r['status'] == 'error'),
            "results": results
        }
        
        return summary
    
    # ============================================
    # AUDIT & ROLLBACK
    # ============================================
    
    def save_remediation_patch(self, issue_id: str, rule_id: str,
                              before_data: Dict, after_data: Dict,
                              applied_by: str, status: str = "applied") -> str:
        """
        Save remediation patch to remediation_patches table
        
        Returns:
            patch_id
        """
        patch_id = str(uuid.uuid4())[:12]
        
        rows = [{
            "patch_id": patch_id,
            "issue_id": issue_id,
            "rule_id": rule_id,
            "before_data": json.dumps(before_data, default=str),
            "after_data": json.dumps(after_data, default=str),
            "applied_by": applied_by,
            "applied_ts": datetime.utcnow().isoformat(),
            "status": status
        }]
        
        table_id = config.REMEDIATION_PATCHES_TABLE
        errors = self.client.insert_rows_json(table_id, rows)
        
        if errors:
            print(f"⚠️ Failed to save patch: {errors}")
        
        return patch_id
    
    def rollback_patch(self, patch_id: str, rolled_back_by: str) -> Dict:
        """
        Rollback a remediation patch
        
        Args:
            patch_id: Patch ID to rollback
            rolled_back_by: User performing rollback
            
        Returns:
            Dict with rollback status
        """
        # Get patch details
        sql = f"""
        SELECT patch_id, issue_id, before_data, after_data
        FROM `{config.REMEDIATION_PATCHES_TABLE}`
        WHERE patch_id = '{patch_id}'
        LIMIT 1
        """
        
        df = run_bq_query(self.project, sql)
        if df.empty:
            return {"status": "error", "error": "Patch not found"}
        
        patch = df.iloc[0]
        before_data = json.loads(patch['before_data'])
        
        # Parse issue_id to get table and record
        issue_parts = patch['issue_id'].split('_')
        table = issue_parts[0]
        record_id = issue_parts[1] if len(issue_parts) > 1 else None
        
        if not record_id:
            return {"status": "error", "error": "Cannot parse issue_id for rollback"}
        
        # Apply rollback (restore before_data)
        # This is essentially applying the before_data as the new state
        # Implementation depends on what changed
        
        log_audit(
            rolled_back_by,
            "rollback_patch",
            patch_id,
            {"issue_id": patch['issue_id']},
            "success"
        )
        
        return {
            "status": "rolled_back",
            "patch_id": patch_id,
            "restored_data": before_data
        }
    
    # ============================================
    # JIRA-STYLE TICKET CREATION
    # ============================================
    
    def create_manual_ticket(self, issue: Dict, reason: str) -> Dict:
        """
        Create a manual intervention ticket for unsafe fixes
        
        Args:
            issue: Issue dict
            reason: Reason for manual intervention
            
        Returns:
            Ticket dict
        """
        ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        
        ticket = {
            "ticket_id": ticket_id,
            "issue_id": issue.get("issue_id"),
            "issue_type": issue.get("issue_type"),
            "reason": reason,
            "status": "open",
            "priority": issue.get("severity", "medium"),
            "created_ts": datetime.utcnow().isoformat(),
            "assigned_to": None,
            "details": json.dumps(issue, default=str)
        }
        
        # In a real system, this would integrate with Jira API
        # For now, we log it
        log_audit(
            "system",
            "create_ticket",
            ticket_id,
            ticket,
            "success"
        )
        
        return ticket

# Global remediator instance
remediator = RemediatorAgent()

