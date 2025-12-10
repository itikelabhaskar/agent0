"""
Create enhancement tables for rule versioning, audit trails, RBAC, and metrics history
"""
from google.cloud import bigquery
import sys

def create_tables():
    project_id = "hackathon-practice-480508"
    dataset_id = "dev_dataset"
    
    client = bigquery.Client(project=project_id)
    
    tables_sql = [
        # Rule versioning
        f"""
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.rules_history` (
          version_id STRING,
          rule_id STRING,
          version_number INT64,
          sql_snippet STRING,
          rule_text STRING,
          created_by STRING,
          created_ts TIMESTAMP,
          change_reason STRING,
          is_active BOOL
        )
        """,
        # Audit trail
        f"""
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.audit_log` (
          audit_id STRING,
          user_id STRING,
          user_email STRING,
          action_type STRING,
          action_target STRING,
          action_details STRING,
          timestamp TIMESTAMP,
          ip_address STRING,
          status STRING
        )
        """,
        # Users for RBAC
        f"""
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.users` (
          user_id STRING,
          email STRING,
          full_name STRING,
          role STRING,
          created_ts TIMESTAMP,
          last_login TIMESTAMP,
          is_active BOOL
        )
        """,
        # Metrics history
        f"""
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.metrics_history` (
          metric_id STRING,
          metric_name STRING,
          metric_value FLOAT64,
          metric_details STRING,
          recorded_ts TIMESTAMP,
          source STRING
        )
        """,
        # Remediation patches
        f"""
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.remediation_patches` (
          patch_id STRING,
          issue_id STRING,
          rule_id STRING,
          before_data STRING,
          after_data STRING,
          applied_by STRING,
          applied_ts TIMESTAMP,
          status STRING
        )
        """
    ]
    
    for i, sql in enumerate(tables_sql, 1):
        try:
            job = client.query(sql)
            job.result()
            print(f"✅ Table {i}/5 created successfully")
        except Exception as e:
            print(f"❌ Error creating table {i}: {e}")
            return False
    
    # Insert default admin user
    try:
        admin_sql = f"""
        INSERT INTO `{project_id}.{dataset_id}.users` 
        (user_id, email, full_name, role, created_ts, last_login, is_active)
        VALUES
        ('admin-001', 'mylilbeast1823@gmail.com', 'Admin User', 'admin', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), TRUE)
        """
        job = client.query(admin_sql)
        job.result()
        print("✅ Default admin user created")
    except Exception as e:
        print(f"⚠️ Admin user may already exist or error: {e}")
    
    print("\n✅ All enhancement tables created successfully!")
    return True

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)

