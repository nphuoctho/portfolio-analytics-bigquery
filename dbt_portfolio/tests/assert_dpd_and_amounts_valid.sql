-- Business-rule integrity. Passes when ZERO rows are returned.
-- Each branch returns the rows that VIOLATE one rule, labelled by rule name.
select 'negative_dpd' as rule, cast(loan_id as string) as id
from {{ ref('mart_loan_dpd_snapshot') }}
where dpd < 0

union all
select 'negative_amount' as rule, payment_id as id
from {{ ref('stg_repayments') }}
where amount_due < 0 or amount_paid < 0

union all
select 'overpaid' as rule, payment_id as id
from {{ ref('stg_repayments') }}
where amount_paid > amount_due
