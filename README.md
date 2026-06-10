# Loan Portfolio Analytics (BigQuery + dbt)

A small analytics warehouse for a consumer-lending portfolio. It takes raw loan
data and builds the marts a credit-risk team actually looks at: days-past-due
buckets, vintage curves, rolling collections, and delinquency by segment.

Live dashboard: https://datastudio.google.com/s/osH2qKIIang

## Layout

- `data_generator/` — Python that generates the dataset (customers, loans, repayments).
- `dbt_portfolio/` — the dbt project: seeds, staging views, marts, tests.
- `docs/architecture.md` — pipeline and lineage diagram.

## Marts

- **mart_loan_dpd_snapshot** — DPD per loan at a cut-off date, bucketed (0 / 1-30 / 31-60 / 60+).
- **mart_vintage_curve** — cumulative delinquency by origination cohort × months-on-book.
- **mart_rolling_collection** — daily collections with a 30-row rolling sum.
- **mart_portfolio_health** — delinquency, 60+, and default rates by segment.

## Running it

```bash
# generate the data (local, no cloud)
cd data_generator
uv run python generate_portfolio_data.py
uv run python validate_marts_offline.py      # independent check

# build on BigQuery (needs ~/.dbt/profiles.yml using oauth)
cd ../dbt_portfolio
cp ../data_generator/data/*.csv seeds/
uv run dbt deps
uv run dbt build
```

`dbt build` runs seeds, models, and tests in one pass. Auth is BigQuery OAuth, so
run `gcloud auth application-default login` first. The repo holds no credentials.

## Tests

The dbt project has the usual schema tests (keys, ranges, accepted values) and
two singular tests. One rejects any payment dated after the cut-off, which keeps
the vintage and DPD logic free of future leakage. The other checks the basic
business rules — no negative DPD, no overpayment. `validate_marts_offline.py`
recomputes the headline numbers in plain Python so I can diff them against the
warehouse instead of trusting the SQL.

## The data

There is no public dataset with clean, installment-level, point-in-time
repayment history, so the data is synthetic. The generator is seeded and
reproducible. It builds in a default-rate gradient across segments and a small
score drift over time. The seeded run is about 4k loans and 59k installments.
The same dbt models would run unchanged against a real warehouse.

## Stack

Python (standard library), BigQuery, dbt Core + dbt_utils, Looker Studio.
