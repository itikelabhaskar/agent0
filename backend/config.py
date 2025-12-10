"""
Centralized configuration management for AgentX
Loads from config.json and environment variables
"""
import json
import os
import sys
from typing import Optional

# Import the central config loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config_loader import CONFIG as CENTRAL_CONFIG
except ImportError:
    CENTRAL_CONFIG = {}

class Config:
    def __init__(self):
        # Load from config.json (legacy) or use central config
        config_path = os.getenv("AGENTX_CONFIG", "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = CENTRAL_CONFIG if CENTRAL_CONFIG else {}
        
        # Core GCP settings - use central config as default
        default_project = CENTRAL_CONFIG.get("project_id", "REPLACE_ME") if CENTRAL_CONFIG else "REPLACE_ME"
        self.PROJECT_ID = os.getenv("PROJECT_ID", config_data.get("project_id", default_project))
        self.DATASET = os.getenv("DATASET", config_data.get("dataset", "dev_dataset"))
        self.REGION = os.getenv("REGION", config_data.get("region", "us-central1"))
        
        # Table names
        self.CUSTOMERS_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.customers"
        self.HOLDINGS_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.holdings"
        self.RULES_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.rules"
        self.RULES_HISTORY_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.rules_history"
        self.ISSUES_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.issues"
        self.AUDIT_LOG_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.audit_log"
        self.USERS_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.users"
        self.METRICS_HISTORY_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.metrics_history"
        self.REMEDIATION_PATCHES_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.remediation_patches"
        self.KNOWLEDGE_BANK_TABLE = f"{self.PROJECT_ID}.{self.DATASET}.knowledge_bank"
        
        # Security
        self.API_KEY = os.getenv("AGENTX_API_KEY", config_data.get("api_key"))
        self.ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"
        
        # Vertex AI
        self.VERTEX_MODEL = config_data.get("vertex_model", "gemini-1.0-pro")
        self.VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", self.REGION)
        
        # Knowledge Bank
        self.KNOWLEDGE_BANK_PATH = os.getenv("KNOWLEDGE_BANK_PATH", "knowledge_bank")
        self.KNOWLEDGE_BANK_YAML = f"{self.KNOWLEDGE_BANK_PATH}/rules.yaml"
        self.KNOWLEDGE_BANK_CSV = f"{self.KNOWLEDGE_BANK_PATH}/treatments.csv"
        
        # Dataplex (optional)
        self.DATAPLEX_LAKE = config_data.get("dataplex_lake")
        self.DATAPLEX_ZONE = config_data.get("dataplex_zone")
        
        # Limits
        self.MAX_QUERY_ROWS = int(os.getenv("MAX_QUERY_ROWS", "10000"))
        self.DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "200"))
        
    def get_table_fqn(self, table_name: str) -> str:
        """Get fully qualified table name"""
        return f"{self.PROJECT_ID}.{self.DATASET}.{table_name}"

# Global config instance
config = Config()

