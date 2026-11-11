"""
menu.py
-------
Interactive command-line interface. Owns the ExpenseManager (in-memory
state) and the menu loop. Persistence lives in file_manager.py,
calculations in reports.py, validation in utils.py.
"""

import reports
import utils
from expense import CATEGORIES, Expense, ExpenseValidationError
from file_manager import FileManagerError


class ExpenseManager:
    """In-memory list of expenses, kept in sync with disk via the file manager."""

    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.expenses = []

    def load(self):
        try:
            self.expenses = self.file_manager.load_expenses()
        except FileManagerError as exc:
            utils.print_error(f"Could not load data: {exc}")
            self.expenses = []

    def save(self):
        try:
            self.file_manager.save_expenses(self.expenses)
        except FileManagerError as exc:
            utils.print_error(f"Could not save data: {exc}")
            return False
        return True

    def add_expense(self, expense):
        self.expenses.append(expense)
        return self.save()

    def delete_expense(self, expense_id):
        target = self.find_by_id(expense_id)
        if target is None:
            return False
        self.expenses.remove(target)
        if not self.save():
            self.expenses.append(target)  # keep memory and disk consistent
            return False
        return True

    def update_expense(self, expense_id, **changes):
        """Returns the updated Expense, or None if not found / not saved."""
        target = self.find_by_id(expense_id)
        if target is None:
            return None
        old = (target.amount, target.category, target.date, target.description)
        target.update(**changes)  # raises ExpenseValidationError on bad input
        if not self.save():
            target.amount, target.category, target.date, target.description = old
            return None
        return target

    def find_by_id(self, expense_id):
        return next((e for e in self.expenses if e.id == expense_id), None)


# ----------------------------------------------------------------------
# Screen helpers
# ----------------------------------------------------------------------

APP_TITLE = "PERSONAL FINANCE MANAGER"

MAIN_MENU_TEXT = """
MAIN MENU:
1. Add New Expense
2. View All Expenses
3. View Category-wise Summary
4. Generate Monthly Report
5. Search Expenses
6. Backup Data
7. Exit
"""


def print_banner():
    print("=" * 42)
    print(APP_TITLE.center(42))
    print("=" * 42)


def pause():
    input("\nPress Enter to continue...")


def run_app(manager):
    print_banner()
    print(f"\nLoaded {len(manager.expenses)} existing expense(s) from "
          f"'{manager.file_manager.data_file}'.")

    handlers = {
        1: handle_add_expense,
        2: handle_view_all,
        3: handle_category_summary,
        4: handle_monthly_report,
        5: handle_search,
        6: handle_backup_menu,
    }
    while True:
        print(MAIN_MENU_TEXT)
        choice = utils.prompt_int_in_range("Enter your choice (1-7): ", 1, 7)
        if choice == 7:
            manager.save()
            print("\n✅ Goodbye! Your data has been saved.")
            break
        handlers[choice](manager)


# ----------------------------------------------------------------------
# 1. Add
# ----------------------------------------------------------------------

def handle_add_expense(manager):
    print("\nADD NEW EXPENSE:  (type 'c' at any prompt to cancel)")

    amount = utils.prompt_with_validation("Enter amount: ", utils.parse_amount)
    if amount is None:
        return _cancelled()

    category = utils.prompt_with_validation(
        f"Enter category ({utils.category_hint()}): ", utils.parse_category)
    if category is None:
        return _cancelled()

    date = utils.prompt_with_validation(
        "Enter date (YYYY-MM-DD, blank = today): ", utils.parse_date)
    if date is None:
        return _cancelled()

    while True:
        raw = input("Enter description: ")
        try:
            description = utils.parse_description(raw)
            break
        except ValueError as exc:
            utils.print_error(str(exc))

    try:
        expense = Expense(amount=amount, category=category, date=date,
                          description=description)
    except ExpenseValidationError as exc:
        utils.print_error(f"Could not add expense: {exc}")
        return pause()

    if manager.add_expense(expense):
        print("\n✅ Expense added successfully!")
    else:
        utils.print_error("Expense is in memory but could not be saved to disk.")
    pause()


def _cancelled():
    utils.print_warning("Cancelled.")
    pause()


# ----------------------------------------------------------------------
# 2. View all (+ update / delete)
# ----------------------------------------------------------------------

def handle_view_all(manager):
    print("\nALL EXPENSES:")
    if not manager.expenses:
        utils.print_warning("No expenses recorded yet.")
        return pause()

    items = sorted(manager.expenses)
    for e in items:
        print(f"[{e.id}] {e}")
    print(f"\nTotal: {len(items)} expense(s), "
          f"{utils.format_currency(reports.total_spent(items))}")

    print("\nOptions: [u] Update an expense  [d] Delete an expense  [Enter] Back to menu")
    action = input("Choice: ").strip().lower()
    if action == "u":
        _update_expense_flow(manager)
    elif action == "d":
        _delete_expense_flow(manager)


def _ask_expense_id(manager, verb):
    raw = input(f"Enter the ID of the expense to {verb}: ").strip()
    try:
        expense_id = int(raw)
    except ValueError:
        utils.print_error("Please enter a valid numeric ID.")
        return None
    existing = manager.find_by_id(expense_id)
    if existing is None:
        utils.print_error(f"No expense found with ID {expense_id}.")
    return existing


def _update_expense_flow(manager):
    existing = _ask_expense_id(manager, "update")
    if existing is None:
        return pause()

    print(f"Current: {existing}")
    print("(Press Enter to keep a value, 'c' to cancel)")

    new_amount = utils.prompt_with_validation(
        f"New amount [{existing.amount}]: ", utils.parse_amount, default=existing.amount)
    if new_amount is None:
        return _cancelled()
    new_category = utils.prompt_with_validation(
        f"New category [{existing.category}]: ", utils.parse_category,
        default=existing.category)
    if new_category is None:
        return _cancelled()
    new_date = utils.prompt_with_validation(
        f"New date [{existing.date}]: ",
        lambda r: utils.parse_date(r, allow_empty_today=False), default=existing.date)
    if new_date is None:
        return _cancelled()

    while True:
        raw = input(f"New description [{existing.description}]: ").strip()
        try:
            new_description = utils.parse_description(raw) if raw else existing.description
            break
        except ValueError as exc:
            utils.print_error(str(exc))

    try:
        updated = manager.update_expense(
            existing.id, amount=new_amount, category=new_category,
            date=new_date, description=new_description)
    except ExpenseValidationError as exc:
        utils.print_error(f"Update failed: {exc}")
        return pause()

    if updated:
        print(f"\n✅ Expense updated: {updated}")
    else:
        utils.print_error("Update could not be saved.")
    pause()


def _delete_expense_flow(manager):
    existing = _ask_expense_id(manager, "delete")
    if existing is None:
        return pause()

    print(f"About to delete: {existing}")
    if not utils.confirm("Confirm deletion? (y/n): "):
        return _cancelled()

    if manager.delete_expense(existing.id):
        print(f"\n✅ Expense {existing.id} deleted successfully!")
    else:
        utils.print_error("Delete could not be saved.")
    pause()


# ----------------------------------------------------------------------
# 3. Category summary
# ----------------------------------------------------------------------

def handle_category_summary(manager):
    print("\nCATEGORY-WISE SUMMARY:")
    if not manager.expenses:
        utils.print_warning("No expenses recorded yet.")
        return pause()

    breakdown = reports.category_breakdown(manager.expenses)
    counts = reports.category_counts(manager.expenses)
    grand_total = reports.total_spent(manager.expenses)
    for cat, amt in breakdown.items():
        pct = (amt / grand_total * 100) if grand_total else 0
        print(f"{cat:<22} {utils.format_currency(amt):>14}  "
              f"({pct:5.1f}%)  [{counts[cat]} item(s)]")
    print(f"\nGrand Total: {utils.format_currency(grand_total)}")
    pause()


# ----------------------------------------------------------------------
# 4. Monthly report
# ----------------------------------------------------------------------

def _parse_month(raw):
    from datetime import datetime
    raw = raw.strip()
    try:
        return datetime.strptime(raw, "%Y-%m").strftime("%Y-%m")
    except ValueError:
        raise ValueError(f"'{raw}' is not a valid month. Use YYYY-MM (e.g. 2024-01).")


def handle_monthly_report(manager):
    print("\nMONTHLY REPORT:")
    if not manager.expenses:
        utils.print_warning("No expenses recorded yet.")
        return pause()

    months = list(reports.monthly_breakdown(manager.expenses))
    print(f"Months with data: {', '.join(months)}")
    month = utils.prompt_with_validation(
        "Month to report on (YYYY-MM, blank = all time): ",
        lambda r: _parse_month(r) if r.strip() else "")
    if month is None:
        return _cancelled()

    if month:
        if month not in months:
            utils.print_warning(f"No expenses recorded in {month}.")
            return pause()
        report_text = reports.build_monthly_report(manager.expenses, month)
        prefix = f"report_{month}"
    else:
        report_text = reports.build_summary_report(manager.expenses)
        prefix = "report_all"
    print(report_text)

    if utils.confirm("\nSave this report to a file? (y/n): "):
        try:
            path = manager.file_manager.export_report(report_text, prefix=prefix)
            print(f"\n✅ Report saved to '{path}'.")
        except FileManagerError as exc:
            utils.print_error(str(exc))
    pause()


# ----------------------------------------------------------------------
# 5. Search
# ----------------------------------------------------------------------

def handle_search(manager):
    print("\nSEARCH EXPENSES:")
    print("1. By category")
    print("2. By date range")
    print("3. By keyword in description")
    choice = utils.prompt_int_in_range("Select an option (1-3): ", 1, 3)

    if choice == 1:
        category = utils.prompt_nonempty("Category to search for: ")
        results = reports.filter_by_category(manager.expenses, category)
    elif choice == 2:
        def parse_bound(raw):
            return utils.parse_date(raw, allow_empty_today=False) if raw.strip() else ""
        start = utils.prompt_with_validation(
            "Start date (YYYY-MM-DD, blank = no lower bound): ", parse_bound)
        if start is None:
            return _cancelled()
        end = utils.prompt_with_validation(
            "End date (YYYY-MM-DD, blank = no upper bound): ", parse_bound)
        if end is None:
            return _cancelled()
        start, end = start or None, end or None
        if start and end and start > end:
            utils.print_error("Start date is after the end date.")
            return pause()
        results = reports.filter_by_date_range(manager.expenses, start, end)
    else:
        keyword = utils.prompt_nonempty("Keyword to search for: ").lower()
        results = [e for e in manager.expenses if keyword in e.description.lower()]

    if not results:
        utils.print_warning("No matching expenses found.")
        return pause()

    for e in sorted(results):
        print(f"[{e.id}] {e}")
    print(f"\nFound {len(results)} expense(s), total "
          f"{utils.format_currency(reports.total_spent(results))}")
    pause()


# ----------------------------------------------------------------------
# 6. Backup / restore / export
# ----------------------------------------------------------------------

def handle_backup_menu(manager):
    print("\nBACKUP DATA:")
    print("1. Create backup now")
    print("2. List backups")
    print("3. Restore from backup")
    print("4. Export expenses to a CSV file")
    choice = utils.prompt_int_in_range("Select an option (1-4): ", 1, 4)
    fm = manager.file_manager

    if choice == 1:
        try:
            manager.save()
            path = fm.create_backup()
            print(f"\n✅ Backup created successfully: '{path}'")
        except FileManagerError as exc:
            utils.print_error(str(exc))

    elif choice == 2:
        backups = fm.list_backups()
        if not backups:
            utils.print_warning("No backups found.")
        for i, name in enumerate(backups, 1):
            print(f" {i}. {name}")

    elif choice == 3:
        backups = fm.list_backups()
        if not backups:
            utils.print_warning("No backups available to restore.")
            return pause()
        for i, name in enumerate(backups, 1):
            print(f" {i}. {name}")
        idx = utils.prompt_int_in_range(
            f"Select a backup to restore (1-{len(backups)}): ", 1, len(backups))
        chosen = backups[idx - 1]
        if not utils.confirm(
                f"This will replace current data with '{chosen}' "
                f"(current data is backed up first). Continue? (y/n): "):
            return _cancelled()
        try:
            fm.restore_backup(chosen)
            manager.load()
            print(f"\n✅ Data restored from '{chosen}'. "
                  f"{len(manager.expenses)} expense(s) loaded.")
        except FileManagerError as exc:
            utils.print_error(str(exc))

    else:
        path = input("Export file path (e.g. reports/export.csv): ").strip()
        if not path:
            return _cancelled()
        try:
            exported = fm.export_csv_copy(manager.expenses, path)
            print(f"\n✅ Exported {len(manager.expenses)} expense(s) to '{exported}'.")
        except FileManagerError as exc:
            utils.print_error(str(exc))

    pause()
