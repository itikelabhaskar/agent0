-- SQL template to detect missing date of birth values
-- BigQuery compatible

SELECT
  customer_id,
  customer_name,
  'Missing DOB' as issue_type
FROM `your_project.your_dataset.customers`
WHERE date_of_birth IS NULL
  OR date_of_birth = ''
