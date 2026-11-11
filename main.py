"""
main.py
-------
Entry point for the Personal Finance Manager.

Run with:
    python main.py

Kept thin on purpose: it wires the file manager and expense manager
together and hands control to the menu loop.
"""

import os
import sys

# Always keep data next to the program, no matter where it is launched from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from file_manager import ExpenseFileManager, FileManagerError  # noqa: E402
from menu import ExpenseManager, run_app                       # noqa: E402
from utils import print_error                                  # noqa: E402

DATA_FILE = os.path.join("data", "expenses.csv")
BACKUP_DIR = "backups"
REPORTS_DIR = "reports"


def main():
    try:
        file_manager = ExpenseFileManager(DATA_FILE, BACKUP_DIR, REPORTS_DIR)
    except FileManagerError as exc:
        print_error(f"Fatal error setting up data storage: {exc}")
        sys.exit(1)

    manager = ExpenseManager(file_manager)
    manager.load()

    try:
        run_app(manager)
    except (KeyboardInterrupt, EOFError):
        print("\n\nInterrupted. Saving data before exit...")
        manager.save()
        print("Goodbye!")
        sys.exit(0)
    except Exception as exc:  # last-resort safety net so data is never lost
        print_error(f"An unexpected error occurred: {exc}")
        manager.save()
        print("Your data has been saved. Please report this issue.")
        sys.exit(1)


if __name__ == "__main__":
    main()
