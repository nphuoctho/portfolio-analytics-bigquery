-- Daily cash collected + a trailing 30-row rolling sum.
-- Note (interview gotcha): ROWS BETWEEN 29 PRECEDING counts 30 *rows that
-- exist* (days with at least one payment), not 30 calendar days. With dense
-- daily activity the two coincide; on sparse days they differ. Use a date
-- spine + RANGE if strict calendar windows are required.
with daily as (
    select
        paid_date as collection_date,
        sum(amount_paid) as daily_collection
    from {{ ref('stg_repayments') }}
    where is_paid
      and paid_date <= date('{{ var("as_of_date") }}')   -- no future leakage
    group by paid_date
)

select
    collection_date,
    daily_collection,
    sum(daily_collection) over (
        order by collection_date
        rows between 29 preceding and current row
    ) as rolling_30day_collection
from daily
order by collection_date
