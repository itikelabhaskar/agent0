"""
Knowledge Bank Management System
Stores and retrieves rules, treatments, and learned patterns
"""
import os
import yaml
import csv
import json
from typing import Dict, List, Optional
from datetime import datetime
from backend.config import config
from google.cloud import bigquery
import pandas as pd

# ============================================
# KNOWLEDGE BANK STRUCTURE
# ============================================

class KnowledgeBank:
    def __init__(self, base_path: str = None):
        self.base_path = base_path or config.KNOWLEDGE_BANK_PATH
        os.makedirs(self.base_path, exist_ok=True)
        
        self.rules_yaml_path = f"{self.base_path}/rules.yaml"
        self.treatments_csv_path = f"{self.base_path}/treatments.csv"
        self.patterns_json_path = f"{self.base_path}/patterns.json"
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Create initial knowledge bank files if missing"""
        if not os.path.exists(self.rules_yaml_path):
            self._write_yaml({
                "version": "1.0",
                "rules": [],
                "categories": {
                    "completeness": [],
                    "validity": [],
                    "consistency": [],
                    "accuracy": [],
                    "timeliness": []
                }
            })
        
        if not os.path.exists(self.treatments_csv_path):
            with open(self.treatments_csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'treatment_id', 'issue_type', 'description', 
                    'confidence', 'cost', 'approval_required', 
                    'success_rate', 'created_ts', 'approved_by'
                ])
        
        if not os.path.exists(self.patterns_json_path):
            self._write_json({
                "learned_patterns": [],
                "root_causes": {},
                "treatment_outcomes": []
            })
    
    def _write_yaml(self, data: dict):
        """Write YAML file"""
        with open(self.rules_yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def _read_yaml(self) -> dict:
        """Read YAML file"""
        with open(self.rules_yaml_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _write_json(self, data: dict):
        """Write JSON file"""
        with open(self.patterns_json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _read_json(self) -> dict:
        """Read JSON file"""
        with open(self.patterns_json_path, 'r') as f:
            return json.load(f)
    
    # ============================================
    # RULE MANAGEMENT
    # ============================================
    
    def add_rule(self, rule_data: dict, category: str = "completeness", 
                 approval_status: str = "pending"):
        """
        Add a rule to the knowledge bank
        
        Args:
            rule_data: Dict with rule_id, rule_text, sql_snippet, created_by, etc.
            category: DQ dimension category
            approval_status: pending, approved, rejected
        """
        rules = self._read_yaml()
        
        rule_entry = {
            "rule_id": rule_data.get("rule_id"),
            "rule_text": rule_data.get("rule_text"),
            "sql_snippet": rule_data.get("sql_snippet"),
            "category": category,
            "created_by": rule_data.get("created_by"),
            "created_ts": datetime.utcnow().isoformat(),
            "approval_status": approval_status,
            "approved_by": rule_data.get("approved_by"),
            "metadata": rule_data.get("metadata", {})
        }
        
        # Add to main rules list
        rules["rules"].append(rule_entry)
        
        # Add to category
        if category not in rules["categories"]:
            rules["categories"][category] = []
        rules["categories"][category].append(rule_entry["rule_id"])
        
        self._write_yaml(rules)
        return rule_entry
    
    def get_rules_by_category(self, category: str) -> List[dict]:
        """Get all rules in a category"""
        rules = self._read_yaml()
        rule_ids = rules.get("categories", {}).get(category, [])
        
        return [
            rule for rule in rules.get("rules", [])
            if rule["rule_id"] in rule_ids
        ]
    
    def get_rule(self, rule_id: str) -> Optional[dict]:
        """Get a specific rule"""
        rules = self._read_yaml()
        for rule in rules.get("rules", []):
            if rule["rule_id"] == rule_id:
                return rule
        return None
    
    def approve_rule(self, rule_id: str, approved_by: str):
        """Approve a pending rule"""
        rules = self._read_yaml()
        for rule in rules.get("rules", []):
            if rule["rule_id"] == rule_id:
                rule["approval_status"] = "approved"
                rule["approved_by"] = approved_by
                rule["approved_ts"] = datetime.utcnow().isoformat()
                break
        self._write_yaml(rules)
    
    # ============================================
    # TREATMENT MANAGEMENT
    # ============================================
    
    def add_treatment(self, treatment_data: dict):
        """
        Add a treatment strategy to knowledge bank
        
        Args:
            treatment_data: Dict with issue_type, description, confidence, etc.
        """
        with open(self.treatments_csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                treatment_data.get("treatment_id"),
                treatment_data.get("issue_type"),
                treatment_data.get("description"),
                treatment_data.get("confidence", 0.5),
                treatment_data.get("cost", 0),
                treatment_data.get("approval_required", True),
                treatment_data.get("success_rate", 0.0),
                datetime.utcnow().isoformat(),
                treatment_data.get("approved_by", "")
            ])
    
    def get_treatments_for_issue(self, issue_type: str) -> List[dict]:
        """Get all treatments for a specific issue type"""
        treatments = []
        with open(self.treatments_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['issue_type'] == issue_type:
                    treatments.append(row)
        return treatments
    
    def update_treatment_success_rate(self, treatment_id: str, success: bool):
        """Update treatment success rate based on outcome"""
        df = pd.read_csv(self.treatments_csv_path)
        
        idx = df[df['treatment_id'] == treatment_id].index
        if len(idx) > 0:
            current_rate = float(df.loc[idx[0], 'success_rate'])
            # Simple moving average update
            new_rate = (current_rate * 0.9) + (1.0 if success else 0.0) * 0.1
            df.loc[idx[0], 'success_rate'] = new_rate
            df.to_csv(self.treatments_csv_path, index=False)
    
    # ============================================
    # PATTERN LEARNING
    # ============================================
    
    def add_learned_pattern(self, pattern: dict):
        """
        Store a learned data quality pattern
        
        Args:
            pattern: Dict with pattern_type, indicators, frequency, etc.
        """
        patterns = self._read_json()
        
        pattern_entry = {
            "pattern_id": f"PAT_{len(patterns['learned_patterns'])+1:04d}",
            "pattern_type": pattern.get("pattern_type"),
            "indicators": pattern.get("indicators", []),
            "frequency": pattern.get("frequency", 0),
            "severity": pattern.get("severity", "medium"),
            "learned_ts": datetime.utcnow().isoformat(),
            "metadata": pattern.get("metadata", {})
        }
        
        patterns["learned_patterns"].append(pattern_entry)
        self._write_json(patterns)
        return pattern_entry
    
    def add_root_cause(self, issue_type: str, root_cause: str, evidence: dict):
        """
        Store root cause analysis result
        
        Args:
            issue_type: Type of issue
            root_cause: Identified root cause
            evidence: Supporting evidence dict
        """
        patterns = self._read_json()
        
        if issue_type not in patterns["root_causes"]:
            patterns["root_causes"][issue_type] = []
        
        patterns["root_causes"][issue_type].append({
            "root_cause": root_cause,
            "evidence": evidence,
            "identified_ts": datetime.utcnow().isoformat(),
            "confidence": evidence.get("confidence", 0.5)
        })
        
        self._write_json(patterns)
    
    def get_root_causes(self, issue_type: str) -> List[dict]:
        """Get known root causes for an issue type"""
        patterns = self._read_json()
        return patterns.get("root_causes", {}).get(issue_type, [])
    
    def add_treatment_outcome(self, treatment_id: str, issue_id: str, 
                             success: bool, details: dict):
        """
        Record treatment outcome for learning
        
        Args:
            treatment_id: ID of applied treatment
            issue_id: ID of issue treated
            success: Whether treatment was successful
            details: Outcome details
        """
        patterns = self._read_json()
        
        outcome = {
            "treatment_id": treatment_id,
            "issue_id": issue_id,
            "success": success,
            "details": details,
            "recorded_ts": datetime.utcnow().isoformat()
        }
        
        patterns["treatment_outcomes"].append(outcome)
        self._write_json(patterns)
        
        # Update treatment success rate
        self.update_treatment_success_rate(treatment_id, success)
    
    # ============================================
    # BIGQUERY SYNC
    # ============================================
    
    def sync_to_bigquery(self):
        """
        Sync knowledge bank to BigQuery knowledge_bank table
        """
        client = bigquery.Client(project=config.PROJECT_ID)
        
        # Create table if not exists
        schema = [
            bigquery.SchemaField("kb_id", "STRING"),
            bigquery.SchemaField("kb_type", "STRING"),  # rule, treatment, pattern
            bigquery.SchemaField("content", "STRING"),  # JSON
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("created_ts", "TIMESTAMP"),
        ]
        
        table_id = config.KNOWLEDGE_BANK_TABLE
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            table = client.create_table(table)
        except Exception:
            # Table exists
            pass
        
        # Sync rules
        rules = self._read_yaml()
        rows = []
        for rule in rules.get("rules", []):
            rows.append({
                "kb_id": rule["rule_id"],
                "kb_type": "rule",
                "content": json.dumps(rule),
                "category": rule.get("category", ""),
                "status": rule.get("approval_status", ""),
                "created_ts": rule.get("created_ts")
            })
        
        if rows:
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                print(f"⚠️ KB sync errors: {errors}")
        
        return len(rows)
    
    def load_from_bigquery(self):
        """
        Load knowledge bank from BigQuery
        """
        from agent.tools import run_bq_query
        
        query = f"""
        SELECT kb_id, kb_type, content, category, status
        FROM `{config.KNOWLEDGE_BANK_TABLE}`
        ORDER BY created_ts DESC
        """
        
        try:
            df = run_bq_query(config.PROJECT_ID, query)
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"⚠️ Could not load from BQ: {e}")
            return []

# Global knowledge bank instance
kb = KnowledgeBank()

