"""Generate the `customers` table.

One row per customer: segment (weighted), join_date (always before AS_OF),
credit_limit (uniform within the segment band) and credit_score (gaussian
around the segment mean). Segment lives here only — loans join back for it.
"""

import datetime as dt

from portfolio_config import (
    N_CUSTOMERS, SEGMENTS, SEGMENT_WEIGHTS, SEGMENT_PARAMS,
    COHORT_START, AS_OF,
)


def generate_customers(rng):
    """Return a list of customer dicts. `rng` is a seeded random.Random."""
    customers = []

    # Customers may have joined up to a year before the first cohort, and at
    # the latest a month before AS_OF (so they have time to take a loan).
    earliest_join = COHORT_START - dt.timedelta(days=365)
    latest_join = AS_OF - dt.timedelta(days=30)
    join_span_days = (latest_join - earliest_join).days

    for i in range(N_CUSTOMERS):
        segment = rng.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
        params = SEGMENT_PARAMS[segment]

        join_date = earliest_join + dt.timedelta(days=rng.randint(0, join_span_days))
        credit_limit = rng.randint(*params["limit_range"])
        # Gaussian score, clamped to a sane band.
        credit_score = int(rng.gauss(params["score_mean"], params["score_sd"]))
        credit_score = max(300, min(850, credit_score))

        customers.append({
            "customer_id": f"C{i:05d}",
            "segment": segment,
            "join_date": join_date.isoformat(),
            "credit_limit": credit_limit,
            "credit_score": credit_score,
        })

    return customers
