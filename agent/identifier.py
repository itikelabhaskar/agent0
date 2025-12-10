"""
Enhanced Identifier Agent
Detects multiple types of data quality issues across 5 DQ dimensions
"""
from typing import Dict, List
from agent.tools import run_bq_query
from backend.config import config
from backend.security import sanitize_identifier, sanitize_sql
import re

class IdentifierAgent:
    """
    Identifier Agent for detecting data quality issues
    Covers 5 dimensions: Completeness, Validity, Consistency, Accuracy, Timeliness
    """
    
    def __init__(self):
        self.project = config.PROJECT_ID
        self.dataset = config.DATASET
    
    # ============================================
    # COMPLETENESS CHECKS
    # ============================================
    
    def detect_missing_dob(self, table: str, limit: int = 100) -> List[Dict]:
        """Detect customers with missing date of birth"""
        table = sanitize_identifier(table)
        
        sql = f"""
        SELECT CUS_ID, CUS_FORNAME, CUS_SURNAME, 'missing_dob' as issue_type
        FROM `{config.CUSTOMERS_TABLE}`
        WHERE CUS_DOB IS NULL
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    def detect_missing_fields(self, table: str, fields: List[str], limit: int = 100) -> List[Dict]:
        """Detect records with missing critical fields"""
        table = sanitize_identifier(table)
        
        conditions = " OR ".join([f"{field} IS NULL" for field in fields])
        
        sql = f"""
        SELECT *, 'missing_field' as issue_type
        FROM `{table}`
        WHERE {conditions}
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    # ============================================
    # VALIDITY CHECKS
    # ============================================
    
    def detect_invalid_emails(self, limit: int = 100) -> List[Dict]:
        """Detect invalid email formats"""
        sql = f"""
        SELECT CUS_ID, CUS_FORNAME, CUS_SURNAME, email, 'invalid_email' as issue_type
        FROM `{config.CUSTOMERS_TABLE}`
        WHERE email IS NOT NULL 
          AND (
            NOT REGEXP_CONTAINS(email, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$')
            OR email LIKE '%@@@%'
          )
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    def detect_invalid_dates(self, limit: int = 100) -> List[Dict]:
        """Detect invalid or future dates"""
        sql = f"""
        SELECT CUS_ID, CUS_DOB, 'invalid_date' as issue_type
        FROM `{config.CUSTOMERS_TABLE}`
        WHERE CUS_DOB > CURRENT_DATE()
           OR CUS_DOB < '1900-01-01'
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    def detect_negative_amounts(self, limit: int = 100) -> List[Dict]:
        """Detect negative transaction amounts and premiums"""
        sql = f"""
        SELECT holding_id, customer_id, holding_amount, POLI_GROSS_PMT,
               'negative_amount' as issue_type
        FROM `{config.HOLDINGS_TABLE}`
        WHERE holding_amount < 0 OR POLI_GROSS_PMT < 0
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    def detect_invalid_formats(self, limit: int = 100) -> List[Dict]:
        """Detect records with invalid data formats"""
        sql = f"""
        SELECT holding_id, customer_id, effective_date, 'invalid_format' as issue_type
        FROM `{config.HOLDINGS_TABLE}`
        WHERE effective_date = 'INVALID_DATE'
           OR effective_date NOT LIKE '____-__-__'
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    # ============================================
    # CONSISTENCY CHECKS
    # ============================================
    
    def detect_duplicates(self, table: str, key_field: str, limit: int = 100) -> List[Dict]:
        """Detect duplicate records"""
        table = sanitize_identifier(table)
        key_field = sanitize_identifier(key_field)
        
        sql = f"""
        SELECT {key_field}, COUNT(*) as duplicate_count, 'duplicate' as issue_type
        FROM `{table}`
        GROUP BY {key_field}
        HAVING COUNT(*) > 1
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    def detect_orphaned_records(self, limit: int = 100) -> List[Dict]:
        """Detect holdings without corresponding customers"""
        sql = f"""
        SELECT h.holding_id, h.customer_id, 'orphaned_record' as issue_type
        FROM `{config.HOLDINGS_TABLE}` h
        LEFT JOIN `{config.CUSTOMERS_TABLE}` c
          ON h.customer_id = c.CUS_ID
        WHERE c.CUS_ID IS NULL
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    # ============================================
    # ACCURACY CHECKS (Statistical)
    # ============================================
    
    def detect_outliers(self, table: str, field: str, std_threshold: float = 3.0, limit: int = 100) -> List[Dict]:
        """Detect statistical outliers using Z-score"""
        table = sanitize_identifier(table)
        field = sanitize_identifier(field)
        
        sql = f"""
        WITH stats AS (
          SELECT 
            AVG({field}) as mean_val,
            STDDEV({field}) as std_val
          FROM `{table}`
          WHERE {field} IS NOT NULL
        )
        SELECT t.*, 
               ABS(t.{field} - s.mean_val) / NULLIF(s.std_val, 0) as z_score,
               'outlier' as issue_type
        FROM `{table}` t, stats s
        WHERE ABS(t.{field} - s.mean_val) / NULLIF(s.std_val, 0) > {std_threshold}
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    # ============================================
    # TIMELINESS CHECKS
    # ============================================
    
    def detect_stale_records(self, table: str, date_field: str, days_threshold: int = 365, limit: int = 100) -> List[Dict]:
        """Detect records that haven't been updated in a long time"""
        table = sanitize_identifier(table)
        date_field = sanitize_identifier(date_field)
        
        sql = f"""
        SELECT *, DATE_DIFF(CURRENT_DATE(), DATE({date_field}), DAY) as days_stale,
               'stale_record' as issue_type
        FROM `{table}`
        WHERE DATE_DIFF(CURRENT_DATE(), DATE({date_field}), DAY) > {days_threshold}
        LIMIT {limit}
        """
        
        df = run_bq_query(self.project, sanitize_sql(sql))
        return df.to_dict(orient='records')
    
    # ============================================
    # ORCHESTRATED DETECTION
    # ============================================
    
    def run_all_checks(self, limit_per_check: int = 50) -> Dict[str, List]:
        """
        Run all data quality checks and return categorized results
        
        Returns:
            Dict with keys: completeness, validity, consistency, accuracy, timeliness
        """
        results = {
            "completeness": [],
            "validity": [],
            "consistency": [],
            "accuracy": [],
            "timeliness": []
        }
        
        try:
            # Completeness
            results["completeness"].extend(self.detect_missing_dob(config.CUSTOMERS_TABLE, limit_per_check))
            
            # Validity
            results["validity"].extend(self.detect_invalid_emails(limit_per_check))
            results["validity"].extend(self.detect_invalid_dates(limit_per_check))
            results["validity"].extend(self.detect_negative_amounts(limit_per_check))
            results["validity"].extend(self.detect_invalid_formats(limit_per_check))
            
            # Consistency
            results["consistency"].extend(
                self.detect_duplicates(config.CUSTOMERS_TABLE, "CUS_ID", limit_per_check)
            )
            results["consistency"].extend(self.detect_orphaned_records(limit_per_check))
            
            # Accuracy
            try:
                results["accuracy"].extend(
                    self.detect_outliers(config.HOLDINGS_TABLE, "holding_amount", 3.0, limit_per_check)
                )
            except Exception as e:
                print(f"⚠️ Outlier detection failed: {e}")
            
            # Timeliness
            try:
                results["timeliness"].extend(
                    self.detect_stale_records(config.HOLDINGS_TABLE, "created_ts", 730, limit_per_check)
                )
            except Exception as e:
                print(f"⚠️ Staleness detection failed: {e}")
        
        except Exception as e:
            print(f"❌ Error during checks: {e}")
        
        # Add summary counts
        results["summary"] = {
            "total_issues": sum(len(v) for v in results.values() if isinstance(v, list)),
            "by_dimension": {k: len(v) for k, v in results.items() if isinstance(v, list)}
        }
        
        return results
    
    def run_custom_rule(self, sql: str, limit: int = 200) -> List[Dict]:
        """
        Run a custom SQL rule for detection
        SQL must be SELECT only and is sanitized
        """
        # Ensure LIMIT
        if "limit" not in sql.lower():
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        
        # Sanitize
        sql = sanitize_sql(sql, allow_only_select=True)
        
        df = run_bq_query(self.project, sql)
        return df.to_dict(orient='records')

# Global identifier agent instance
identifier = IdentifierAgent()

