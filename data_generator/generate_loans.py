"""Generate the `loans` table (one customer takes 1..MAX loans).

Key risk patterns baked in here:
- amount = a fraction of the customer's credit_limit
- app_score drifts DOWN for loans issued on/after DRIFT_START (creates PSI)
- _is_default is drawn from the segment default_prob gradient
- status is derived: default / closed (fully matured) / active

`segment` is NOT stored on the loan — it lives on the customer; the marts
join back. `_is_default` is an internal hint passed to the repayment generator
(it is dropped before the CSV is written).
"""

import datetime as dt

from portfolio_config import (
    MAX_LOANS_PER_CUSTOMER, COHORT_START, AS_OF, DRIFT_START,
    SEGMENT_PARAMS, TERM_MONTHS, APP_SCORE_BASE, APP_SCORE_SD, APP_SCORE_DRIFT,
)
from date_utils import add_months


def generate_loans(rng, customers):
    """Return a list of loan dicts (with an internal `_is_default` key)."""
    loans = []
    loan_seq = 0

    for customer in customers:
        n_loans = rng.randint(1, MAX_LOANS_PER_CUSTOMER)
        join_date = dt.date.fromisoformat(customer["join_date"])
        params = SEGMENT_PARAMS[customer["segment"]]

        for _ in range(n_loans):
            # Loan can't be issued before the customer joined or the cohort window.
            earliest_issue = max(COHORT_START, join_date)
            if earliest_issue >= AS_OF:
                continue
            issue_span = (AS_OF - earliest_issue).days
            issue_date = earliest_issue + dt.timedelta(days=rng.randint(0, issue_span))

            amount = int(customer["credit_limit"] * rng.uniform(0.2, 0.8))
            term_months = rng.choice(TERM_MONTHS)

            # Application score with downward drift after DRIFT_START.
            score_mean = APP_SCORE_BASE + (APP_SCORE_DRIFT if issue_date >= DRIFT_START else 0)
            app_score = int(rng.gauss(score_mean, APP_SCORE_SD))

            is_default = rng.random() < params["default_prob"]

            # Derived status (no repayments needed to decide this).
            last_due = add_months(issue_date, term_months)
            if is_default:
                status = "default"
            elif last_due <= AS_OF:
                status = "closed"      # plan fully matured by AS_OF
            else:
                status = "active"

            loans.append({
                "loan_id": f"L{loan_seq:06d}",
                "customer_id": customer["customer_id"],
                "amount": amount,
                "issue_date": issue_date.isoformat(),
                "term_months": term_months,
                "interest_rate": round(params["rate"], 4),
                "app_score": app_score,
                "status": status,
                "_is_default": is_default,
            })
            loan_seq += 1

    return loans
