# Loan Portfolio Analytics - BigQuery + dbt

This project turns raw lending data into analytics marts: **DPD buckets, vintage
curves (cohort × MOB), rolling collections, and segment health KPIs**. SQL
window functions do the math on **BigQuery**. **dbt** runs the pipeline. A
separate Python script checks every number against ground truth.

**Live links** · 📊 Dashboard: https://datastudio.google.com/s/osH2qKIIang · 📚 dbt docs: _(GitHub Pages — add link)_

---

## Architecture / Kiến trúc

```
data_generator/ (Python, stdlib)        BigQuery (dbt)
  customers.csv  ┐                 seeds (raw)     staging (views)        marts (tables)
  loans.csv      ├─ dbt seed ────> customers  ──>  stg_customers ┐
  repayments.csv ┘                 loans      ──>  stg_loans     ├─> mart_loan_dpd_snapshot ─> mart_portfolio_health
                                   repayments ──>  stg_repayments┘    mart_vintage_curve
                                                                       mart_rolling_collection
  validate_marts_offline.py ── ground-truth cross-check (no cloud) ──┘
```

Three layers. **raw** loads the CSVs as-is. **staging** cleans, casts, renames
(views). **mart** aggregates into query-ready tables. `dbt build` rebuilds the
whole thing in one command.

## Tech stack

| Tool | Role |
|---|---|
| Python (stdlib) | Synthetic, point-in-time-correct data generator |
| BigQuery (sandbox) | Cloud warehouse |
| dbt Core + dbt_utils | Transformations, tests, lineage/docs |
| Looker Studio | Dashboards |

## The marts

| Mart | What it computes |
|---|---|
| `mart_loan_dpd_snapshot` | Per-loan DPD (oldest unpaid due installment) + bucket, as of `as_of_date` |
| `mart_vintage_curve` | Cumulative delinquency by issue-cohort × months-on-book (triangle) |
| `mart_rolling_collection` | Daily cash collected + 30-row rolling sum |
| `mart_portfolio_health` | Segment KPIs: delinquency %, 60+ %, default % |

## Run it / Cách chạy

```bash
# 1. Generate the data (no cloud needed)
cd data_generator
uv run python generate_portfolio_data.py     # -> data/*.csv + stats
uv run python validate_marts_offline.py       # ground-truth numbers

# 2. Load + build + test on BigQuery (needs ~/.dbt/profiles.yml, oauth)
cd ../dbt_portfolio
cp ../data_generator/data/*.csv seeds/
uv run dbt deps
uv run dbt build          # seed + run + test, one command
uv run dbt docs generate  # lineage graph + data dictionary
```

`~/.dbt/profiles.yml` uses BigQuery with `method: oauth`. Run
`gcloud auth application-default login` first. No credentials live in the repo.

## Data quality / Chất lượng dữ liệu

- Schema tests: `not_null`, `unique`, `relationships`, `accepted_values`, `accepted_range`.
- 2 singular tests:
  - `assert_no_future_payments` — point-in-time integrity (no `paid_date > as_of`).
  - `assert_dpd_and_amounts_valid` — DPD ≥ 0, amounts ≥ 0, no overpayment.
- **Ground-truth cross-check:** `validate_marts_offline.py` recomputes the marts
  in plain Python. The numbers match BigQuery. I check outputs instead of
  trusting generated SQL.

## Results (SEED=42) / Kết quả

Scale: **3,953 loans · 58,896 installments · 2,000 customers**.

DPD buckets: `0` = 3361 · `1-30` = 375 · `31-60` = 34 · `60+` = 183.

| Segment | Loans | Delinquency (DPD≥1) | 60+ | Default |
|---|---|---|---|---|
| prime | 1,629 | 11.2% | 1.6% | 3.2% |
| near_prime | 1,610 | 16.0% | 5.2% | 9.4% |
| subprime | 714 | 21.3% | 10.5% | 17.1% |

The Python validator and the BigQuery marts return the same figures.

## Why synthetic data? / Vì sao dùng data tổng hợp?

No public dataset gives installment-level, point-in-time-correct repayment
history with risk signals I can control. So I generate it. That rules out future
leakage, bakes in a known default gradient, and lets me prove the marts against
ground truth — the skill this role screens for. Swap the seeds for real
warehouse tables and the dbt code stays the same.

---

## CV bullets

- Built a **BigQuery + dbt** lending-portfolio warehouse (raw → staging → mart)
  computing **DPD buckets, cumulative vintage curves (cohort × MOB), rolling
  collections, and segment delinquency** via CTEs and window functions
  (3.9k loans / 58.9k installments).
- Added dbt schema tests plus a custom **point-in-time integrity** test (no
  future-payment leakage) and business-rule checks. Lineage and docs generate
  from `dbt docs`.
- **Cross-validated** every mart against a separate Python ground-truth script.
  I check outputs instead of trusting generated SQL.
