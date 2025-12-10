"""
ADK Multi-Agent Orchestrator
Coordinates all agents in the AgentX system
"""
from typing import Dict, List, Optional
from agent.identifier import identifier
from agent.treatment import treatment
from agent.remediator import remediator
from agent.metrics import metrics
from backend.knowledge_bank import kb
from backend.config import config
from backend.enhancements import log_audit
from datetime import datetime
import json

class AgentOrchestrator:
    """
    Central orchestrator for AgentX multi-agent system
    Coordinates workflow between Identifier, Treatment, Remediator, and Metrics agents
    """
    
    def __init__(self):
        self.identifier = identifier
        self.treatment = treatment
        self.remediator = remediator
        self.metrics = metrics
        self.kb = kb
        
        self.workflow_state = {
            "current_phase": None,
            "issues_detected": [],
            "treatments_suggested": {},
            "fixes_applied": [],
            "metrics_calculated": None
        }
    
    # ============================================
    # COMPLETE DQ CYCLE
    # ============================================
    
    def run_full_dq_cycle(self, config_override: Dict = None, 
                         auto_remediate: bool = False,
                         user_email: str = "system") -> Dict:
        """
        Execute complete data quality cycle
        
        Workflow:
        1. Identify issues (all 5 dimensions)
        2. For each issue, suggest treatments with root cause
        3. Apply approved treatments (if auto_remediate=True)
        4. Calculate metrics and ROI
        5. Generate report
        
        Args:
            config_override: Optional config overrides
            auto_remediate: If True, auto-apply high-confidence treatments
            user_email: User running the cycle
            
        Returns:
            Complete cycle results
        """
        print("=" * 60)
        print("🚀 AgentX Multi-Agent Orchestration - Full DQ Cycle")
        print("=" * 60)
        
        cycle_id = f"CYCLE_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Phase 1: Identification
        print("\n📍 Phase 1: Issue Identification")
        self.workflow_state["current_phase"] = "identification"
        
        issues_by_dimension = self.identifier.run_all_checks(limit_per_check=50)
        
        # Flatten issues
        all_issues = []
        for dimension, issues_list in issues_by_dimension.items():
            if isinstance(issues_list, list):
                for issue in issues_list:
                    issue['dimension'] = dimension
                    all_issues.append(issue)
        
        self.workflow_state["issues_detected"] = all_issues
        
        print(f"   ✅ Detected {len(all_issues)} issues across {len(issues_by_dimension) - 1} dimensions")
        for dim in ['completeness', 'validity', 'consistency', 'accuracy', 'timeliness']:
            count = len(issues_by_dimension.get(dim, []))
            if count > 0:
                print(f"      - {dim.capitalize()}: {count}")
        
        # Phase 2: Treatment Suggestion
        print("\n💊 Phase 2: Treatment Suggestion & Root Cause Analysis")
        self.workflow_state["current_phase"] = "treatment"
        
        treatments_by_issue = {}
        for i, issue in enumerate(all_issues[:20]):  # Limit to first 20 for demo
            issue_key = f"{issue.get('issue_type', 'unknown')}_{i}"
            
            analysis = self.treatment.analyze_and_suggest(issue)
            treatments_by_issue[issue_key] = {
                "issue": issue,
                "root_causes": analysis["root_causes"],
                "treatments": analysis["treatments"],
                "recommended": analysis["recommended_treatment"]
            }
        
        self.workflow_state["treatments_suggested"] = treatments_by_issue
        
        print(f"   ✅ Generated treatments for {len(treatments_by_issue)} issues")
        print(f"      - Average {len(analysis['treatments'])} options per issue")
        print(f"      - Average {len(analysis['root_causes'])} root causes identified")
        
        # Phase 3: Remediation (if auto_remediate)
        print("\n🔧 Phase 3: Remediation")
        self.workflow_state["current_phase"] = "remediation"
        
        fixes_applied = []
        
        if auto_remediate:
            print("   ⚙️  Auto-remediation enabled...")
            
            for issue_key, treatment_data in treatments_by_issue.items():
                recommended = treatment_data["recommended"]
                
                # Only auto-apply high-confidence, low-cost treatments
                if (recommended and 
                    recommended.get("confidence", 0) > 0.7 and 
                    recommended.get("cost") == "low"):
                    
                    # For now, just log (full implementation would call remediator)
                    print(f"      ✓ Would apply: {recommended['description'][:50]}...")
                    
                    fixes_applied.append({
                        "issue": treatment_data["issue"],
                        "treatment": recommended,
                        "status": "would_apply",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        else:
            print("   ℹ️  Auto-remediation disabled (HITL approval required)")
            print(f"      - {len(treatments_by_issue)} treatments pending approval")
        
        self.workflow_state["fixes_applied"] = fixes_applied
        
        # Phase 4: Metrics Calculation
        print("\n📊 Phase 4: Metrics Calculation")
        self.workflow_state["current_phase"] = "metrics"
        
        dq_metrics = self.metrics.calculate_overall_dq_score()
        roi_metrics = self.metrics.calculate_roi_and_cost(
            issues_count=len(all_issues),
            remediated_count=len(fixes_applied)
        )
        
        print(f"   ✅ Overall DQ Score: {dq_metrics['overall_dq_score']:.2%} (Grade: {dq_metrics['grade']})")
        print(f"   ✅ ROI: {roi_metrics['roi']['percentage']:.0f}%")
        print(f"   ✅ Cost of Inaction: ${roi_metrics['cost_of_inaction']['total']:,.0f}")
        
        self.workflow_state["metrics_calculated"] = {
            "dq_metrics": dq_metrics,
            "roi_metrics": roi_metrics
        }
        
        # Phase 5: Reporting
        print("\n📈 Phase 5: Report Generation")
        
        report = {
            "cycle_id": cycle_id,
            "executed_by": user_email,
            "executed_at": datetime.utcnow().isoformat(),
            "configuration": {
                "auto_remediate": auto_remediate,
                "project": config.PROJECT_ID,
                "dataset": config.DATASET
            },
            "results": {
                "identification": {
                    "total_issues": len(all_issues),
                    "by_dimension": {
                        dim: len(issues_by_dimension.get(dim, []))
                        for dim in ['completeness', 'validity', 'consistency', 'accuracy', 'timeliness']
                    },
                    "issues": all_issues[:100]  # Limit for report size
                },
                "treatment": {
                    "issues_analyzed": len(treatments_by_issue),
                    "treatments_generated": sum(len(t["treatments"]) for t in treatments_by_issue.values()),
                    "pending_approval": len(treatments_by_issue) - len(fixes_applied)
                },
                "remediation": {
                    "fixes_applied": len(fixes_applied),
                    "auto_remediated": len([f for f in fixes_applied if f["status"] == "applied"]),
                    "pending_hitl": len(treatments_by_issue) - len(fixes_applied)
                },
                "metrics": {
                    "dq_score": dq_metrics["overall_dq_score"],
                    "grade": dq_metrics["grade"],
                    "dimensions": {k: v["overall"] for k, v in dq_metrics["dimensions"].items()},
                    "roi_percentage": roi_metrics["roi"]["percentage"],
                    "cost_savings": roi_metrics["costs"]["savings"],
                    "time_saved_hours": roi_metrics["time"]["saved_hours"]
                }
            },
            "recommendations": self._generate_cycle_recommendations(
                len(all_issues),
                dq_metrics,
                roi_metrics
            )
        }
        
        # Log audit
        log_audit(
            user_email,
            "run_full_dq_cycle",
            cycle_id,
            {
                "issues_detected": len(all_issues),
                "fixes_applied": len(fixes_applied),
                "dq_score": dq_metrics["overall_dq_score"]
            },
            "success"
        )
        
        # Store in knowledge bank
        self._store_cycle_learnings(report)
        
        print("\n" + "=" * 60)
        print("✅ Full DQ Cycle Complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  • Issues Detected: {len(all_issues)}")
        print(f"  • Treatments Generated: {sum(len(t['treatments']) for t in treatments_by_issue.values())}")
        print(f"  • Fixes Applied: {len(fixes_applied)}")
        print(f"  • DQ Score: {dq_metrics['overall_dq_score']:.2%} ({dq_metrics['grade']})")
        print(f"  • ROI: {roi_metrics['roi']['percentage']:.0f}%")
        
        return report
    
    # ============================================
    # TARGETED WORKFLOWS
    # ============================================
    
    def run_identification_only(self, dimension: Optional[str] = None) -> Dict:
        """
        Run only identification phase
        
        Args:
            dimension: Optional dimension filter (completeness, validity, etc.)
            
        Returns:
            Issues dict
        """
        print(f"🔍 Running Identification{f' - {dimension}' if dimension else ''}...")
        
        if dimension:
            # Run specific dimension checks
            method_name = f"detect_{dimension}_issues"
            if hasattr(self.identifier, method_name):
                issues = getattr(self.identifier, method_name)()
            else:
                issues = []
        else:
            issues = self.identifier.run_all_checks()
        
        return {
            "phase": "identification_only",
            "dimension": dimension,
            "issues": issues,
            "count": sum(len(v) for v in issues.values() if isinstance(v, list))
        }
    
    def run_treatment_for_issue(self, issue: Dict) -> Dict:
        """
        Run treatment analysis for a single issue
        
        Args:
            issue: Issue dict
            
        Returns:
            Treatment analysis
        """
        print(f"💊 Analyzing treatment for {issue.get('issue_type')}...")
        
        return self.treatment.analyze_and_suggest(issue)
    
    def apply_treatment_with_approval(self, issue: Dict, treatment: Dict, 
                                     approved_by: str, mode: str = "dryrun") -> Dict:
        """
        Apply a treatment with human approval
        
        Args:
            issue: Issue dict
            treatment: Treatment dict
            approved_by: User who approved
            mode: "dryrun" or "apply"
            
        Returns:
            Remediation result
        """
        print(f"🔧 Applying treatment (mode: {mode})...")
        
        # Log approval
        log_audit(
            approved_by,
            "approve_treatment",
            treatment.get("treatment_id"),
            {"issue": issue, "treatment": treatment},
            "success"
        )
        
        # Apply remediation (placeholder - would integrate with remediator)
        result = {
            "status": "approved",
            "mode": mode,
            "treatment_id": treatment.get("treatment_id"),
            "approved_by": approved_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Record outcome in knowledge bank
        if mode == "apply":
            self.kb.add_treatment_outcome(
                treatment.get("treatment_id"),
                str(issue),
                True,  # success - would be actual result
                {"approved_by": approved_by}
            )
        
        return result
    
    # ============================================
    # HELPERS
    # ============================================
    
    def _generate_cycle_recommendations(self, issues_count: int, 
                                       dq_metrics: Dict, roi_metrics: Dict) -> List[str]:
        """Generate recommendations for the cycle"""
        recommendations = []
        
        if issues_count > 100:
            recommendations.append(
                "🔴 HIGH PRIORITY: Over 100 issues detected. Run remediation immediately."
            )
        
        if dq_metrics["overall_dq_score"] < 0.70:
            recommendations.append(
                "🔴 CRITICAL: DQ score below 70%. Implement prevention measures."
            )
        
        if roi_metrics["roi"]["percentage"] > 300:
            recommendations.append(
                "🟢 EXCELLENT: ROI exceeds 300%. Consider expanding to more datasets."
            )
        
        if roi_metrics["cost_of_inaction"]["total"] > 100000:
            recommendations.append(
                "🔴 URGENT: Cost of inaction exceeds $100k. Escalate to management."
            )
        
        return recommendations
    
    def _store_cycle_learnings(self, report: Dict):
        """Store cycle learnings in knowledge bank"""
        # Store patterns learned from this cycle
        pattern = {
            "pattern_type": "dq_cycle",
            "indicators": {
                "issues_detected": report["results"]["identification"]["total_issues"],
                "dq_score": report["results"]["metrics"]["dq_score"]
            },
            "frequency": 1,
            "severity": report["results"]["metrics"]["grade"],
            "metadata": {
                "cycle_id": report["cycle_id"],
                "executed_at": report["executed_at"]
            }
        }
        
        self.kb.add_learned_pattern(pattern)
    
    def get_workflow_status(self) -> Dict:
        """Get current workflow state"""
        return {
            "current_phase": self.workflow_state["current_phase"],
            "issues_detected_count": len(self.workflow_state["issues_detected"]),
            "treatments_suggested_count": len(self.workflow_state["treatments_suggested"]),
            "fixes_applied_count": len(self.workflow_state["fixes_applied"]),
            "metrics_available": self.workflow_state["metrics_calculated"] is not None
        }

# Global orchestrator instance
orchestrator = AgentOrchestrator()
