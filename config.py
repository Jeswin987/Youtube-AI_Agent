"""
Configuration file for YouTube Agent
Store your settings and API keys here
"""

class Config:
   
    
    LLM_PROVIDER = "ollama"  
    
    
    GROQ_API_KEY = "your_groq_api_key_here"
    
   
    GROQ_MODEL = "llama-3.1-70b"
    
   
    OLLAMA_MODEL = "llama3.1:8b"
    
    OLLAMA_URL = "http://localhost:11434/api/generate"
    
   
    MAX_TRANSCRIPT_LENGTH = 15000
    
   
    SUMMARY_WORD_COUNT = "300-400"
    
    
    NUM_TIMESTAMPS = "5-7"
    
    NUM_THEMES = "3-5"
    
   
    TEMPERATURE = 0.7
    
    
    MAX_TOKENS = 2000
    
    
    ENABLE_DYNAMIC_WORD_COUNT = True
    
    
    DYNAMIC_WORD_COUNT_RULES = {
        5: "100-150",   
        10: "200-300",   
        20: "300-400",   
        40: "400-500",  
        999: "500-600"
    }
    
   
    SAVE_TO_JSON = True
    
    JSON_FILENAME_PATTERN = "analysis_{timestamp}.json"
    
    DEBUG_MODE = True
    
    
    WORD_COUNT_TRIM_THRESHOLD = 1.3
    
    
    MIN_SUMMARY_RETENTION = 0.7


