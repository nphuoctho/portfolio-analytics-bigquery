-- Vintage curve: CUMULATIVE delinquency by issue-month cohort x months-on-book.
-- "A loan is delinquent by MOB m" if its FIRST unpaid-due installment happened
-- at or before month m. Rate rises with MOB -> the classic vintage shape.
-- Triangle by construction: each cohort is observed only up to
-- min(months elapsed since issue, loan term), and never past as_of.
-- Assumptions: MOB starts at 1; delinquency threshold = first missed installment.
with first_delinquency as (
    -- earliest MOB at which each loan missed a due installment
    select
        l.loan_id,
        min(date_diff(r.due_date, l.issue_date, month)) as first_delq_mob
    from {{ ref('stg_loans') }} l
    join {{ ref('stg_repayments') }} r using (loan_id)
    where r.due_date <= date('{{ var("as_of_date") }}')
      and not r.is_paid
    group by l.loan_id
),

loan_mob_grid as (
    -- one row per loan per observable MOB (1 .. min(age, term))
    select
        l.loan_id,
        l.cohort_month,
        mob
    from {{ ref('stg_loans') }} l,
    unnest(generate_array(
        1,
        least(
            date_diff(date('{{ var("as_of_date") }}'), l.issue_date, month),
            l.term_months
        )
    )) as mob
)

select
    g.cohort_month,
    g.mob,
    count(*) as loans_observed,
    countif(fd.first_delq_mob <= g.mob) as loans_delinquent,
    safe_divide(countif(fd.first_delq_mob <= g.mob), count(*)) as delinquency_rate
from loan_mob_grid g
left join first_delinquency fd using (loan_id)
group by g.cohort_month, g.mob
order by g.cohort_month, g.mob
