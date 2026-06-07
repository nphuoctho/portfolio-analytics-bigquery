-- Point-in-time integrity: no installment may be paid after the as_of cut-off.
-- A singular test passes when it returns ZERO rows. Any row here = leakage.
select
    payment_id,
    paid_date
from {{ ref('stg_repayments') }}
where paid_date > date('{{ var("as_of_date") }}')
