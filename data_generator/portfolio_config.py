"""Central configuration for the synthetic loan-portfolio dataset.

Everything is driven by one SEED so the data is fully reproducible:
re-running the generator with the same SEED yields byte-identical CSVs.
These are the "risk knobs" — change them to make the portfolio healthier
or riskier, then re-run the offline validator to get the new baseline.
"""

import datetime as dt

# Reproducibility: single source of randomness.
SEED = 42

# ---- Volume ----------------------------------------------------------------
N_CUSTOMERS = 2000              # customers; loans come out to ~3.0k
MAX_LOANS_PER_CUSTOMER = 3      # each customer takes 1..MAX loans

# ---- Timeline (point-in-time anchor) --------------------------------------
# AS_OF is "today". Nothing may be observed after it (no future leakage).
# It MUST match var('as_of_date') in dbt_project.yml.
COHORT_START = dt.date(2023, 1, 1)    # earliest possible loan issue date
AS_OF        = dt.date(2025, 4, 15)   # observation cut-off
DRIFT_START  = dt.date(2024, 7, 1)    # app_score quality drops after this -> PSI signal

# ---- Segments --------------------------------------------------------------
SEGMENTS = ["prime", "near_prime", "subprime"]
SEGMENT_WEIGHTS = [0.41, 0.40, 0.19]  # population mix (sums to 1.0)

# Per-segment risk + economics. default_prob is the gradient the marts must surface.
SEGMENT_PARAMS = {
    "prime":      {"default_prob": 0.03, "score_mean": 750, "score_sd": 30,
                   "limit_range": (50_000, 200_000), "rate": 0.012},
    "near_prime": {"default_prob": 0.09, "score_mean": 680, "score_sd": 35,
                   "limit_range": (20_000, 80_000),  "rate": 0.020},
    "subprime":   {"default_prob": 0.18, "score_mean": 600, "score_sd": 40,
                   "limit_range": (5_000, 30_000),   "rate": 0.032},
}

TERM_MONTHS = [6, 12, 18, 24]   # installment plan lengths

# ---- Application score + drift ---------------------------------------------
# Loans issued on/after DRIFT_START get a lower mean -> distribution shift (PSI).
APP_SCORE_BASE = 660
APP_SCORE_SD = 25
APP_SCORE_DRIFT = -18           # mean shift applied after DRIFT_START

# ---- Output ----------------------------------------------------------------
OUTPUT_DIR = "data"
