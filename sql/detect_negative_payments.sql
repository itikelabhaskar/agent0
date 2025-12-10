-- SQL template to detect negative payment amounts
-- BigQuery compatible

SELECT
  payment_id,
  customer_id,
  payment_amount,
  payment_date,
  'Negative Payment' as issue_type
FROM `your_project.your_dataset.payments`
WHERE payment_amount < 0
