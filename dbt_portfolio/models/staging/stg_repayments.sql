SELECT payment_id,
  loan_id,
  due_date,
  SAFE_CAST(NULLIF(paid_date, '') AS date) AS paid_date,
  NULLIF(paid_date, '') IS NOT NULL AS is_paid,
  amount_due,
  amount_paid
FROM { { ref('repayments') } }