"""
Dataplex Integration for AgentX
Uses Google Cloud Dataplex for data profiling and metadata discovery
"""
from typing import Dict, List, Optional
from backend.config import config
import json

# Try to import Dataplex, but gracefully handle if not installed
try:
    from google.cloud import dataplex_v1
    DATAPLEX_AVAILABLE = True
except ImportError:
    DATAPLEX_AVAILABLE = False
    print("⚠️  google-cloud-dataplex not installed. Install with: pip install google-cloud-dataplex")
    # Create mock class for type hints
    class dataplex_v1:
        pass

class DataplexIntegration:
    """
    Integration with Google Cloud Dataplex for automated data profiling
    """
    
    def __init__(self):
        self.project = config.PROJECT_ID
        self.location = config.REGION
        self.lake_name = config.DATAPLEX_LAKE
        self.zone_name = config.DATAPLEX_ZONE
        
        # Initialize clients (will fail gracefully if Dataplex not configured)
        if not DATAPLEX_AVAILABLE:
            print("⚠️  Dataplex library not installed - using fallback mode")
            self.available = False
            return
        
        try:
            self.dataplex_client = dataplex_v1.DataplexServiceClient()
            self.catalog_client = dataplex_v1.CatalogServiceClient()
            self.data_scan_client = dataplex_v1.DataScanServiceClient()
            self.available = True
            print("✅ Dataplex integration initialized")
        except Exception as e:
            print(f"⚠️  Dataplex not available: {e}")
            self.available = False
    
    # ============================================
    # DATA PROFILING
    # ============================================
    
    def create_data_profile_scan(self, table_name: str, scan_name: str = None) -> Optional[str]:
        """
        Create a Dataplex Data Profile scan for a BigQuery table
        
        Args:
            table_name: Full table name (project.dataset.table)
            scan_name: Optional custom scan name
            
        Returns:
            Scan ID if successful, None otherwise
        """
        if not self.available:
            print("⚠️  Dataplex not available, skipping profile scan creation")
            return None
        
        if not scan_name:
            scan_name = f"profile_{table_name.split('.')[-1]}"
        
        try:
            parent = f"projects/{self.project}/locations/{self.location}"
            
            # Create DataProfileSpec
            data_profile_spec = dataplex_v1.DataProfileSpec(
                sampling_percent=100.0,  # Profile 100% of data for small tables
                row_filter=""  # No filter, profile all rows
            )
            
            # Create DataSource pointing to BigQuery
            data_source = dataplex_v1.DataSource(
                resource=f"//bigquery.googleapis.com/projects/{self.project}/datasets/{config.DATASET}/tables/{table_name.split('.')[-1]}"
            )
            
            # Create DataScan
            data_scan = dataplex_v1.DataScan(
                data=data_source,
                data_profile_spec=data_profile_spec,
                description=f"Automated profile scan for {table_name}"
            )
            
            request = dataplex_v1.CreateDataScanRequest(
                parent=parent,
                data_scan=data_scan,
                data_scan_id=scan_name
            )
            
            operation = self.data_scan_client.create_data_scan(request=request)
            response = operation.result()
            
            scan_id = response.name.split('/')[-1]
            print(f"✅ Created Dataplex profile scan: {scan_id}")
            
            return scan_id
        
        except Exception as e:
            print(f"❌ Failed to create profile scan: {e}")
            return None
    
    def get_data_profile(self, table_name: str) -> Optional[Dict]:
        """
        Get data profile results for a table
        
        Args:
            table_name: Table name
            
        Returns:
            Dict with profile statistics
        """
        if not self.available:
            return None
        
        try:
            # Get the scan name
            scan_name = f"profile_{table_name.split('.')[-1]}"
            scan_path = f"projects/{self.project}/locations/{self.location}/dataScans/{scan_name}"
            
            # Get latest scan result
            request = dataplex_v1.ListDataScanJobsRequest(
                parent=scan_path,
                page_size=1  # Get most recent
            )
            
            response = self.data_scan_client.list_data_scan_jobs(request=request)
            
            for job in response:
                if job.data_profile_result:
                    profile = job.data_profile_result
                    
                    # Extract key statistics
                    stats = {
                        "row_count": profile.row_count,
                        "columns": []
                    }
                    
                    # Get column profiles
                    for field in profile.profile.fields:
                        col_stats = {
                            "name": field.name,
                            "type": field.type_,
                            "mode": field.mode,
                            "profile": {}
                        }
                        
                        # Extract relevant stats based on type
                        if hasattr(field.profile, 'null_ratio'):
                            col_stats["profile"]["null_ratio"] = field.profile.null_ratio
                        
                        if hasattr(field.profile, 'string_profile'):
                            sp = field.profile.string_profile
                            col_stats["profile"]["avg_length"] = sp.average_length
                            col_stats["profile"]["min_length"] = sp.min_length
                            col_stats["profile"]["max_length"] = sp.max_length
                        
                        if hasattr(field.profile, 'numeric_profile'):
                            np_prof = field.profile.numeric_profile
                            col_stats["profile"]["mean"] = np_prof.mean
                            col_stats["profile"]["std_dev"] = np_prof.std_dev
                            col_stats["profile"]["min"] = np_prof.min
                            col_stats["profile"]["max"] = np_prof.max
                            col_stats["profile"]["quartiles"] = list(np_prof.quartiles) if np_prof.quartiles else []
                        
                        stats["columns"].append(col_stats)
                    
                    return stats
            
            return None
        
        except Exception as e:
            print(f"⚠️  Failed to get profile: {e}")
            return None
    
    def run_profile_scan(self, table_name: str) -> bool:
        """
        Trigger a profile scan run
        
        Args:
            table_name: Table to profile
            
        Returns:
            True if scan started successfully
        """
        if not self.available:
            return False
        
        try:
            scan_name = f"profile_{table_name.split('.')[-1]}"
            scan_path = f"projects/{self.project}/locations/{self.location}/dataScans/{scan_name}"
            
            request = dataplex_v1.RunDataScanRequest(name=scan_path)
            response = self.data_scan_client.run_data_scan(request=request)
            
            print(f"✅ Started profile scan for {table_name}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to run scan: {e}")
            return False
    
    # ============================================
    # AUTOMATED RULE SUGGESTION FROM PROFILE
    # ============================================
    
    def suggest_rules_from_profile(self, table_name: str) -> List[Dict]:
        """
        Generate rule suggestions based on Dataplex profile
        
        Args:
            table_name: Table name
            
        Returns:
            List of suggested rules
        """
        profile = self.get_data_profile(table_name)
        
        if not profile:
            print("⚠️  No profile available, using fallback rules")
            return self._get_fallback_rules(table_name)
        
        suggestions = []
        
        for column in profile.get("columns", []):
            col_name = column["name"]
            col_profile = column.get("profile", {})
            
            # Rule 1: High null ratio
            null_ratio = col_profile.get("null_ratio", 0)
            if null_ratio > 0.1:  # More than 10% nulls
                suggestions.append({
                    "rule_type": "completeness",
                    "column": col_name,
                    "issue": f"High null ratio ({null_ratio:.1%})",
                    "suggested_sql": f"SELECT * FROM `{table_name}` WHERE {col_name} IS NULL LIMIT 200",
                    "confidence": 0.9,
                    "source": "dataplex_profile"
                })
            
            # Rule 2: Numeric outliers (using quartiles)
            if "quartiles" in col_profile and len(col_profile["quartiles"]) >= 3:
                q1 = col_profile["quartiles"][0]
                q3 = col_profile["quartiles"][2]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                suggestions.append({
                    "rule_type": "accuracy",
                    "column": col_name,
                    "issue": f"Values outside IQR bounds ({lower_bound:.2f} - {upper_bound:.2f})",
                    "suggested_sql": f"SELECT * FROM `{table_name}` WHERE {col_name} < {lower_bound} OR {col_name} > {upper_bound} LIMIT 200",
                    "confidence": 0.8,
                    "source": "dataplex_profile"
                })
            
            # Rule 3: String length anomalies
            if "avg_length" in col_profile:
                avg_len = col_profile["avg_length"]
                suggestions.append({
                    "rule_type": "validity",
                    "column": col_name,
                    "issue": f"String length significantly different from average ({avg_len:.0f})",
                    "suggested_sql": f"SELECT * FROM `{table_name}` WHERE LENGTH({col_name}) > {avg_len * 2} OR LENGTH({col_name}) < {avg_len * 0.5} LIMIT 200",
                    "confidence": 0.7,
                    "source": "dataplex_profile"
                })
        
        print(f"✅ Generated {len(suggestions)} rule suggestions from Dataplex profile")
        return suggestions
    
    def _get_fallback_rules(self, table_name: str) -> List[Dict]:
        """Fallback rules when Dataplex is not available"""
        base_rules = [
            {
                "rule_type": "completeness",
                "column": "various",
                "issue": "Missing critical fields",
                "suggested_sql": f"SELECT * FROM `{table_name}` WHERE 1=0 LIMIT 200",  # Template
                "confidence": 0.5,
                "source": "fallback"
            }
        ]
        return base_rules
    
    # ============================================
    # DATA QUALITY SCORE FROM DATAPLEX
    # ============================================
    
    def calculate_dq_score_from_profile(self, table_name: str) -> Optional[Dict]:
        """
        Calculate data quality score using Dataplex profile data
        
        Args:
            table_name: Table name
            
        Returns:
            Dict with DQ scores
        """
        profile = self.get_data_profile(table_name)
        
        if not profile:
            return None
        
        # Calculate completeness score
        null_ratios = [col["profile"].get("null_ratio", 0) for col in profile.get("columns", [])]
        completeness_score = 1 - (sum(null_ratios) / len(null_ratios)) if null_ratios else 1.0
        
        # Calculate consistency score (placeholder - would need more data)
        consistency_score = 0.95  # Assume high consistency
        
        # Overall score
        overall_score = (completeness_score * 0.6 + consistency_score * 0.4)
        
        return {
            "table": table_name,
            "completeness": completeness_score,
            "consistency": consistency_score,
            "overall": overall_score,
            "row_count": profile.get("row_count", 0),
            "column_count": len(profile.get("columns", [])),
            "source": "dataplex"
        }
    
    # ============================================
    # UTILITY
    # ============================================
    
    def is_available(self) -> bool:
        """Check if Dataplex is available and configured"""
        return self.available

# Global instance
dataplex = DataplexIntegration()

