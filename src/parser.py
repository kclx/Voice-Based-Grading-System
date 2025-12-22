"""Text parsing module to extract name and scores from speech."""

import re
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from config import CORRECT_KEYWORDS, WRONG_KEYWORDS
from src.utils import safe_int_conversion, normalize_chinese_text


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
    Parser for extracting structured data from speech text.

    Expected formats:
    - "姓名 + 对/正确 + 数字 + 错/错误 + 数字"
    - "杨洋 对 18 错 2"
    - "张三 正确 20 错误 0"
    """

    def __init__(self):
        """Initialize the parser with logging."""
        self.logger = logging.getLogger(__name__)

        # Build regex patterns for matching
        correct_pattern = "|".join(CORRECT_KEYWORDS)
        wrong_pattern = "|".join(WRONG_KEYWORDS)

        # Pattern: [name] [correct_keyword] [number] [wrong_keyword] [number]
        # Flexible spacing and number formats (Arabic or Chinese)
        self.pattern = re.compile(
            rf"^(.+?)\s*(?:{correct_pattern})\s*(\d+|[零一二三四五六七八九十百千万]+)\s*(?:{wrong_pattern})\s*(\d+|[零一二三四五六七八九十百千万]+)$"
        )

    def parse(self, text: str) -> Optional[GradeEntry]:
        """
        Parse speech text into a GradeEntry.

        Args:
            text: Recognized speech text

        Returns:
            Optional[GradeEntry]: Parsed entry or None if parsing fails
        """
        # Normalize text
        text = normalize_chinese_text(text)
        self.logger.debug(f"Parsing text: '{text}'")

        # Try to match the pattern
        match = self.pattern.match(text)
        if not match:
            self.logger.warning(f"Text does not match expected format: '{text}'")
            return None

        # Extract components
        name = match.group(1).strip()
        correct_str = match.group(2).strip()
        wrong_str = match.group(3).strip()

        # Convert numbers
        correct = safe_int_conversion(correct_str)
        wrong = safe_int_conversion(wrong_str)

        if correct is None or wrong is None:
            self.logger.error(f"Failed to convert numbers: correct='{correct_str}', wrong='{wrong_str}'")
            return None

        # Validate numbers
        if correct < 0 or wrong < 0:
            self.logger.error(f"Invalid negative numbers: correct={correct}, wrong={wrong}")
            return None

        entry = GradeEntry(name=name, correct=correct, wrong=wrong)
        self.logger.info(f"Successfully parsed: {entry}")
        return entry

    def validate_format(self, text: str) -> Tuple[bool, str]:
        """
        Validate if text matches expected format and provide feedback.

        Args:
            text: Speech text to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        text = normalize_chinese_text(text)

        # Check if any correct keyword present
        has_correct = any(kw in text for kw in CORRECT_KEYWORDS)
        if not has_correct:
            return False, f"Missing correct keyword ({'/'.join(CORRECT_KEYWORDS)})"

        # Check if any wrong keyword present
        has_wrong = any(kw in text for kw in WRONG_KEYWORDS)
        if not has_wrong:
            return False, f"Missing wrong keyword ({'/'.join(WRONG_KEYWORDS)})"

        # Check pattern match
        if not self.pattern.match(text):
            return False, "Format does not match: 姓名 + 对/正确 + 数字 + 错/错误 + 数字"

        return True, ""
