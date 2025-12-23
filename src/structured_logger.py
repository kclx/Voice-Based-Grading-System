"""Structured logging utility for voice marking system.

This module provides JSON-based structured logging for all critical stages
of the voice recognition and grading pipeline.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum


class Stage(str, Enum):
    """Processing stages for structured logging."""

    # ASR Stage
    ASR_OUTPUT = "ASR_OUTPUT"

    # Text Processing
    TEXT_NORMALIZE = "TEXT_NORMALIZE"

    # Parser Stage
    PARSE_SUCCESS = "PARSE_SUCCESS"
    PARSE_FAIL = "PARSE_FAIL"

    # Name Matching Stages
    NAME_MATCH_EXACT = "NAME_MATCH_EXACT"
    NAME_MATCH_PINYIN_EXACT = "NAME_MATCH_PINYIN_EXACT"
    NAME_MATCH_PINYIN_CONTAINS = "NAME_MATCH_PINYIN_CONTAINS"
    NAME_MATCH_FUZZY = "NAME_MATCH_FUZZY"
    NAME_MATCH_AMBIGUOUS = "NAME_MATCH_AMBIGUOUS"
    NAME_MATCH_FAIL = "NAME_MATCH_FAIL"

    # Alias/Mapping (future)
    NAME_ALIAS_APPLIED = "NAME_ALIAS_APPLIED"

    # CSV Update
    CSV_UPDATE_SUCCESS = "CSV_UPDATE_SUCCESS"
    CSV_UPDATE_FAIL = "CSV_UPDATE_FAIL"


class StructuredLogger:
    """
    JSON-based structured logger for the voice marking system.

    All logs are emitted as valid JSON with standard fields:
    - timestamp: ISO format timestamp
    - stage: Processing stage (from Stage enum)
    - Additional context-specific fields
    """

    def __init__(self, name: str):
        """Initialize structured logger.

        Args:
            name: Logger name (typically module name)
        """
        self.logger = logging.getLogger(name)
        self.name = name

    def _log_structured(self, level: int, stage: Stage, data: Dict[str, Any]) -> None:
        """
        Log a structured JSON entry.

        Args:
            level: Logging level (logging.INFO, logging.WARNING, etc.)
            stage: Processing stage
            data: Additional data fields to include
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage.value,
            "logger": self.name,
            **data
        }

        # Convert to JSON string
        json_str = json.dumps(log_entry, ensure_ascii=False)
        self.logger.log(level, json_str)

    # ==================== ASR Stage ====================

    def log_asr_output(
        self,
        raw_input: str,
        engine: str = "google",
        confidence: Optional[float] = None
    ) -> None:
        """Log ASR output.

        Args:
            raw_input: Raw ASR recognized text
            engine: Recognition engine used
            confidence: Recognition confidence (if available)
        """
        data = {
            "raw_input": raw_input,
            "engine": engine
        }
        if confidence is not None:
            data["confidence"] = confidence

        self._log_structured(logging.INFO, Stage.ASR_OUTPUT, data)

    # ==================== Text Normalization ====================

    def log_text_normalize(
        self,
        raw_input: str,
        normalized_input: str,
        removed_tokens: Optional[List[str]] = None
    ) -> None:
        """Log text normalization (before/after cleaning).

        Args:
            raw_input: Original text
            normalized_input: Normalized text
            removed_tokens: List of tokens that were removed
        """
        data = {
            "raw_input": raw_input,
            "normalized_input": normalized_input,
            "removed_tokens": removed_tokens or []
        }

        self._log_structured(logging.INFO, Stage.TEXT_NORMALIZE, data)

    # ==================== Parser Stage ====================

    def log_parse_success(
        self,
        raw_input: str,
        name: str,
        correct: int,
        wrong: int
    ) -> None:
        """Log successful parsing.

        Args:
            raw_input: Original input text
            name: Extracted name
            correct: Correct count
            wrong: Wrong count
        """
        data = {
            "raw_input": raw_input,
            "name": name,
            "correct": correct,
            "wrong": wrong
        }

        self._log_structured(logging.INFO, Stage.PARSE_SUCCESS, data)

    def log_parse_fail(
        self,
        raw_input: str,
        reason: str,
        missing_fields: Optional[List[str]] = None
    ) -> None:
        """Log parsing failure with detailed reason.

        Args:
            raw_input: Original input text
            reason: Failure reason (e.g., "missing_correct", "missing_wrong", "no_numbers", "regex_mismatch")
            missing_fields: List of missing fields
        """
        data = {
            "raw_input": raw_input,
            "reason": reason,
            "missing_fields": missing_fields or []
        }

        self._log_structured(logging.WARNING, Stage.PARSE_FAIL, data)

    # ==================== Name Matching Stages ====================

    def log_name_match_exact(
        self,
        input_name: str,
        matched_name: str
    ) -> None:
        """Log exact name match.

        Args:
            input_name: Input name from ASR
            matched_name: Matched student name
        """
        data = {
            "input_name": input_name,
            "matched_name": matched_name
        }

        self._log_structured(logging.INFO, Stage.NAME_MATCH_EXACT, data)

    def log_name_match_pinyin_exact(
        self,
        input_name: str,
        input_pinyin: str,
        matched_name: str,
        matched_pinyin: str
    ) -> None:
        """Log pinyin exact match.

        Args:
            input_name: Input name from ASR
            input_pinyin: Input name's pinyin
            matched_name: Matched student name
            matched_pinyin: Matched student's pinyin
        """
        data = {
            "input_name": input_name,
            "input_pinyin": input_pinyin,
            "matched_name": matched_name,
            "matched_pinyin": matched_pinyin
        }

        self._log_structured(logging.INFO, Stage.NAME_MATCH_PINYIN_EXACT, data)

    def log_name_match_pinyin_contains(
        self,
        input_name: str,
        input_pinyin: str,
        matched_name: str,
        matched_pinyin: str
    ) -> None:
        """Log pinyin contains match.

        Args:
            input_name: Input name from ASR
            input_pinyin: Input name's pinyin
            matched_name: Matched student name
            matched_pinyin: Matched student's pinyin
        """
        data = {
            "input_name": input_name,
            "input_pinyin": input_pinyin,
            "matched_name": matched_name,
            "matched_pinyin": matched_pinyin
        }

        self._log_structured(logging.INFO, Stage.NAME_MATCH_PINYIN_CONTAINS, data)

    def log_name_match_fuzzy(
        self,
        input_name: str,
        input_pinyin: str,
        matched_name: str,
        all_candidates: List[tuple]  # [(name, distance), ...]
    ) -> None:
        """Log fuzzy match with ALL candidates.

        Args:
            input_name: Input name from ASR
            input_pinyin: Input name's pinyin
            matched_name: Final matched student name
            all_candidates: All fuzzy match candidates with distances
        """
        data = {
            "input_name": input_name,
            "input_pinyin": input_pinyin,
            "matched_name": matched_name,
            "candidate_count": len(all_candidates),
            "candidates": [
                {"name": name, "distance": dist}
                for name, dist in all_candidates
            ]
        }

        self._log_structured(logging.INFO, Stage.NAME_MATCH_FUZZY, data)

    def log_name_match_ambiguous(
        self,
        input_name: str,
        input_pinyin: str,
        candidates: List[tuple]  # [(name, distance), ...]
    ) -> None:
        """Log ambiguous match (multiple equal-distance candidates).

        Args:
            input_name: Input name from ASR
            input_pinyin: Input name's pinyin
            candidates: All ambiguous candidates
        """
        data = {
            "input_name": input_name,
            "input_pinyin": input_pinyin,
            "candidate_count": len(candidates),
            "candidates": [
                {"name": name, "distance": dist}
                for name, dist in candidates
            ]
        }

        self._log_structured(logging.WARNING, Stage.NAME_MATCH_AMBIGUOUS, data)

    def log_name_match_fail(
        self,
        input_name: str,
        input_pinyin: str,
        top_candidates: Optional[List[tuple]] = None
    ) -> None:
        """Log name matching failure.

        Args:
            input_name: Input name from ASR
            input_pinyin: Input name's pinyin
            top_candidates: Top N closest candidates (even if beyond threshold)
        """
        data = {
            "input_name": input_name,
            "input_pinyin": input_pinyin,
            "top_candidates": [
                {"name": name, "distance": dist}
                for name, dist in (top_candidates or [])
            ]
        }

        self._log_structured(logging.WARNING, Stage.NAME_MATCH_FAIL, data)

    # ==================== Alias Mapping (Future) ====================

    def log_alias_applied(
        self,
        raw_input: str,
        alias_from: str,
        alias_to: str
    ) -> None:
        """Log alias mapping application.

        Args:
            raw_input: Original input
            alias_from: Alias source
            alias_to: Alias target
        """
        data = {
            "raw_input": raw_input,
            "alias_from": alias_from,
            "alias_to": alias_to
        }

        self._log_structured(logging.INFO, Stage.NAME_ALIAS_APPLIED, data)

    # ==================== CSV Update ====================

    def log_csv_update_success(
        self,
        student_name: str,
        correct_delta: int,
        wrong_delta: int,
        new_correct: int,
        new_wrong: int
    ) -> None:
        """Log successful CSV update.

        Args:
            student_name: Student name
            correct_delta: Change in correct count
            wrong_delta: Change in wrong count
            new_correct: New total correct count
            new_wrong: New total wrong count
        """
        data = {
            "student_name": student_name,
            "correct_delta": correct_delta,
            "wrong_delta": wrong_delta,
            "new_correct": new_correct,
            "new_wrong": new_wrong
        }

        self._log_structured(logging.INFO, Stage.CSV_UPDATE_SUCCESS, data)

    def log_csv_update_fail(
        self,
        student_name: str,
        reason: str,
        row_index: Optional[int] = None
    ) -> None:
        """Log CSV update failure.

        Args:
            student_name: Student name
            reason: Failure reason
            row_index: Row index in CSV (if applicable)
        """
        data = {
            "student_name": student_name,
            "reason": reason
        }
        if row_index is not None:
            data["row_index"] = row_index

        self._log_structured(logging.ERROR, Stage.CSV_UPDATE_FAIL, data)
