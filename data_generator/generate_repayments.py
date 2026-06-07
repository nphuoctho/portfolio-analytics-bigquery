"""Generate the `repayments` table — the heart of point-in-time correctness.

For every loan we lay out one row per scheduled monthly installment
(due_date = issue_date + k months, k = 1..term). Whether it is paid depends
on behaviour:
- good loans pay every installment that is already due (small 0-10 day delay)
- defaulted loans pay a few, then STOP at a random installment (heavy tail)

Hard invariant: paid_date is NEVER after AS_OF. If a payment would land after
the cut-off we leave it unpaid. Future installments (due_date > AS_OF) are
emitted as unpaid rows — they simply are not due yet.
"""

from portfolio_config import AS_OF
from date_utils import add_months


def generate_repayments(rng, loans):
    """Return a list of repayment dicts. Reads loan['_is_default']."""
    repayments = []
    payment_seq = 0

    for loan in loans:
        issue_date = _date(loan["issue_date"])
        term = loan["term_months"]
        installment_due = max(1, round(loan["amount"] / term))

        # Defaulted loans stop paying early; the +1 guarantees at least one
        # payment. expovariate gives a geometric-ish "months until they quit".
        if loan["_is_default"]:
            stop_at = min(term, 1 + int(rng.expovariate(1 / 3.0)))
        else:
            stop_at = term + 1  # effectively "never stops"

        for k in range(1, term + 1):
            due_date = add_months(issue_date, k)
            paid_date = ""
            amount_paid = 0

            # Only installments already due by AS_OF can be paid.
            if due_date <= AS_OF and k < stop_at:
                pay_day = due_date + _delay(rng)
                if pay_day <= AS_OF:                  # no future leakage
                    paid_date = pay_day.isoformat()
                    amount_paid = installment_due

            repayments.append({
                "payment_id": f"P{payment_seq:07d}",
                "loan_id": loan["loan_id"],
                "due_date": due_date.isoformat(),
                "paid_date": paid_date,               # "" -> NULL in staging
                "amount_due": installment_due,
                "amount_paid": amount_paid,
            })
            payment_seq += 1

    return repayments


# -- helpers -----------------------------------------------------------------

def _date(iso):
    import datetime as dt
    return dt.date.fromisoformat(iso)


def _delay(rng):
    import datetime as dt
    return dt.timedelta(days=rng.randint(0, 10))
