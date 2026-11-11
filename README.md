# Personal Finance Management System

A command-line expense tracker built with Python, using object-oriented
design, CSV-based persistence, and no third-party dependencies.

Track your spending, search and filter past expenses, generate reports
with category/month breakdowns, and back up or restore your data —
all from an interactive terminal menu.

## Features

- **Add / view / update / delete** expenses with full input validation
- **Search & filter** by category, date range, or keyword
- **Reports & analysis**: total, average, median, category breakdown,
  monthly breakdown, month-over-month trend, top 5 largest expenses
- **CSV persistence** — data survives between runs in `data/expenses.csv`
- **Backup & restore** — timestamped backups, one-command restore,
  with an automatic safety backup before any restore
- **Export** — save a report to a text file, or your expenses to a
  separate CSV file for sharing
- **Robust error handling** — bad input is caught and re-prompted
  instead of crashing the program; a `KeyboardInterrupt` (Ctrl+C) still
  saves your data before exiting

## Project Structure

```
expense_tracker/
├── main.py          # Entry point — run this
├── expense.py        # Expense class (the data model)
├── file_manager.py   # CSV read/write, backup/restore, export
├── reports.py         # Calculations and report text generation
├── utils.py           # Input validation, parsing, console formatting
├── menu.py            # ExpenseManager + interactive CLI menu
├── data/
│   └── expenses.csv   # Your expense data (created automatically)
├── backups/            # Timestamped backups (created automatically)
├── reports/            # Exported report files (created automatically)
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Requirements

- Python 3.8 or later (no other software needed)
- Optionally, [VS Code](https://code.visualstudio.com/) with the Python
  extension for a nicer editing experience

Check your Python version:

```bash
python3 --version
```

### 2. Run it

No installation step is required — the project only uses Python's
standard library.

```bash
cd expense_tracker
python3 main.py
```

You'll see a menu like this:

```
============================================================
                     MAIN MENU
============================================================

 1. Add Expense
 2. View All Expenses
 3. Search / Filter Expenses
 4. Update Expense
 5. Delete Expense
 6. Reports & Analysis
 7. Backup & Restore
 8. Export Data
 0. Exit
```

Follow the prompts. Most inputs accept `c` or `cancel` to back out
partway through.

### 3. Your data

Expenses are stored in `data/expenses.csv` as plain CSV, so you can
also open it in Excel, Google Sheets, or any text editor:

```csv
id,amount,category,date,description
1,45.50,Food,2026-11-10,Grocery run
2,12.00,Transportation,2026-11-11,Bus pass
```

## Design Notes

- **`Expense`** is a small, self-validating class: its `amount`,
  `category`, and `date` are Python properties, so an `Expense` object
  can never exist in an invalid state (negative amount, bad date
  format, empty category, etc.) — invalid input raises
  `ExpenseValidationError` with a clear message.
- **`ExpenseFileManager`** owns all disk access. It creates the
  `data/`, `backups/`, and `reports/` folders automatically on first
  run, skips (and warns about) malformed CSV rows instead of crashing,
  and always takes a safety backup before overwriting data during a
  restore.
- **`reports.py`** is pure calculation/formatting code with no I/O or
  `input()` calls, so it's straightforward to unit test or reuse (e.g.
  to build a web dashboard later) independently of the CLI.
- **`menu.py`** is the only module that calls `input()`/`print()`
  directly; it composes the other modules rather than duplicating
  their logic.

## Testing Ideas

Since this project uses only the standard library, you can add tests
with `unittest` (also in the standard library), for example:

```python
import unittest
from expense import Expense, ExpenseValidationError

class TestExpense(unittest.TestCase):
    def test_negative_amount_rejected(self):
        with self.assertRaises(ExpenseValidationError):
            Expense(amount=-10, category="Food")

if __name__ == "__main__":
    unittest.main()
```

## Roadmap / Optional Extensions

- Budgets per category with over-budget alerts
- Charting (e.g. with `matplotlib`) for visual spending trends
- Recurring expenses
- Multi-currency support
- A `config.json` for custom categories and default currency

## Preparing for GitHub

1. `git init`
2. Review the included `.gitignore` (it excludes your personal
   `data/expenses.csv`, backups, and exported reports so you don't
   accidentally publish your real financial data)
3. `git add . && git commit -m "Initial commit: personal finance tracker"`
4. Create a repo on GitHub and push:
   ```bash
   git remote add origin <your-repo-url>
   git branch -M main
   git push -u origin main
   ```
# To Run the App
import sys

%cd personal_finance_manager

#Drop cached copies so edits made in the cells above take effect on re-run

for m in ["expense", "utils", "file_manager", "reports", "menu", "main"]:
    sys.modules.pop(m, None)

%run main.py

## License

Free to use and modify for personal or educational purposes.
