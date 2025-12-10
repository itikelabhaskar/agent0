-- Rule versioning table
CREATE TABLE IF NOT EXISTS `hackathon-practice-480508.dev_dataset.rules_history` (
  version_id STRING,
  rule_id STRING,
  version_number INT64,
  sql_snippet STRING,
  rule_text STRING,
  created_by STRING,
  created_ts TIMESTAMP,
  change_reason STRING,
  is_active BOOL
);

-- Audit trail table
CREATE TABLE IF NOT EXISTS `hackathon-practice-480508.dev_dataset.audit_log` (
  audit_id STRING,
  user_id STRING,
  user_email STRING,
  action_type STRING,  -- 'create_rule', 'run_rule', 'apply_fix', 'rollback', etc.
  action_target STRING,  -- rule_id, issue_id, etc.
  action_details STRING,  -- JSON string with details
  timestamp TIMESTAMP,
  ip_address STRING,
  status STRING  -- 'success', 'failed'
);

-- Users table for RBAC
CREATE TABLE IF NOT EXISTS `hackathon-practice-480508.dev_dataset.users` (
  user_id STRING,
  email STRING,
  full_name STRING,
  role STRING,  -- 'business_user', 'engineer', 'admin'
  created_ts TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOL
);

-- Metrics history table for trend tracking
CREATE TABLE IF NOT EXISTS `hackathon-practice-480508.dev_dataset.metrics_history` (
  metric_id STRING,
  metric_name STRING,
  metric_value FLOAT64,
  metric_details STRING,  -- JSON string
  recorded_ts TIMESTAMP,
  source STRING
);

-- Remediation patches table for export
CREATE TABLE IF NOT EXISTS `hackathon-practice-480508.dev_dataset.remediation_patches` (
  patch_id STRING,
  issue_id STRING,
  rule_id STRING,
  before_data STRING,  -- JSON
  after_data STRING,   -- JSON
  applied_by STRING,
  applied_ts TIMESTAMP,
  status STRING  -- 'pending', 'applied', 'rolled_back'
);

