"""Configuration constants for the voice marking system."""

# CSV Configuration
CSV_FILE_PATH = "students.csv"
CSV_COLUMNS = ["name", "correct", "wrong"]

# Speech Recognition Configuration
SPEECH_ENGINE = "google"  # Using Google Speech Recognition
LANGUAGE = "zh-CN"  # Chinese (Simplified)
ENERGY_THRESHOLD = 4000  # Adjust based on classroom noise
PAUSE_THRESHOLD = 0.8  # Seconds of silence before considering phrase complete
PHRASE_TIME_LIMIT = 5  # Maximum seconds for a single phrase

# Name Matching Configuration
LEVENSHTEIN_THRESHOLD = 1  # Maximum edit distance for fuzzy matching
MATCH_PRIORITY = {
    "exact": 1,
    "pinyin_exact": 2,
    "pinyin_fuzzy": 3
}

# Logging Configuration
LOG_FILE = "logs/voice_marking.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Parser Configuration
CORRECT_KEYWORDS = ["对", "正确"]
WRONG_KEYWORDS = ["错", "错误"]
