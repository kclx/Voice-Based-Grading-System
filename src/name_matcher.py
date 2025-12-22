"""Name matching module with exact, pinyin, and fuzzy matching."""

import logging
from typing import List, Optional, Tuple
from pypinyin import lazy_pinyin
import Levenshtein
from config import LEVENSHTEIN_THRESHOLD, MATCH_PRIORITY


class NameMatcher:
    """
    Name matching system with multiple strategies.

    Matching Priority:
    1. Exact Chinese name match
    2. Exact Pinyin match
    3. Fuzzy Pinyin match (Levenshtein distance ≤ 1)
    """

    def __init__(self, student_names: List[str]):
        """
        Initialize name matcher with list of valid student names.

        Args:
            student_names: List of student names from CSV
        """
        self.logger = logging.getLogger(__name__)
        self.student_names = student_names

        # Pre-compute pinyin for all students for efficiency
        self.name_to_pinyin = {
            name: self._get_pinyin(name) for name in student_names
        }

        self.logger.info(f"Initialized NameMatcher with {len(student_names)} students")

    @staticmethod
    def _get_pinyin(name: str) -> str:
        """
        Convert Chinese name to pinyin (lowercase, no tones).

        Args:
            name: Chinese name

        Returns:
            str: Pinyin representation
        """
        # Use lazy_pinyin to get pinyin without tones
        # Join without spaces for easier matching
        return ''.join(lazy_pinyin(name)).lower()

    def find_match(self, input_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the best match for input name using priority-based matching.

        Args:
            input_name: Name to match (from speech recognition)

        Returns:
            Tuple[Optional[str], Optional[str]]: (matched_name, match_type) or (None, None)
            match_type can be: 'exact', 'pinyin_exact', 'pinyin_fuzzy', or None
        """
        # Priority 1: Exact match
        if input_name in self.student_names:
            self.logger.info(f"Exact match found: '{input_name}'")
            return input_name, 'exact'

        # Priority 2: Exact pinyin match
        input_pinyin = self._get_pinyin(input_name)
        for name, pinyin in self.name_to_pinyin.items():
            if input_pinyin == pinyin:
                self.logger.info(f"Exact pinyin match: '{input_name}' -> '{name}'")
                return name, 'pinyin_exact'

        # Priority 3: Fuzzy pinyin match
        candidates = []
        for name, pinyin in self.name_to_pinyin.items():
            distance = Levenshtein.distance(input_pinyin, pinyin)
            if distance <= LEVENSHTEIN_THRESHOLD:
                candidates.append((name, distance))

        if candidates:
            # Sort by distance (lower is better)
            candidates.sort(key=lambda x: x[1])

            # Check for multiple matches with same distance
            best_distance = candidates[0][1]
            best_matches = [c for c in candidates if c[1] == best_distance]

            if len(best_matches) > 1:
                # Multiple equally good matches - ambiguous
                names = [m[0] for m in best_matches]
                self.logger.warning(
                    f"Ambiguous fuzzy match for '{input_name}': {names}. "
                    f"Distance: {best_distance}"
                )
                return None, 'ambiguous'

            matched_name = candidates[0][0]
            self.logger.info(
                f"Fuzzy pinyin match: '{input_name}' -> '{matched_name}' "
                f"(distance: {best_distance})"
            )
            return matched_name, 'pinyin_fuzzy'

        # No match found
        self.logger.warning(f"No match found for: '{input_name}'")
        return None, None

    def find_all_similar(self, input_name: str, max_distance: int = 2) -> List[Tuple[str, int]]:
        """
        Find all similar names for debugging or user feedback.

        Args:
            input_name: Name to match
            max_distance: Maximum Levenshtein distance

        Returns:
            List[Tuple[str, int]]: List of (name, distance) sorted by distance
        """
        input_pinyin = self._get_pinyin(input_name)
        candidates = []

        for name, pinyin in self.name_to_pinyin.items():
            distance = Levenshtein.distance(input_pinyin, pinyin)
            if distance <= max_distance:
                candidates.append((name, distance))

        candidates.sort(key=lambda x: x[1])
        return candidates

    def update_student_list(self, new_names: List[str]):
        """
        Update the student list (e.g., when CSV is reloaded).

        Args:
            new_names: Updated list of student names
        """
        self.student_names = new_names
        self.name_to_pinyin = {
            name: self._get_pinyin(name) for name in new_names
        }
        self.logger.info(f"Updated student list: {len(new_names)} students")
