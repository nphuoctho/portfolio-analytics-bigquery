-- Segment-level portfolio KPIs for leadership reporting.
-- Built ON TOP of mart_loan_dpd_snapshot (DRY: don't recompute DPD here) ->
-- this also gives a two-level mart lineage in the dbt DAG.
-- delinquency_rate = share with DPD >= 1; dpd60plus_rate = share with DPD >= 60;
-- default_rate = share with loan status 'default'.
select
    segment,
    count(*) as loans,
    safe_divide(countif(dpd >= 1),  count(*)) as delinquency_rate,
    safe_divide(countif(dpd >= 60), count(*)) as dpd60plus_rate,
    safe_divide(countif(status = 'default'), count(*)) as default_rate
from {{ ref('mart_loan_dpd_snapshot') }}
group by segment
order by segment
