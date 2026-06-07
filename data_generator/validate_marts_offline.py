"""Offline ground-truth check.

Recomputes the headline marts (DPD buckets + segment health) in plain Python
straight from the CSVs, with no SQL/warehouse involved. Compare this output to
the BigQuery marts: matching numbers prove the dbt SQL is correct rather than
trusting it blindly.

    cd data_generator && uv run python validate_marts_offline.py
"""

import csv
import datetime as dt
import os
from collections import defaultdict

from portfolio_config import AS_OF, OUTPUT_DIR

SEGMENTS = ["prime", "near_prime", "subprime"]
BUCKETS = ["0", "1-30", "31-60", "60+"]


def _load(name):
    with open(os.path.join(OUTPUT_DIR, name)) as f:
        return list(csv.DictReader(f))


def _bucket(dpd):
    if dpd == 0:
        return "0"
    if dpd <= 30:
        return "1-30"
    if dpd <= 60:
        return "31-60"
    return "60+"


def compute_dpd(loans, repayments):
    """DPD per loan = max days-past-due among due-and-unpaid installments."""
    dpd = {l["loan_id"]: 0 for l in loans}
    for r in repayments:
        due = dt.date.fromisoformat(r["due_date"])
        if due <= AS_OF and not r["paid_date"].strip():
            dpd[r["loan_id"]] = max(dpd[r["loan_id"]], (AS_OF - due).days)
    return dpd


def main():
    customers = _load("customers.csv")
    loans = _load("loans.csv")
    repayments = _load("repayments.csv")

    seg_of = {c["customer_id"]: c["segment"] for c in customers}
    dpd = compute_dpd(loans, repayments)

    print(f"=== GROUND TRUTH (Python, AS_OF={AS_OF}) ===\n")

    buckets = defaultdict(int)
    for loan_id, days in dpd.items():
        buckets[_bucket(days)] += 1
    print("DPD buckets:")
    for b in BUCKETS:
        print(f"  {b:<6} {buckets[b]}")

    print("\nPortfolio health by segment:")
    agg = {s: {"loans": 0, "dq": 0, "d60": 0, "default": 0} for s in SEGMENTS}
    for loan in loans:
        seg = seg_of[loan["customer_id"]]
        days = dpd[loan["loan_id"]]
        a = agg[seg]
        a["loans"] += 1
        a["dq"] += days >= 1
        a["d60"] += days >= 60
        a["default"] += loan["status"] == "default"
    for s in SEGMENTS:
        a = agg[s]
        n = a["loans"]
        print(f"  {s:<11} loans={n:<5} "
              f"dq={a['dq']/n:.3f} d60={a['d60']/n:.3f} default={a['default']/n:.3f}")

    print("\nCompare these to: select dpd_bucket,count(*) ... and mart_portfolio_health.")


if __name__ == "__main__":
    main()
