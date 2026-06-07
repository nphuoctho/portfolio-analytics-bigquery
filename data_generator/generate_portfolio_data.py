"""Orchestrator: build customers -> loans -> repayments, write CSVs, print stats.

Run from this directory:
    uv run python generate_portfolio_data.py

Output: data/customers.csv, data/loans.csv, data/repayments.csv
Everything is reproducible from SEED in portfolio_config.py.
"""

import csv
import os
import random

from portfolio_config import SEED, AS_OF, OUTPUT_DIR
from generate_customers import generate_customers
from generate_loans import generate_loans
from generate_repayments import generate_repayments

# CSV columns per table (excludes internal keys like _is_default).
CUSTOMER_COLS = ["customer_id", "segment", "join_date", "credit_limit", "credit_score"]
LOAN_COLS = ["loan_id", "customer_id", "amount", "issue_date", "term_months",
             "interest_rate", "app_score", "status"]
REPAYMENT_COLS = ["payment_id", "loan_id", "due_date", "paid_date",
                  "amount_due", "amount_paid"]


def write_csv(path, rows, columns):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def assert_point_in_time(repayments):
    """Hard guard: no payment may be observed after the AS_OF cut-off."""
    as_of = AS_OF.isoformat()
    leaks = [r for r in repayments if r["paid_date"] and r["paid_date"] > as_of]
    assert not leaks, f"LEAKAGE: {len(leaks)} payments after AS_OF {as_of}"


def print_stats(customers, loans, repayments):
    seg_of = {c["customer_id"]: c["segment"] for c in customers}
    segments = ["prime", "near_prime", "subprime"]

    print(f"\n=== Portfolio dataset (SEED={SEED}, AS_OF={AS_OF}) ===")
    print(f"customers : {len(customers):>6}")
    print(f"loans     : {len(loans):>6}")
    print(f"repayments: {len(repayments):>6}")

    print("\nLoans + default rate by segment:")
    for seg in segments:
        seg_loans = [l for l in loans if seg_of[l["customer_id"]] == seg]
        n = len(seg_loans)
        defaults = sum(1 for l in seg_loans if l["status"] == "default")
        rate = defaults / n if n else 0
        print(f"  {seg:<11} loans={n:>5}  default={rate:6.1%}")

    paid = sum(1 for r in repayments if r["paid_date"])
    print(f"\npaid installments: {paid}/{len(repayments)} ({paid/len(repayments):.1%})")
    print("(Exact DPD buckets come from the offline validator in Phase 5.)")


def main():
    rng = random.Random(SEED)
    customers = generate_customers(rng)
    loans = generate_loans(rng, customers)
    repayments = generate_repayments(rng, loans)

    assert_point_in_time(repayments)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    write_csv(os.path.join(OUTPUT_DIR, "customers.csv"), customers, CUSTOMER_COLS)
    write_csv(os.path.join(OUTPUT_DIR, "loans.csv"), loans, LOAN_COLS)
    write_csv(os.path.join(OUTPUT_DIR, "repayments.csv"), repayments, REPAYMENT_COLS)

    print_stats(customers, loans, repayments)
    print(f"\nCSVs written to ./{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
