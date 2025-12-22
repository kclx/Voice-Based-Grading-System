"""Utility functions for logging, validation, and common operations."""

import logging
import os
from typing import Optional
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration for the application.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


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


def normalize_chinese_text(text: str) -> str:
    """
    Normalize Chinese text by removing extra spaces and standardizing format.

    Args:
        text: Input text

    Returns:
        str: Normalized text
    """
    return ' '.join(text.split())


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
