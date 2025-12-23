"""Configuration constants for the voice marking system."""

# CSV Configuration
CSV_FILE_PATH = "students.csv"
CSV_COLUMNS = ["name", "correct", "wrong"]

# Speech Recognition Configuration
SPEECH_ENGINE = "google"  # Using Google Speech Recognition
LANGUAGE = "zh-CN"  # Chinese (Simplified)
ENERGY_THRESHOLD = 1000  # Adjust based on classroom noise
PAUSE_THRESHOLD = 2  # Seconds of silence before considering phrase complete
PHRASE_TIME_LIMIT = 5  # Maximum seconds for a single phrase

# Name Matching Configuration
LEVENSHTEIN_THRESHOLD = 2  # Maximum edit distance for fuzzy matching
MATCH_PRIORITY = {
    "exact": 1,
    "pinyin_exact": 2,
    "pinyin_fuzzy": 3
}

# Logging Configuration
LOG_DIR = "logs"
LOG_FILE_PREFIX = "voice_marking"  # Will be formatted as: voice_marking-YYYY-MM-DD.log
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ENABLE_STRUCTURED_LOGGING = True  # Enable JSON structured logging

# Parser Configuration
CORRECT_KEYWORDS = ["对", "正确"]
WRONG_KEYWORDS = ["错", "错误"]
