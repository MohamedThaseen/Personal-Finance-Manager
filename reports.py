"""
reports.py
----------
Calculations and report text built from a list of Expense objects.
Pure functions: no input/output, so they are easy to test and reuse.
"""

from collections import defaultdict
from datetime import datetime
from statistics import mean, median

from utils import format_currency


# ----------------------------------------------------------------------
# Calculations
# ----------------------------------------------------------------------

def total_spent(expenses):
    return round(sum(e.amount for e in expenses), 2)


def average_spent(expenses):
    return round(mean(e.amount for e in expenses), 2) if expenses else 0.0


def median_spent(expenses):
    return round(median(e.amount for e in expenses), 2) if expenses else 0.0


def category_breakdown(expenses):
    """{category: total}, highest spend first."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e.category] += e.amount
    return {k: round(v, 2) for k, v in
            sorted(totals.items(), key=lambda kv: kv[1], reverse=True)}


def category_counts(expenses):
    counts = defaultdict(int)
    for e in expenses:
        counts[e.category] += 1
    return dict(counts)


def monthly_breakdown(expenses):
    """{'YYYY-MM': total}, oldest month first."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e.date[:7]] += e.amount
    return {k: round(v, 2) for k, v in sorted(totals.items())}


def top_expenses(expenses, n=5):
    return sorted(expenses, key=lambda e: e.amount, reverse=True)[:n]


def filter_by_category(expenses, category):
    category = category.strip().title()
    return [e for e in expenses if e.category == category]


def filter_by_date_range(expenses, start_date=None, end_date=None):
    """start_date / end_date are 'YYYY-MM-DD' strings (inclusive) or None."""
    return [e for e in expenses
            if (start_date is None or e.date >= start_date)
            and (end_date is None or e.date <= end_date)]


def filter_by_month(expenses, month):
    """month is 'YYYY-MM'."""
    return [e for e in expenses if e.date.startswith(month)]


def spending_trend(expenses):
    """Latest month vs the one before it, or None if fewer than two months."""
    monthly = monthly_breakdown(expenses)
    months = list(monthly)
    if len(months) < 2:
        return None
    prev_m, curr_m = months[-2], months[-1]
    prev_t, curr_t = monthly[prev_m], monthly[curr_m]
    pct = round((curr_t - prev_t) / prev_t * 100, 1) if prev_t else None
    return {"previous_month": prev_m, "previous_total": prev_t,
            "current_month": curr_m, "current_total": curr_t, "pct_change": pct}


# ----------------------------------------------------------------------
# Report text
# ----------------------------------------------------------------------

def _category_lines(expenses, width_name=22):
    breakdown = category_breakdown(expenses)
    counts = category_counts(expenses)
    grand_total = total_spent(expenses)
    max_amount = max(breakdown.values()) if breakdown else 1
    lines = []
    for cat, amt in breakdown.items():
        pct = (amt / grand_total * 100) if grand_total else 0
        bar = "#" * int(amt / max_amount * 20)
        lines.append(f"{cat:<{width_name}} {format_currency(amt):>14} ({pct:5.1f}%) "
                     f"[{counts[cat]:>3}] {bar}")
    return lines


def build_summary_report(expenses, title="PERSONAL FINANCE SUMMARY REPORT"):
    width = 66
    lines = ["=" * width, title.center(width),
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(width),
             "=" * width]
    if not expenses:
        lines.append("\nNo expenses recorded yet.")
        return "\n".join(lines)

    largest = max(expenses, key=lambda e: e.amount)
    smallest = min(expenses, key=lambda e: e.amount)
    lines += [
        f"\nTotal expenses recorded : {len(expenses)}",
        f"Total amount spent      : {format_currency(total_spent(expenses))}",
        f"Average per expense     : {format_currency(average_spent(expenses))}",
        f"Median expense          : {format_currency(median_spent(expenses))}",
        f"Largest expense         : {format_currency(largest.amount)} "
        f"({largest.category}, {largest.date})",
        f"Smallest expense        : {format_currency(smallest.amount)} "
        f"({smallest.category}, {smallest.date})",
        "\n" + "-" * width, "SPENDING BY CATEGORY", "-" * width,
    ]
    lines += _category_lines(expenses)

    lines += ["\n" + "-" * width, "SPENDING BY MONTH", "-" * width]
    for month, amt in monthly_breakdown(expenses).items():
        lines.append(f"{month:<22} {format_currency(amt):>14}")

    trend = spending_trend(expenses)
    if trend:
        pct = trend["pct_change"]
        if pct is None:
            change, direction = "N/A", "n/a"
        else:
            change = f"{pct:+.1f}%"
            direction = "up" if pct > 0 else "down" if pct < 0 else "unchanged"
        lines += ["\n" + "-" * width, "MONTH-OVER-MONTH TREND", "-" * width,
                  f"{trend['previous_month']} -> {trend['current_month']}: "
                  f"{format_currency(trend['previous_total'])} -> "
                  f"{format_currency(trend['current_total'])} ({change}, {direction})"]

    lines += ["\n" + "-" * width, "TOP 5 LARGEST EXPENSES", "-" * width]
    lines += [str(e) for e in top_expenses(expenses, 5)]
    lines.append("\n" + "=" * width)
    return "\n".join(lines)


def build_monthly_report(expenses, month):
    """Report for a single 'YYYY-MM' month."""
    subset = filter_by_month(expenses, month)
    return build_summary_report(subset, title=f"MONTHLY REPORT: {month}")
