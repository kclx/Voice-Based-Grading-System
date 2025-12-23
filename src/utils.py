"""Utility functions for logging, validation, and common operations."""

import logging
import os
from datetime import datetime
from typing import Optional, List
from config import LOG_DIR, LOG_FILE_PREFIX, LOG_LEVEL, LOG_FORMAT, ENABLE_STRUCTURED_LOGGING


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration for the application with daily rotation.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # Generate daily log file name: voice_marking-YYYY-MM-DD.log
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"{LOG_FILE_PREFIX}-{today}.log")

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - File: {log_file}, Structured: {ENABLE_STRUCTURED_LOGGING}")

    return logger


def validate_csv_structure(df, required_columns: list) -> bool:
    """
    Validate that CSV has required columns.

    Args:
        df: pandas DataFrame
        required_columns: List of required column names

    Returns:
        bool: True if valid, False otherwise
    """
    return all(col in df.columns for col in required_columns)


def normalize_chinese_text(text: str, track_removed: bool = False) -> tuple[str, List[str]] | str:
    """
    Normalize Chinese text by removing extra spaces and standardizing format.

    Args:
        text: Input text
        track_removed: If True, return (normalized_text, removed_tokens)

    Returns:
        str or tuple: Normalized text, or (normalized_text, removed_tokens) if track_removed=True
    """
    # For now, simple whitespace normalization
    # Future: could track specific removed tokens
    normalized = ' '.join(text.split())

    if track_removed:
        # Calculate what was removed (simplified - just extra spaces for now)
        removed = []
        if text != normalized:
            removed.append("extra_whitespace")
        return normalized, removed

    return normalized


def safe_int_conversion(value: str) -> Optional[int]:
    """
    Safely convert string to integer, handling Chinese numbers.

    Args:
        value: String value to convert

    Returns:
        Optional[int]: Converted integer or None if conversion fails
    """
    try:
        # Try direct conversion first
        return int(value)
    except ValueError:
        # Try Chinese number conversion
        try:
            import cn2an
            return cn2an.cn2an(value, "smart")
        except Exception:
            return None
