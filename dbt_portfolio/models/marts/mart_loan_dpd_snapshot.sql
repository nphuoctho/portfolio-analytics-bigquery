-- DPD snapshot per loan as of var('as_of_date').
-- DPD = days past due of the OLDEST unpaid installment that is already due.
-- Loans with no overdue installment are kept (LEFT JOIN) with dpd = 0.
WITH overdue AS (
    -- installments already due by as_of but not yet paid
    SELECT
        loan_id,
        date_diff(date('{{ var("as_of_date") }}'), due_date, day) as dpd_days
    FROM {{ ref('stg_repayments') }}
    WHERE due_date <= date('{{ var("as_of_date") }}')   -- never look into the future
      AND NOT is_paid
),

worst AS (
    -- oldest unpaid installment per loan = the largest days-past-due
    SELECT
        loan_id,
        max(dpd_days) AS dpd
    FROM overdue
    GROUP BY loan_id
),

final AS (
    SELECT
        l.loan_id,
        c.segment,
        l.status,
        coalesce(w.dpd, 0) AS dpd,
        CASE
            WHEN coalesce(w.dpd, 0) = 0 THEN '0'
            WHEN w.dpd <= 30            THEN '1-30'
            WHEN w.dpd <= 60            THEN '31-60'
            else                             '60+'
        END AS dpd_bucket
    FROM {{ ref('stg_loans') }} l
    JOIN {{ ref('stg_customers') }} c USING (customer_id)
    LEFT JOIN worst w USING (loan_id)   -- LEFT: keep every loan (denominator)
)

SELECT * FROM final
