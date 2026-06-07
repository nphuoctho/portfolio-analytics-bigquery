SELECT customer_id,
  segment,
  join_date,
  credit_limit,
  credit_score
FROM {{ ref('customers') }}