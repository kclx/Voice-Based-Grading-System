"""Text parsing module to extract name and scores from speech."""

import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from config import CORRECT_KEYWORDS, WRONG_KEYWORDS, ENABLE_STRUCTURED_LOGGING
from src.utils import safe_int_conversion, normalize_chinese_text
from src.structured_logger import StructuredLogger


@dataclass
class GradeEntry:
    """Data class for a parsed grade entry."""

    name: str
    correct: int
    wrong: int

    def __str__(self):
        return f"GradeEntry(name='{self.name}', correct={self.correct}, wrong={self.wrong})"


class SpeechParser:
    """
    Robust parser for extracting grading information from noisy speech text.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.structured_logger = StructuredLogger(__name__)

        correct_pattern = "|".join(CORRECT_KEYWORDS)
        wrong_pattern = "|".join(WRONG_KEYWORDS)

        # 提取 “数字 + 对/错” 或 “对/错 + 数字”
        self.correct_regex = re.compile(
            rf"(?:({correct_pattern})\s*(\d+|[零一二三四五六七八九十百千万]+)|(\d+|[零一二三四五六七八九十百千万]+)\s*(?:{correct_pattern}))"
        )

        self.wrong_regex = re.compile(
            rf"(?:({wrong_pattern})\s*(\d+|[零一二三四五六七八九十百千万]+)|(\d+|[零一二三四五六七八九十百千万]+)\s*(?:{wrong_pattern}))"
        )

    def _extract_count(self, regex: re.Pattern, text: str) -> Optional[int]:
        match = regex.search(text)
        if not match:
            return None

        # 数字可能在 group(2) 或 group(3)
        num_str = match.group(2) or match.group(3)
        return safe_int_conversion(num_str)

    def parse(self, text: str) -> Optional[GradeEntry]:
        raw_input = text
        normalized_text, removed_tokens = normalize_chinese_text(text, track_removed=True)
        text = normalized_text

        # Structured logging: Text normalization
        if ENABLE_STRUCTURED_LOGGING:
            self.structured_logger.log_text_normalize(
                raw_input=raw_input,
                normalized_input=normalized_text,
                removed_tokens=removed_tokens
            )

        self.logger.debug(f"Parsing text: '{text}'")

        # 1️⃣ 提取数量（允许缺失其一）
        correct = self._extract_count(self.correct_regex, text)
        wrong = self._extract_count(self.wrong_regex, text)

        if correct is None and wrong is None:
            self.logger.warning("No correct or wrong count detected")

            # Structured logging: Parse failure
            if ENABLE_STRUCTURED_LOGGING:
                self.structured_logger.log_parse_fail(
                    raw_input=raw_input,
                    reason="missing_both_counts",
                    missing_fields=["correct", "wrong"]
                )
            return None

        # 2️⃣ 姓名：暂时取"最前面的非数字非关键词部分"
        name_candidate = re.split(r"\d|对|正确|错|错误", text, maxsplit=1)[0].strip()

        if not name_candidate:
            self.logger.warning("Failed to extract name candidate")

            # Structured logging: Parse failure
            if ENABLE_STRUCTURED_LOGGING:
                self.structured_logger.log_parse_fail(
                    raw_input=raw_input,
                    reason="no_name_extracted",
                    missing_fields=["name"]
                )
            return None

        entry = GradeEntry(name=name_candidate, correct=correct or 0, wrong=wrong or 0)

        self.logger.info(f"Parsed entry: {entry}")

        # Structured logging: Parse success
        if ENABLE_STRUCTURED_LOGGING:
            self.structured_logger.log_parse_success(
                raw_input=raw_input,
                name=entry.name,
                correct=entry.correct,
                wrong=entry.wrong
            )

        return entry
