"""
file_manager.py
---------------
All disk access: CSV load/save, timestamped backups, restore, and exports.

CSV columns: ID, Date, Category, Amount, Description
"""

import csv
import os
import shutil
from datetime import datetime

from expense import Expense, ExpenseValidationError

HEADER = ["ID", "Date", "Category", "Amount", "Description"]


class FileManagerError(Exception):
    """Raised for file I/O problems the caller should report to the user."""


class ExpenseFileManager:
    def __init__(self, data_file=os.path.join("data", "expenses.csv"),
                 backup_dir="backups", reports_dir="reports"):
        self.data_file = data_file
        self.backup_dir = backup_dir
        self.reports_dir = reports_dir
        self._ensure_paths()

    def _ensure_paths(self):
        try:
            os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
            os.makedirs(self.backup_dir, exist_ok=True)
            os.makedirs(self.reports_dir, exist_ok=True)
        except OSError as exc:
            raise FileManagerError(f"Could not create required folders: {exc}")
        if not os.path.exists(self.data_file):
            self.save_expenses([])

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------
    def load_expenses(self):
        expenses, skipped = [], 0
        if not os.path.exists(self.data_file):
            return expenses
        try:
            with open(self.data_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # header
                for row in reader:
                    if not row or not any(cell.strip() for cell in row):
                        continue
                    try:
                        expenses.append(Expense.from_row(row))
                    except (ExpenseValidationError, ValueError):
                        skipped += 1
        except (OSError, csv.Error, UnicodeDecodeError) as exc:
            raise FileManagerError(f"Failed to read '{self.data_file}': {exc}")

        if skipped:
            print(f"⚠ Warning: skipped {skipped} malformed row(s) in {self.data_file}.")

        # Duplicate IDs would make update/delete ambiguous; re-number repeats.
        seen = set()
        next_id = max((e.id for e in expenses), default=0) + 1
        for e in expenses:
            if e.id in seen:
                e.id = next_id
                next_id += 1
            seen.add(e.id)
        Expense.reset_id_counter(next_id)
        return expenses

    def save_expenses(self, expenses):
        """Write atomically (temp file, then replace) so a crash mid-write
        can never leave a half-written CSV."""
        tmp_path = self.data_file + ".tmp"
        try:
            self._write_csv(tmp_path, expenses)
            os.replace(tmp_path, self.data_file)
        except OSError as exc:
            raise FileManagerError(f"Failed to write '{self.data_file}': {exc}")

    @staticmethod
    def _write_csv(path, expenses):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
            for e in sorted(expenses, key=lambda x: x.id):
                writer.writerow(e.to_row())

    # ------------------------------------------------------------------
    # Backup / restore
    # ------------------------------------------------------------------
    def create_backup(self):
        if not os.path.exists(self.data_file):
            raise FileManagerError("No data file exists yet, nothing to back up.")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        base = os.path.splitext(os.path.basename(self.data_file))[0]
        path = os.path.join(self.backup_dir, f"{base}_backup_{stamp}.csv")
        try:
            shutil.copy2(self.data_file, path)
        except OSError as exc:
            raise FileManagerError(f"Backup failed: {exc}")
        return path

    def list_backups(self):
        """Backup file names, newest first."""
        if not os.path.isdir(self.backup_dir):
            return []
        return sorted((f for f in os.listdir(self.backup_dir) if f.endswith(".csv")),
                      reverse=True)

    def restore_backup(self, backup_filename):
        """Restore from a backup. The current data is backed up first so a
        restore can always be undone."""
        # Only plain file names are allowed (blocks '../' tricks).
        if os.path.basename(backup_filename) != backup_filename:
            raise FileManagerError("Invalid backup name.")
        backup_path = os.path.join(self.backup_dir, backup_filename)
        if not os.path.isfile(backup_path):
            raise FileManagerError(f"Backup '{backup_filename}' not found.")
        if os.path.exists(self.data_file):
            self.create_backup()
        try:
            shutil.copy2(backup_path, self.data_file)
        except OSError as exc:
            raise FileManagerError(f"Restore failed: {exc}")

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------
    def export_report(self, text, prefix="report"):
        try:
            os.makedirs(self.reports_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.reports_dir, f"{prefix}_{stamp}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as exc:
            raise FileManagerError(f"Failed to write report: {exc}")
        return path

    def export_csv_copy(self, expenses, path):
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._write_csv(path, expenses)
        except OSError as exc:
            raise FileManagerError(f"Failed to export CSV to '{path}': {exc}")
        return path
