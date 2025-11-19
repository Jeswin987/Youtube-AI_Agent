import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core provider settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")  # 'google', 'groq', or 'ollama'
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # Model configurations
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")

    # Processing parameters
    MAX_TRANSCRIPT_LENGTH = 15000
    SUMMARY_WORD_COUNT = "300-400"
    NUM_TIMESTAMPS = "5-7"
    NUM_THEMES = "3-5"

    # LLM behavior
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2000))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

    # Summary customization
    ENABLE_DYNAMIC_WORD_COUNT = True
    DYNAMIC_WORD_COUNT_RULES = {
        5: "100-150",
        10: "200-300",
        20: "300-400",
        40: "400-500",
        999: "500-600",
    }

    # Authentication helpers
    YOUTUBE_COOKIES_FILE = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()

    # Output settings
    SAVE_TO_JSON = True
    JSON_FILENAME_PATTERN = "analysis_{timestamp}.json"
    WORD_COUNT_TRIM_THRESHOLD = 1.3
    MIN_SUMMARY_RETENTION = 0.7
