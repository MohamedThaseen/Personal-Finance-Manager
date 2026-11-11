"""
expense.py
----------
Defines the Expense class: the core data model of the Personal Finance
Manager. Dates are stored as YYYY-MM-DD strings everywhere, which keeps
the CSV readable and makes plain string sorting chronological.
"""

import itertools
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"
CATEGORIES = [
    "Food",
    "Transport",
    "Entertainment",
    "Shopping",
    "Bills",
    "Health",
    "Education",
    "Other",
]


class ExpenseValidationError(ValueError):
    """Raised when an Expense is built (or changed) with invalid data."""


def validate_amount(amount):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ExpenseValidationError(f"Amount must be a number, got: {amount!r}")
    if amount != amount or amount in (float("inf"), float("-inf")):
        raise ExpenseValidationError("Amount must be a finite number.")
    if amount <= 0:
        raise ExpenseValidationError("Amount must be greater than zero.")
    return round(amount, 2)


def validate_category(category):
    if category is None or not str(category).strip():
        raise ExpenseValidationError("Category cannot be empty.")
    return str(category).strip().title()


def validate_date(date):
    try:
        datetime.strptime(str(date), DATE_FORMAT)
    except ValueError:
        raise ExpenseValidationError(f"Date must be in YYYY-MM-DD format, got: {date!r}")
    return str(date)


class Expense:
    """A single expense record: amount, category, date, description."""

    _id_counter = itertools.count(1)

    def __init__(self, amount, category, date, description="", expense_id=None):
        self.amount = validate_amount(amount)
        self.category = validate_category(category)
        self.date = validate_date(date)
        self.description = str(description).strip() if description else ""
        self.id = expense_id if expense_id is not None else next(Expense._id_counter)

    @classmethod
    def reset_id_counter(cls, start):
        cls._id_counter = itertools.count(start)

    @property
    def date_obj(self):
        return datetime.strptime(self.date, DATE_FORMAT)

    def update(self, amount=None, category=None, date=None, description=None):
        """Change fields with the same validation as the constructor.
        Nothing is modified unless every supplied value is valid."""
        new_amount = validate_amount(amount) if amount is not None else self.amount
        new_category = validate_category(category) if category is not None else self.category
        new_date = validate_date(date) if date is not None else self.date
        new_desc = str(description).strip() if description is not None else self.description
        self.amount, self.category, self.date, self.description = (
            new_amount, new_category, new_date, new_desc,
        )

    def to_row(self):
        """CSV row: [ID, Date, Category, Amount, Description]."""
        return [self.id, self.date, self.category, f"{self.amount:.2f}", self.description]

    @classmethod
    def from_row(cls, row):
        expense_id, date, category, amount, description = (list(row) + [""] * 5)[:5]
        return cls(
            amount=amount,
            category=category,
            date=date,
            description=description,
            expense_id=int(expense_id) if str(expense_id).strip() else None,
        )

    def __str__(self):
        desc = f" - {self.description}" if self.description else ""
        return f"{self.date} | {self.category}: ₹{self.amount:,.2f}{desc}"

    def __repr__(self):
        return (f"Expense(id={self.id}, amount={self.amount}, category={self.category!r}, "
                f"date={self.date!r}, description={self.description!r})")

    def __lt__(self, other):
        return (self.date, self.id) < (other.date, other.id)
