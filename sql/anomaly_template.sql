-- Generic SQL template for anomaly detection
-- BigQuery compatible

SELECT
  {columns}
FROM `{project}.{dataset}.{table}`
WHERE {conditions}
