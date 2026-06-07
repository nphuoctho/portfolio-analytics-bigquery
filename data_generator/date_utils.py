"""Small date helper shared by the loan/repayment generators."""

import datetime as dt


def add_months(base, months):
    """Return `base` shifted forward by `months`, clamping the day to the
    last valid day of the target month (so 31 Jan + 1 month -> 28/29 Feb)."""
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    # Day-of-month clamp: step back from the 1st of the next month.
    if month == 12:
        next_month_first = dt.date(year + 1, 1, 1)
    else:
        next_month_first = dt.date(year, month + 1, 1)
    last_day = (next_month_first - dt.timedelta(days=1)).day
    return dt.date(year, month, min(base.day, last_day))
