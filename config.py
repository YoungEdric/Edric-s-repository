# config.py - Configuration file for Sarah AI Assistant

# User Configuration
USER_NAME = "User"  # Your name - Sarah will use this to address you
WAKE_WORDS = ["sarah", "hey sarah", "ok sarah"]  # Words that activate Sarah

# Voice Settings
VOICE_RATE = 180  # Speech speed (words per minute)
VOICE_VOLUME = 0.9  # Volume level (0.0 to 1.0)
VOICE_ID = 0  # Voice ID (0 for default, 1 for alternate if available)

# OpenAI Configuration
OPENAI_API_KEY = "your-openai-api-key-here"  # Get from https://platform.openai.com/
OPENAI_MODEL = "gpt-3.5-turbo"  # or "gpt-4" if you have access

# Email Configuration (Gmail)
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Use Gmail App Password, not regular password
DEFAULT_EMAIL_RECIPIENT = "recipient@example.com"

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"  # Get from @BotFather on Telegram
TELEGRAM_CHAT_ID = "your-chat-id"  # Your Telegram chat ID

# WhatsApp Configuration (via pywhatkit)
WHATSAPP_DEFAULT_CONTACT = "+1234567890"  # Default contact number with country code

# Computer Vision Settings
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows path
# TESSERACT_PATH = "/usr/bin/tesseract"  # Linux/Mac path

# Security Settings
SECURITY_SCAN_INTERVAL = 300  # Seconds between security scans (5 minutes)
SUSPICIOUS_PROCESSES = [
    "keylogger", "trojan", "malware", "virus", 
    "backdoor", "rootkit", "spyware"
]

# Automation Settings
MORNING_ROUTINE_APPS = [
    "chrome.exe",
    "outlook.exe",
    "spotify.exe"
]

# Media Settings
YOUTUBE_SEARCH_RESULTS = 1  # Number of YouTube results to show
SPOTIFY_DEVICE_NAME = None  # Leave None for default device

# File Paths
SCREENSHOTS_DIR = "screenshots"
LOGS_DIR = "logs"
DATA_DIR = "data"

# Recognition Settings
MICROPHONE_TIMEOUT = 1  # Seconds to wait for speech
MICROPHONE_PHRASE_TIMEOUT = 3  # Seconds of silence before stopping
RECOGNITION_LANGUAGE = "en-US"  # Language for speech recognition

# Wake Word Detection Settings
WAKE_WORD_TIMEOUT = 0.5  # Time to listen for wake word
WAKE_WORD_SENSITIVITY = 0.7  # Sensitivity threshold (0.0 to 1.0)

# Error Handling
MAX_RETRIES = 3  # Maximum retries for failed operations
RETRY_DELAY = 1  # Seconds to wait between retries

# Debug Settings
DEBUG_MODE = True  # Set to False in production
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# API Timeouts
OPENAI_TIMEOUT = 30  # Seconds
HTTP_REQUEST_TIMEOUT = 10  # Seconds

# Default Responses
DEFAULT_RESPONSES = {
    "greeting": [
        "Hello! How can I help you today?",
        "Hi there! What would you like me to do?",
        "Good to see you! How can I assist?"
    ],
    "goodbye": [
        "Goodbye! Have a great day!",
        "See you later!",
        "Take care!"
    ],
    "error": [
        "Sorry, I didn't understand that. Could you try again?",
        "I'm not sure what you mean. Can you rephrase that?",
        "Something went wrong. Please try again."
    ],
    "not_found": [
        "I couldn't find what you're looking for.",
        "That doesn't seem to exist.",
        "I'm unable to locate that."
    ]
}