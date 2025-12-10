# Agent wrapper for FastAPI integration
# Wraps the ADK agent for API calls

import os
from agent.tools import detect_missing_dob, read_local_csv

def run_identifier(project, table):
    """
    Run data quality identifier on specified table

    Args:
        project (str): GCP project ID
        table (str): Full table reference in format 'dataset.table'

    Returns:
        dict: Results of the data quality check
    """
    try:
        # For testing, use local CSV data instead of BigQuery
        # This allows us to test the API without needing BigQuery setup

        if table == "customers.sample":
            # Use local customers CSV for testing
            csv_path = os.path.join(os.path.dirname(__file__), "..", "fake_data", "customers_sample.csv")
            if os.path.exists(csv_path):
                data = read_local_csv(csv_path)
                # Simulate missing DOB detection
                import math
                missing_dob_records = []
                for record in data:
                    dob = record.get('date_of_birth', '')
                    # Handle NaN, None, empty strings, and whitespace
                    is_missing = (
                        dob is None or
                        (isinstance(dob, float) and math.isnan(dob)) or
                        str(dob).strip() == '' or
                        str(dob).lower() in ['nan', 'none', 'null']
                    )
                    if is_missing:
                        # Clean the record to remove NaN values for JSON serialization
                        clean_record = {}
                        for key, value in record.items():
                            if isinstance(value, float) and math.isnan(value):
                                clean_record[key] = None
                            else:
                                clean_record[key] = value
                        missing_dob_records.append(clean_record)
                return {
                    "status": "success",
                    "check_type": "missing_dob",
                    "results": missing_dob_records,
                    "count": len(missing_dob_records),
                    "source": "local_csv"
                }
            else:
                return {
                    "status": "error",
                    "message": f"CSV file not found: {csv_path}"
                }

        # Parse dataset and table from the table parameter for BigQuery
        if '.' not in table:
            raise ValueError("Table parameter must be in format 'dataset.table'")

        dataset, table_name = table.split('.', 1)

        # Run the missing DOB detection on BigQuery
        results = detect_missing_dob(project, dataset, table_name)

        return {
            "status": "success",
            "check_type": "missing_dob",
            "results": results,
            "count": len(results),
            "source": "bigquery"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
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
