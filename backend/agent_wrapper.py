# Agent wrapper for FastAPI integration
# Wraps the ADK agent for API calls

import os
from agent.tools import detect_missing_dob

def run_identifier(project, table):
    """
    Run data quality identifier on specified table

    Args:
        project (str): GCP project ID
        table (str): Full table reference in format 'dataset.table' or 'project.dataset.table'

    Returns:
        dict: Results of the data quality check
    """
    try:
        # Parse the table parameter
        # Support both 'dataset.table' and 'project.dataset.table' formats
        parts = table.split('.')
        
        if len(parts) == 2:
            # Format: dataset.table
            dataset, table_name = parts
        elif len(parts) == 3:
            # Format: project.dataset.table
            _, dataset, table_name = parts
        else:
            raise ValueError("Table parameter must be in format 'dataset.table' or 'project.dataset.table'")

        # Run the missing DOB detection on BigQuery
        results = detect_missing_dob(project, dataset, table_name)

        return {
            "status": "success",
            "check_type": "missing_dob",
            "results": results,
            "count": len(results),
            "source": "bigquery",
            "table": f"{project}.{dataset}.{table_name}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "table": table
        }


def suggest_treatments_for_missing_dob(issue_record):
    """
    Suggest treatments for missing DOB issues

    Args:
        issue_record (dict): The issue record with customer information

    Returns:
        list: List of treatment suggestions
    """
    suggestions = []

    # Suggestion 1: Impute from other records (if same email/name exists)
    suggestions.append({
        "suggestion_id": "T1",
        "description": "Impute DOB from other customer records with matching email or name",
        "confidence": 0.7,
        "action_type": "impute",
        "requires_approval": True
    })

    # Suggestion 2: Flag for manual review/customer outreach
    suggestions.append({
        "suggestion_id": "T2",
        "description": "Flag record for customer outreach to collect missing DOB",
        "confidence": 0.6,
        "action_type": "flag",
        "requires_approval": True
    })

    # Suggestion 3: Business decision to leave blank
    suggestions.append({
        "suggestion_id": "T3",
        "description": "Leave DOB blank - business process allows missing values",
        "confidence": 0.3,
        "action_type": "accept",
        "requires_approval": False
    })

    return suggestions


def apply_fix(payload):
    """
    Apply a selected fix (remediation action)

    Args:
        payload (dict): Contains fix details and apply_mode

    Returns:
        dict: Result of the fix application
    """
    fix = payload.get("fix", {})
    apply_mode = payload.get("apply_mode", "dryrun")

    if apply_mode == "dryrun":
        # Return what would change without actually applying
        return {
            "status": "dryrun",
            "diff": {
                "before": {"dob": None},
                "after": {"dob": "would_be_imputed_or_flagged"},
                "action": fix.get("description", "Unknown action")
            }
        }
    else:
        # Apply the fix - for now, just log it (would write to cleaned table in production)
        return {
            "status": "applied",
            "details": f"Applied fix {fix.get('suggestion_id')} to customer {fix.get('customer_id', 'unknown')}",
            "timestamp": "2025-12-09T10:35:00Z"  # Would use actual timestamp
        }
