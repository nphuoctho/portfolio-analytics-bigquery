SELECT loan_id,
  customer_id,
  amount,
  issue_date,
  DATE_TRUNC(issue_date, month) AS cohort_month,
  term_months,
  interest_rate,
  app_score,
  status
FROM { { ref('loans') } }