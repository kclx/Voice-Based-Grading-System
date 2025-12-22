"""CSV file operations for reading and updating student grades."""

import pandas as pd
import logging
import os
from typing import List, Optional
from threading import Lock
from config import CSV_FILE_PATH, CSV_COLUMNS
from src.parser import GradeEntry
from src.utils import validate_csv_structure


class CSVUpdater:
    """
    Thread-safe CSV file operations for student grades.

    Features:
    - Load and validate CSV structure
    - Update student records atomically
    - Create backup before updates
    - Thread-safe operations
    """

    def __init__(self, csv_path: str = CSV_FILE_PATH):
        """
        Initialize CSV updater.

        Args:
            csv_path: Path to CSV file
        """
        self.csv_path = csv_path
        self.logger = logging.getLogger(__name__)
        self.lock = Lock()  # Thread safety for concurrent updates
        self.df = None

        # Load CSV on initialization
        self.reload()

    def reload(self):
        """Load or reload CSV file."""
        try:
            if not os.path.exists(self.csv_path):
                raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

            self.df = pd.read_csv(self.csv_path, encoding='utf-8')

            # Validate structure
            if not validate_csv_structure(self.df, CSV_COLUMNS):
                raise ValueError(
                    f"CSV missing required columns. Expected: {CSV_COLUMNS}, "
                    f"Found: {list(self.df.columns)}"
                )

            # Ensure correct column types
            self.df['correct'] = pd.to_numeric(self.df['correct'], errors='coerce').fillna(0).astype(int)
            self.df['wrong'] = pd.to_numeric(self.df['wrong'], errors='coerce').fillna(0).astype(int)

            self.logger.info(f"CSV loaded successfully: {len(self.df)} students")

        except Exception as e:
            self.logger.error(f"Failed to load CSV: {e}")
            raise

    def get_student_names(self) -> List[str]:
        """
        Get list of all student names.

        Returns:
            List[str]: List of student names
        """
        if self.df is None:
            return []
        return self.df['name'].tolist()

    def get_student_record(self, name: str) -> Optional[dict]:
        """
        Get current record for a student.

        Args:
            name: Student name

        Returns:
            Optional[dict]: Student record or None if not found
        """
        if self.df is None:
            return None

        matches = self.df[self.df['name'] == name]
        if len(matches) == 0:
            return None

        row = matches.iloc[0]
        return {
            'name': row['name'],
            'correct': int(row['correct']),
            'wrong': int(row['wrong'])
        }

    def update_student(self, entry: GradeEntry) -> bool:
        """
        Update student record with new grades.

        Args:
            entry: GradeEntry with student name and scores

        Returns:
            bool: True if update successful, False otherwise
        """
        with self.lock:
            try:
                # Find student index
                student_idx = self.df[self.df['name'] == entry.name].index

                if len(student_idx) == 0:
                    self.logger.error(f"Student not found in CSV: '{entry.name}'")
                    return False

                if len(student_idx) > 1:
                    self.logger.warning(f"Duplicate student entries found: '{entry.name}'. Updating first occurrence.")

                idx = student_idx[0]

                # Get old values for logging
                old_correct = int(self.df.loc[idx, 'correct'])
                old_wrong = int(self.df.loc[idx, 'wrong'])

                # Update values
                self.df.loc[idx, 'correct'] = entry.correct
                self.df.loc[idx, 'wrong'] = entry.wrong

                # Save to file
                self.df.to_csv(self.csv_path, index=False, encoding='utf-8')

                self.logger.info(
                    f"Updated '{entry.name}': "
                    f"correct {old_correct}->{entry.correct}, "
                    f"wrong {old_wrong}->{entry.wrong}"
                )

                return True

            except Exception as e:
                self.logger.error(f"Failed to update student '{entry.name}': {e}")
                return False

    def create_backup(self, backup_suffix: str = None):
        """
        Create a backup of the current CSV file.

        Args:
            backup_suffix: Optional suffix for backup file (default: timestamp)
        """
        if not os.path.exists(self.csv_path):
            return

        if backup_suffix is None:
            from datetime import datetime
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = f"{self.csv_path}.backup_{backup_suffix}"

        try:
            import shutil
            shutil.copy2(self.csv_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")

    def get_statistics(self) -> dict:
        """
        Get summary statistics from CSV.

        Returns:
            dict: Statistics including total students, total correct, total wrong
        """
        if self.df is None:
            return {}

        return {
            'total_students': len(self.df),
            'total_correct': int(self.df['correct'].sum()),
            'total_wrong': int(self.df['wrong'].sum()),
            'avg_correct': float(self.df['correct'].mean()),
            'avg_wrong': float(self.df['wrong'].mean())
        }
