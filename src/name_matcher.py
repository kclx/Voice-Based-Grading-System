"""Name matching module with exact, pinyin, and fuzzy matching."""

import logging
from typing import List, Optional, Tuple
from pypinyin import lazy_pinyin
import Levenshtein
from config import LEVENSHTEIN_THRESHOLD, MATCH_PRIORITY, ENABLE_STRUCTURED_LOGGING
from src.structured_logger import StructuredLogger

NAME_NOISE_WORDS = ["证券", "队伍", "实物", "成绩", "同学", "同学的", "的"]


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
        self.structured_logger = StructuredLogger(__name__)
        self.student_names = student_names

        # Pre-compute pinyin for all students for efficiency
        self.name_to_pinyin = {name: self._get_pinyin(name) for name in student_names}

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
        return "".join(lazy_pinyin(name)).lower()

    def find_match(self, input_name: str) -> Tuple[Optional[str], Optional[str]]:
        original_input = input_name
        input_name = self._clean_input_name(input_name)

        # 1. Exact Chinese
        if input_name in self.student_names:
            if ENABLE_STRUCTURED_LOGGING:
                self.structured_logger.log_name_match_exact(
                    input_name=original_input,
                    matched_name=input_name
                )
            return input_name, "exact"

        input_pinyin = self._get_pinyin(input_name)

        # 2. Exact pinyin
        for name, pinyin in self.name_to_pinyin.items():
            if input_pinyin == pinyin:
                if ENABLE_STRUCTURED_LOGGING:
                    self.structured_logger.log_name_match_pinyin_exact(
                        input_name=original_input,
                        input_pinyin=input_pinyin,
                        matched_name=name,
                        matched_pinyin=pinyin
                    )
                return name, "pinyin_exact"

        # 3. Pinyin contains (VERY IMPORTANT)
        for name, pinyin in self.name_to_pinyin.items():
            if input_pinyin.startswith(pinyin) or pinyin.startswith(input_pinyin):
                if ENABLE_STRUCTURED_LOGGING:
                    self.structured_logger.log_name_match_pinyin_contains(
                        input_name=original_input,
                        input_pinyin=input_pinyin,
                        matched_name=name,
                        matched_pinyin=pinyin
                    )
                return name, "pinyin_contains"

        # 4. Fuzzy pinyin
        candidates = []
        for name, pinyin in self.name_to_pinyin.items():
            dist = Levenshtein.distance(input_pinyin, pinyin)
            if dist <= 2:
                candidates.append((name, dist))

        if not candidates:
            # Get top 3 closest candidates for logging (even beyond threshold)
            all_candidates = []
            for name, pinyin in self.name_to_pinyin.items():
                dist = Levenshtein.distance(input_pinyin, pinyin)
                all_candidates.append((name, dist))
            all_candidates.sort(key=lambda x: x[1])
            top_candidates = all_candidates[:3]

            if ENABLE_STRUCTURED_LOGGING:
                self.structured_logger.log_name_match_fail(
                    input_name=original_input,
                    input_pinyin=input_pinyin,
                    top_candidates=top_candidates
                )
            return None, None

        candidates.sort(key=lambda x: x[1])

        # Check for ambiguity
        if len(candidates) > 1 and candidates[0][1] == candidates[1][1]:
            # Multiple equal-distance candidates
            ambiguous_candidates = [c for c in candidates if c[1] == candidates[0][1]]
            if ENABLE_STRUCTURED_LOGGING:
                self.structured_logger.log_name_match_ambiguous(
                    input_name=original_input,
                    input_pinyin=input_pinyin,
                    candidates=ambiguous_candidates
                )
            return None, "ambiguous"

        # Successful fuzzy match - log ALL candidates, not just the winner
        matched_name = candidates[0][0]
        if ENABLE_STRUCTURED_LOGGING:
            self.structured_logger.log_name_match_fuzzy(
                input_name=original_input,
                input_pinyin=input_pinyin,
                matched_name=matched_name,
                all_candidates=candidates  # Log ALL candidates
            )

        return matched_name, "pinyin_fuzzy"

    def find_all_similar(
        self, input_name: str, max_distance: int = 2
    ) -> List[Tuple[str, int]]:
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
        self.name_to_pinyin = {name: self._get_pinyin(name) for name in new_names}
        self.logger.info(f"Updated student list: {len(new_names)} students")

    def _clean_input_name(self, name: str) -> str:
        cleaned = name
        for noise in NAME_NOISE_WORDS:
            cleaned = cleaned.replace(noise, "")
        return cleaned.strip()
