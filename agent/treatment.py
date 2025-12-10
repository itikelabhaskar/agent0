"""
Enhanced Treatment Agent
Suggests remediation strategies with root-cause analysis
"""
from typing import Dict, List, Optional
from backend.knowledge_bank import kb
from backend.config import config
from agent.tools import run_bq_query
import uuid

class TreatmentAgent:
    """
    Treatment Agent for suggesting data quality remediation strategies
    Uses knowledge bank for historical success rates and root-cause analysis
    """
    
    def __init__(self):
        self.kb = kb
        self.project = config.PROJECT_ID
    
    # ============================================
    # ROOT CAUSE ANALYSIS
    # ============================================
    
    def analyze_root_cause(self, issue: Dict) -> List[Dict]:
        """
        Analyze potential root causes for an issue
        
        Args:
            issue: Issue dict with issue_type, data, etc.
            
        Returns:
            List of potential root causes with confidence scores
        """
        issue_type = issue.get("issue_type", "unknown")
        
        # Check knowledge bank for known root causes
        known_causes = self.kb.get_root_causes(issue_type)
        
        if known_causes:
            return known_causes
        
        # Apply heuristics for common issues
        root_causes = []
        
        if issue_type == "missing_dob":
            root_causes.append({
                "root_cause": "Data entry incomplete during customer onboarding",
                "confidence": 0.7,
                "evidence": {"common_pattern": "new_customers"}
            })
            root_causes.append({
                "root_cause": "Legacy system migration data loss",
                "confidence": 0.5,
                "evidence": {"common_pattern": "old_records"}
            })
            root_causes.append({
                "root_cause": "Privacy concerns - customer refused to provide",
                "confidence": 0.3,
                "evidence": {"common_pattern": "specific_demographics"}
            })
        
        elif issue_type == "negative_amount":
            root_causes.append({
                "root_cause": "Incorrect sign in payment processing",
                "confidence": 0.8,
                "evidence": {"pattern": "systematic_error"}
            })
            root_causes.append({
                "root_cause": "Refund/chargeback recorded incorrectly",
                "confidence": 0.6,
                "evidence": {"pattern": "transaction_type"}
            })
        
        elif issue_type == "invalid_email":
            root_causes.append({
                "root_cause": "No email validation in data entry form",
                "confidence": 0.9,
                "evidence": {"pattern": "input_validation_missing"}
            })
            root_causes.append({
                "root_cause": "Placeholder/test data in production",
                "confidence": 0.4,
                "evidence": {"pattern": "test_accounts"}
            })
        
        elif issue_type == "duplicate":
            root_causes.append({
                "root_cause": "No unique constraint on database",
                "confidence": 0.8,
                "evidence": {"pattern": "database_design"}
            })
            root_causes.append({
                "root_cause": "Multiple system integrations creating duplicates",
                "confidence": 0.6,
                "evidence": {"pattern": "integration_issue"}
            })
        
        elif issue_type == "orphaned_record":
            root_causes.append({
                "root_cause": "No foreign key constraints",
                "confidence": 0.7,
                "evidence": {"pattern": "referential_integrity"}
            })
            root_causes.append({
                "root_cause": "Parent record deleted without cascade",
                "confidence": 0.6,
                "evidence": {"pattern": "deletion_policy"}
            })
        
        else:
            # Generic root cause
            root_causes.append({
                "root_cause": "Data quality check not implemented",
                "confidence": 0.5,
                "evidence": {"pattern": "prevention_gap"}
            })
        
        # Store for future reference
        if root_causes:
            self.kb.add_root_cause(issue_type, root_causes[0]["root_cause"], root_causes[0]["evidence"])
        
        return root_causes
    
    # ============================================
    # TREATMENT SUGGESTION
    # ============================================
    
    def suggest_treatments(self, issue: Dict, root_causes: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Suggest treatment strategies for an issue
        
        Args:
            issue: Issue dict
            root_causes: Optional list of root causes from analysis
            
        Returns:
            List of treatment suggestions ranked by confidence/success rate
        """
        issue_type = issue.get("issue_type", "unknown")
        
        # Check knowledge bank for existing treatments
        kb_treatments = self.kb.get_treatments_for_issue(issue_type)
        
        if kb_treatments:
            # Use knowledge bank treatments with success rates
            treatments = []
            for t in kb_treatments:
                treatments.append({
                    "treatment_id": t['treatment_id'],
                    "description": t['description'],
                    "confidence": float(t.get('confidence', 0.5)),
                    "success_rate": float(t.get('success_rate', 0.0)),
                    "cost": t.get('cost', 'low'),
                    "approval_required": t.get('approval_required', 'true').lower() == 'true',
                    "source": "knowledge_bank"
                })
            
            # Sort by success rate
            treatments.sort(key=lambda x: x['success_rate'], reverse=True)
            return treatments[:5]
        
        # Generate treatments based on issue type
        treatments = []
        
        if issue_type == "missing_dob":
            treatments = [
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Impute from records with same email/phone (ML-based similarity)",
                    "confidence": 0.75,
                    "success_rate": 0.0,
                    "cost": "medium",
                    "approval_required": True,
                    "steps": ["Find similar records", "Calculate average/mode DOB", "Apply with validation"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Request from customer via email/SMS campaign",
                    "confidence": 0.60,
                    "success_rate": 0.0,
                    "cost": "high",
                    "approval_required": False,
                    "steps": ["Generate outreach list", "Send automated request", "Update on response"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Mark as incomplete and flag for manual review",
                    "confidence": 0.90,
                    "success_rate": 0.0,
                    "cost": "low",
                    "approval_required": False,
                    "steps": ["Add flag to record", "Create manual review ticket"]
                }
            ]
        
        elif issue_type == "negative_amount":
            treatments = [
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Convert to absolute value (if systematic sign error)",
                    "confidence": 0.70,
                    "success_rate": 0.0,
                    "cost": "low",
                    "approval_required": True,
                    "steps": ["Verify pattern", "Apply ABS() function", "Audit results"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Investigate and reclassify as refund/chargeback",
                    "confidence": 0.60,
                    "success_rate": 0.0,
                    "cost": "medium",
                    "approval_required": True,
                    "steps": ["Check transaction type", "Reclassify if refund", "Update transaction category"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Mark for financial audit and manual correction",
                    "confidence": 0.85,
                    "success_rate": 0.0,
                    "cost": "high",
                    "approval_required": False,
                    "steps": ["Flag for audit", "Create ticket for finance team"]
                }
            ]
        
        elif issue_type == "invalid_email":
            treatments = [
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Attempt auto-correction (common typos: @gmai.com → @gmail.com)",
                    "confidence": 0.65,
                    "success_rate": 0.0,
                    "cost": "low",
                    "approval_required": True,
                    "steps": ["Apply common typo fixes", "Validate format", "Update if valid"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Request email update from customer",
                    "confidence": 0.75,
                    "success_rate": 0.0,
                    "cost": "medium",
                    "approval_required": False,
                    "steps": ["Send verification request", "Provide update link", "Confirm new email"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Clear invalid email and mark for re-entry",
                    "confidence": 0.50,
                    "success_rate": 0.0,
                    "cost": "low",
                    "approval_required": True,
                    "steps": ["Set email to NULL", "Flag for customer contact"]
                }
            ]
        
        elif issue_type == "duplicate":
            treatments = [
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Merge duplicate records keeping most recent data",
                    "confidence": 0.70,
                    "success_rate": 0.0,
                    "cost": "medium",
                    "approval_required": True,
                    "steps": ["Identify master record", "Merge fields", "Archive duplicates"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Manual review to determine correct record",
                    "confidence": 0.90,
                    "success_rate": 0.0,
                    "cost": "high",
                    "approval_required": False,
                    "steps": ["Create review task", "Compare records", "Mark winner", "Delete losers"]
                }
            ]
        
        elif issue_type == "orphaned_record":
            treatments = [
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Archive orphaned record to historical table",
                    "confidence": 0.80,
                    "success_rate": 0.0,
                    "cost": "low",
                    "approval_required": True,
                    "steps": ["Move to archive", "Add orphan_flag", "Log for audit"]
                },
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Attempt to match with parent based on other fields",
                    "confidence": 0.50,
                    "success_rate": 0.0,
                    "cost": "medium",
                    "approval_required": True,
                    "steps": ["Fuzzy match on name/email", "Suggest parent", "Apply if high confidence"]
                }
            ]
        
        else:
            # Generic treatment
            treatments = [
                {
                    "treatment_id": f"T_{uuid.uuid4().hex[:6]}",
                    "description": "Flag for manual review",
                    "confidence": 0.70,
                    "success_rate": 0.0,
                    "cost": "low",
                    "approval_required": False,
                    "steps": ["Create ticket", "Assign to DQ team"]
                }
            ]
        
        # Save treatments to knowledge bank
        for treatment in treatments:
            self.kb.add_treatment(treatment)
        
        # Sort by confidence
        treatments.sort(key=lambda x: x['confidence'], reverse=True)
        
        return treatments
    
    # ============================================
    # FULL ANALYSIS
    # ============================================
    
    def analyze_and_suggest(self, issue: Dict) -> Dict:
        """
        Complete analysis: root cause + treatment suggestions
        
        Args:
            issue: Issue dict
            
        Returns:
            Dict with root_causes and treatments
        """
        root_causes = self.analyze_root_cause(issue)
        treatments = self.suggest_treatments(issue, root_causes)
        
        return {
            "issue": issue,
            "root_causes": root_causes,
            "treatments": treatments,
            "recommended_treatment": treatments[0] if treatments else None
        }

# Global treatment agent instance
treatment = TreatmentAgent()

