"""
Enhanced Metrics Agent
Calculates 5 DQ dimensions and ROI/cost-of-inaction
"""
from typing import Dict, List, Optional
from agent.tools import run_bq_query
from backend.config import config
from backend.enhancements import save_metrics_snapshot
from datetime import datetime
import json

class MetricsAgent:
    """
    Metrics Agent for calculating comprehensive data quality KPIs
    Covers 5 dimensions: Completeness, Validity, Consistency, Accuracy, Timeliness
    """
    
    def __init__(self):
        self.project = config.PROJECT_ID
        self.dataset = config.DATASET
    
    # ============================================
    # DIMENSION 1: COMPLETENESS
    # ============================================
    
    def calculate_completeness(self) -> Dict:
        """
        Calculate completeness percentage for critical fields
        
        Returns:
            Dict with completeness scores per field and overall
        """
        # Customers table
        customer_sql = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNTIF(CUS_DOB IS NOT NULL) as dob_complete,
            COUNTIF(email IS NOT NULL) as email_complete,
            COUNTIF(phone IS NOT NULL) as phone_complete,
            COUNTIF(CUS_FORNAME IS NOT NULL) as forename_complete,
            COUNTIF(CUS_SURNAME IS NOT NULL) as surname_complete
        FROM `{config.CUSTOMERS_TABLE}`
        """
        
        df = run_bq_query(self.project, customer_sql)
        row = df.iloc[0]
        
        total = row['total_records']
        if total == 0:
            return {"overall": 0.0, "by_field": {}}
        
        by_field = {
            "dob": row['dob_complete'] / total,
            "email": row['email_complete'] / total,
            "phone": row['phone_complete'] / total,
            "forename": row['forename_complete'] / total,
            "surname": row['surname_complete'] / total
        }
        
        overall = sum(by_field.values()) / len(by_field)
        
        return {
            "dimension": "completeness",
            "overall": round(overall, 4),
            "by_field": by_field,
            "total_records": int(total),
            "critical_fields_count": len(by_field)
        }
    
    # ============================================
    # DIMENSION 2: VALIDITY
    # ============================================
    
    def calculate_validity(self) -> Dict:
        """
        Calculate validity percentage (format/type correctness)
        
        Returns:
            Dict with validity scores
        """
        # Check email format validity
        email_sql = f"""
        SELECT 
            COUNT(*) as total_emails,
            COUNTIF(REGEXP_CONTAINS(email, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$')) as valid_emails
        FROM `{config.CUSTOMERS_TABLE}`
        WHERE email IS NOT NULL
        """
        
        # Check date validity (not future, not too old)
        date_sql = f"""
        SELECT 
            COUNT(*) as total_dates,
            COUNTIF(CUS_DOB <= CURRENT_DATE() AND CUS_DOB >= '1900-01-01') as valid_dates
        FROM `{config.CUSTOMERS_TABLE}`
        WHERE CUS_DOB IS NOT NULL
        """
        
        # Check amount validity (non-negative)
        amount_sql = f"""
        SELECT 
            COUNT(*) as total_amounts,
            COUNTIF(holding_amount >= 0 AND POLI_GROSS_PMT >= 0) as valid_amounts
        FROM `{config.HOLDINGS_TABLE}`
        """
        
        email_df = run_bq_query(self.project, email_sql)
        date_df = run_bq_query(self.project, date_sql)
        amount_df = run_bq_query(self.project, amount_sql)
        
        validities = []
        
        # Email validity
        if email_df.iloc[0]['total_emails'] > 0:
            email_validity = email_df.iloc[0]['valid_emails'] / email_df.iloc[0]['total_emails']
            validities.append(email_validity)
        
        # Date validity
        if date_df.iloc[0]['total_dates'] > 0:
            date_validity = date_df.iloc[0]['valid_dates'] / date_df.iloc[0]['total_dates']
            validities.append(date_validity)
        
        # Amount validity
        if amount_df.iloc[0]['total_amounts'] > 0:
            amount_validity = amount_df.iloc[0]['valid_amounts'] / amount_df.iloc[0]['total_amounts']
            validities.append(amount_validity)
        
        overall = sum(validities) / len(validities) if validities else 0.0
        
        return {
            "dimension": "validity",
            "overall": round(overall, 4),
            "by_check": {
                "email_format": round(validities[0], 4) if len(validities) > 0 else 0,
                "date_range": round(validities[1], 4) if len(validities) > 1 else 0,
                "amount_positive": round(validities[2], 4) if len(validities) > 2 else 0
            }
        }
    
    # ============================================
    # DIMENSION 3: CONSISTENCY
    # ============================================
    
    def calculate_consistency(self) -> Dict:
        """
        Calculate consistency (no duplicates, referential integrity)
        
        Returns:
            Dict with consistency scores
        """
        # Check for duplicate customer IDs
        duplicate_sql = f"""
        SELECT 
            COUNT(*) as total_customers,
            COUNT(DISTINCT CUS_ID) as unique_customers
        FROM `{config.CUSTOMERS_TABLE}`
        """
        
        # Check referential integrity (orphaned holdings)
        integrity_sql = f"""
        SELECT 
            COUNT(*) as total_holdings,
            COUNTIF(c.CUS_ID IS NOT NULL) as valid_references
        FROM `{config.HOLDINGS_TABLE}` h
        LEFT JOIN `{config.CUSTOMERS_TABLE}` c
          ON h.customer_id = c.CUS_ID
        """
        
        dup_df = run_bq_query(self.project, duplicate_sql)
        int_df = run_bq_query(self.project, integrity_sql)
        
        scores = []
        
        # No duplicates score
        total_cust = dup_df.iloc[0]['total_customers']
        unique_cust = dup_df.iloc[0]['unique_customers']
        if total_cust > 0:
            no_duplicates_score = unique_cust / total_cust
            scores.append(no_duplicates_score)
        
        # Referential integrity score
        total_hold = int_df.iloc[0]['total_holdings']
        valid_refs = int_df.iloc[0]['valid_references']
        if total_hold > 0:
            integrity_score = valid_refs / total_hold
            scores.append(integrity_score)
        
        overall = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "dimension": "consistency",
            "overall": round(overall, 4),
            "by_check": {
                "no_duplicates": round(scores[0], 4) if len(scores) > 0 else 0,
                "referential_integrity": round(scores[1], 4) if len(scores) > 1 else 0
            },
            "duplicate_count": int(total_cust - unique_cust),
            "orphaned_count": int(total_hold - valid_refs)
        }
    
    # ============================================
    # DIMENSION 4: ACCURACY
    # ============================================
    
    def calculate_accuracy(self) -> Dict:
        """
        Calculate accuracy (within expected ranges, no outliers)
        
        Returns:
            Dict with accuracy scores
        """
        # Check for statistical outliers in holdings
        outlier_sql = f"""
        WITH stats AS (
            SELECT 
                AVG(holding_amount) as mean_val,
                STDDEV(holding_amount) as std_val,
                COUNT(*) as total
            FROM `{config.HOLDINGS_TABLE}`
            WHERE holding_amount IS NOT NULL
        )
        SELECT 
            s.total,
            COUNTIF(ABS(h.holding_amount - s.mean_val) / NULLIF(s.std_val, 0) <= 3) as within_3_std
        FROM `{config.HOLDINGS_TABLE}` h, stats s
        WHERE h.holding_amount IS NOT NULL
        """
        
        df = run_bq_query(self.project, outlier_sql)
        
        if df.iloc[0]['total'] > 0:
            accuracy_score = df.iloc[0]['within_3_std'] / df.iloc[0]['total']
        else:
            accuracy_score = 0.0
        
        return {
            "dimension": "accuracy",
            "overall": round(accuracy_score, 4),
            "by_check": {
                "no_outliers_3std": round(accuracy_score, 4)
            },
            "outlier_count": int(df.iloc[0]['total'] - df.iloc[0]['within_3_std'])
        }
    
    # ============================================
    # DIMENSION 5: TIMELINESS
    # ============================================
    
    def calculate_timeliness(self) -> Dict:
        """
        Calculate timeliness (data freshness, recent updates)
        
        Returns:
            Dict with timeliness scores
        """
        # Check data freshness (records updated within last 365 days)
        freshness_sql = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNTIF(DATE_DIFF(CURRENT_DATE(), DATE(created_ts), DAY) <= 365) as recent_records
        FROM `{config.HOLDINGS_TABLE}`
        WHERE created_ts IS NOT NULL
        """
        
        df = run_bq_query(self.project, freshness_sql)
        
        if df.iloc[0]['total_records'] > 0:
            timeliness_score = df.iloc[0]['recent_records'] / df.iloc[0]['total_records']
        else:
            timeliness_score = 0.0
        
        stale_count = int(df.iloc[0]['total_records'] - df.iloc[0]['recent_records'])
        
        return {
            "dimension": "timeliness",
            "overall": round(timeliness_score, 4),
            "by_check": {
                "within_1_year": round(timeliness_score, 4)
            },
            "stale_count": stale_count,
            "freshness_threshold_days": 365
        }
    
    # ============================================
    # OVERALL DQ SCORE
    # ============================================
    
    def calculate_overall_dq_score(self) -> Dict:
        """
        Calculate overall data quality score across all 5 dimensions
        
        Returns:
            Dict with all dimensions and overall score
        """
        print("📊 Calculating 5D Data Quality Metrics...")
        
        completeness = self.calculate_completeness()
        validity = self.calculate_validity()
        consistency = self.calculate_consistency()
        accuracy = self.calculate_accuracy()
        timeliness = self.calculate_timeliness()
        
        # Weighted average (can be customized)
        weights = {
            "completeness": 0.25,
            "validity": 0.25,
            "consistency": 0.20,
            "accuracy": 0.20,
            "timeliness": 0.10
        }
        
        overall_score = (
            completeness["overall"] * weights["completeness"] +
            validity["overall"] * weights["validity"] +
            consistency["overall"] * weights["consistency"] +
            accuracy["overall"] * weights["accuracy"] +
            timeliness["overall"] * weights["timeliness"]
        )
        
        result = {
            "overall_dq_score": round(overall_score, 4),
            "grade": self._score_to_grade(overall_score),
            "dimensions": {
                "completeness": completeness,
                "validity": validity,
                "consistency": consistency,
                "accuracy": accuracy,
                "timeliness": timeliness
            },
            "weights": weights,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Save to metrics history
        metrics_flat = {
            "overall_dq_score": overall_score,
            "completeness": completeness["overall"],
            "validity": validity["overall"],
            "consistency": consistency["overall"],
            "accuracy": accuracy["overall"],
            "timeliness": timeliness["overall"]
        }
        save_metrics_snapshot(metrics_flat, "5d_calculation")
        
        return result
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.85:
            return "B+"
        elif score >= 0.80:
            return "B"
        elif score >= 0.75:
            return "C+"
        elif score >= 0.70:
            return "C"
        elif score >= 0.60:
            return "D"
        else:
            return "F"
    
    # ============================================
    # ROI & COST OF INACTION
    # ============================================
    
    def calculate_roi_and_cost(self, issues_count: int = None, 
                               remediated_count: int = 0) -> Dict:
        """
        Calculate ROI and cost of inaction
        
        Args:
            issues_count: Total issues detected (fetches from DB if None)
            remediated_count: Number of issues remediated
            
        Returns:
            Dict with ROI metrics
        """
        # Get issues count if not provided
        if issues_count is None:
            issues_sql = f"SELECT COUNT(*) as cnt FROM `{config.ISSUES_TABLE}`"
            df = run_bq_query(self.project, issues_sql)
            issues_count = int(df.iloc[0]['cnt'])
        
        # Assumptions (can be customized based on business context)
        COST_PER_ISSUE_MANUAL = 50  # $50 per issue to fix manually
        COST_PER_ISSUE_AUTOMATED = 2  # $2 per issue fixed by automation
        AVG_BUSINESS_IMPACT_PER_ISSUE = 500  # $500 potential loss per unresolved issue
        TIME_MANUAL_HOURS = 0.5  # 30 minutes per issue manually
        TIME_AUTOMATED_HOURS = 0.05  # 3 minutes per issue automated
        
        # Calculate costs
        manual_cost = issues_count * COST_PER_ISSUE_MANUAL
        automated_cost = issues_count * COST_PER_ISSUE_AUTOMATED
        cost_savings = manual_cost - automated_cost
        
        # Calculate time savings
        manual_time = issues_count * TIME_MANUAL_HOURS
        automated_time = issues_count * TIME_AUTOMATED_HOURS
        time_saved = manual_time - automated_time
        
        # Cost of inaction (unresolved issues)
        unresolved_issues = issues_count - remediated_count
        cost_of_inaction = unresolved_issues * AVG_BUSINESS_IMPACT_PER_ISSUE
        
        # ROI calculation
        investment = automated_cost  # Cost of automation
        returns = cost_savings + (remediated_count * AVG_BUSINESS_IMPACT_PER_ISSUE * 0.1)  # Savings + prevented losses
        roi_percentage = (returns / investment * 100) if investment > 0 else 0
        
        # Payback period (months)
        monthly_savings = cost_savings / 12  # Assuming annual issue rate
        payback_months = investment / monthly_savings if monthly_savings > 0 else float('inf')
        
        return {
            "issues_detected": issues_count,
            "issues_remediated": remediated_count,
            "issues_remaining": unresolved_issues,
            "costs": {
                "manual_approach": manual_cost,
                "automated_approach": automated_cost,
                "savings": cost_savings,
                "currency": "USD"
            },
            "time": {
                "manual_hours": round(manual_time, 2),
                "automated_hours": round(automated_time, 2),
                "saved_hours": round(time_saved, 2),
                "saved_days": round(time_saved / 8, 2)
            },
            "cost_of_inaction": {
                "total": cost_of_inaction,
                "per_issue": AVG_BUSINESS_IMPACT_PER_ISSUE,
                "description": "Estimated business impact of unresolved issues"
            },
            "roi": {
                "percentage": round(roi_percentage, 2),
                "investment": investment,
                "returns": returns,
                "payback_months": round(payback_months, 1) if payback_months != float('inf') else "N/A"
            },
            "materiality": self._calculate_materiality(issues_count, cost_of_inaction)
        }
    
    def _calculate_materiality(self, issues_count: int, cost_of_inaction: float) -> str:
        """Determine materiality level"""
        if cost_of_inaction > 100000 or issues_count > 1000:
            return "CRITICAL"
        elif cost_of_inaction > 50000 or issues_count > 500:
            return "HIGH"
        elif cost_of_inaction > 10000 or issues_count > 100:
            return "MEDIUM"
        else:
            return "LOW"
    
    # ============================================
    # COMPREHENSIVE REPORT
    # ============================================
    
    def generate_full_report(self) -> Dict:
        """
        Generate comprehensive DQ report with all metrics
        
        Returns:
            Complete report dict
        """
        print("📈 Generating comprehensive DQ report...")
        
        # Calculate 5D metrics
        dq_metrics = self.calculate_overall_dq_score()
        
        # Calculate ROI
        roi_metrics = self.calculate_roi_and_cost()
        
        # Get issue breakdown
        issues_sql = f"""
        SELECT 
            rule_id,
            severity,
            COUNT(*) as issue_count
        FROM `{config.ISSUES_TABLE}`
        GROUP BY rule_id, severity
        ORDER BY issue_count DESC
        """
        
        try:
            issues_df = run_bq_query(self.project, issues_sql)
            issues_breakdown = issues_df.to_dict(orient='records')
        except:
            issues_breakdown = []
        
        report = {
            "report_type": "comprehensive_dq_report",
            "generated_at": datetime.utcnow().isoformat(),
            "data_quality_metrics": dq_metrics,
            "roi_analysis": roi_metrics,
            "issues_breakdown": issues_breakdown,
            "recommendations": self._generate_recommendations(dq_metrics, roi_metrics)
        }
        
        return report
    
    def _generate_recommendations(self, dq_metrics: Dict, roi_metrics: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        dims = dq_metrics["dimensions"]
        
        # Completeness recommendations
        if dims["completeness"]["overall"] < 0.80:
            recommendations.append(
                "🔴 CRITICAL: Completeness is below 80%. Implement mandatory field validation."
            )
        elif dims["completeness"]["overall"] < 0.90:
            recommendations.append(
                "🟡 MEDIUM: Improve completeness by adding data entry prompts."
            )
        
        # Validity recommendations
        if dims["validity"]["overall"] < 0.85:
            recommendations.append(
                "🔴 CRITICAL: Validity issues detected. Add format validation at input."
            )
        
        # Consistency recommendations
        if dims["consistency"]["duplicate_count"] > 10:
            recommendations.append(
                f"🟡 MEDIUM: {dims['consistency']['duplicate_count']} duplicates found. Implement deduplication process."
            )
        
        # ROI recommendations
        if roi_metrics["cost_of_inaction"]["total"] > 50000:
            recommendations.append(
                f"🔴 CRITICAL: Cost of inaction is ${roi_metrics['cost_of_inaction']['total']:,.0f}. Prioritize remediation immediately."
            )
        
        if roi_metrics["roi"]["percentage"] > 200:
            recommendations.append(
                f"🟢 POSITIVE: ROI is {roi_metrics['roi']['percentage']:.0f}%. Expand automation to other datasets."
            )
        
        return recommendations

# Global metrics agent instance
metrics = MetricsAgent()

