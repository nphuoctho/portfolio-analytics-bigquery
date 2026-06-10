# Architecture

Three layers, built and tested by dbt on BigQuery.

- **raw** — three seeded CSVs loaded as-is.
- **staging** — one view per source table; clean, cast, rename.
- **marts** — aggregated tables the dashboards query.

```mermaid
flowchart LR
  subgraph raw["raw (seeds)"]
    c[customers]
    l[loans]
    r[repayments]
  end
  subgraph staging["staging (views)"]
    sc[stg_customers]
    sl[stg_loans]
    sr[stg_repayments]
  end
  subgraph marts["marts (tables)"]
    dpd[mart_loan_dpd_snapshot]
    vin[mart_vintage_curve]
    roll[mart_rolling_collection]
    health[mart_portfolio_health]
  end

  c --> sc
  l --> sl
  r --> sr

  sc --> dpd
  sl --> dpd
  sr --> dpd
  sl --> vin
  sr --> vin
  sr --> roll
  dpd --> health
```

`mart_portfolio_health` reads `mart_loan_dpd_snapshot` instead of recomputing
DPD, so the segment KPIs and the per-loan snapshot can never disagree.

A separate Python script (`data_generator/validate_marts_offline.py`) recomputes
the DPD buckets and segment rates straight from the CSVs. It never touches
BigQuery, so matching numbers confirm the SQL rather than restate it.
