"""
utils.py
--------
Validation, parsing and console-formatting helpers shared by the app.
"""

from datetime import datetime, timedelta

from expense import CATEGORIES, DATE_FORMAT, ExpenseValidationError


class Color:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def colorize(text, color):
    return f"{color}{text}{Color.END}"


def print_success(msg):
    print(colorize(f"✅ {msg}", Color.GREEN))


def print_error(msg):
    print(colorize(f"❌ {msg}", Color.RED))


def print_warning(msg):
    print(colorize(f"⚠ {msg}", Color.YELLOW))


def format_currency(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


# ----------------------------------------------------------------------
# Parsers: return a clean value or raise ValueError with a friendly message
# ----------------------------------------------------------------------

def parse_amount(raw):
    raw = raw.strip().replace(",", "").replace("₹", "")
    if not raw:
        raise ValueError("Amount cannot be empty.")
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"'{raw}' is not a valid number.")
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("Amount must be a finite number.")
    if value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return round(value, 2)


def parse_date(raw, allow_empty_today=True):
    """Accept YYYY-MM-DD, or blank/'today'/'yesterday' as shortcuts."""
    raw = raw.strip().lower()
    if raw == "today" or (raw == "" and allow_empty_today):
        return datetime.now().strftime(DATE_FORMAT)
    if raw == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime(DATE_FORMAT)
    try:
        parsed = datetime.strptime(raw, DATE_FORMAT)
    except ValueError:
        raise ValueError(f"'{raw}' is not a valid date. Use YYYY-MM-DD (e.g. 2024-01-15).")
    if parsed > datetime.now() + timedelta(days=1):
        raise ValueError("Date cannot be in the future.")
    return parsed.strftime(DATE_FORMAT)


def parse_category(raw):
    """Any non-empty category is accepted (so users can add their own);
    it is title-cased so 'food' and 'FOOD' end up the same."""
    raw = raw.strip()
    if not raw:
        raise ValueError("Category cannot be empty.")
    if len(raw) > 40:
        raise ValueError("Category is too long (max 40 characters).")
    return raw.title()


def parse_description(raw, max_len=200):
    raw = raw.strip()
    if len(raw) > max_len:
        raise ValueError(f"Description is too long (max {max_len} characters).")
    return raw


# ----------------------------------------------------------------------
# Prompt helpers
# ----------------------------------------------------------------------

def prompt_with_validation(prompt_text, parser, default=None, allow_cancel=True):
    """Retry until `parser(raw)` succeeds. Typing 'c' cancels (returns None).
    If `default` is given, pressing Enter on a blank line returns it."""
    while True:
        raw = input(prompt_text)
        if allow_cancel and raw.strip().lower() in ("c", "cancel"):
            return None
        if raw.strip() == "" and default is not None:
            return default
        try:
            return parser(raw)
        except (ValueError, ExpenseValidationError) as exc:
            print_error(str(exc))


def prompt_nonempty(prompt_text):
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print_error("This field cannot be empty. Please try again.")


def prompt_int_in_range(prompt_text, low, high):
    while True:
        raw = input(prompt_text).strip()
        try:
            value = int(raw)
        except ValueError:
            print_error("Please enter a valid number.")
            continue
        if not (low <= value <= high):
            print_error(f"Please enter a number between {low} and {high}.")
            continue
        return value


def confirm(prompt_text="Are you sure? (y/n): "):
    while True:
        raw = input(prompt_text).strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print_error("Please enter 'y' or 'n'.")


def category_hint():
    return "/".join(CATEGORIES)
