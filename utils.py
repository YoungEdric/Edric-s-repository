# utils.py - Utility functions for Sarah AI Assistant

import logging
import os
import random
import time
import speech_recognition as sr
import pyttsx3
from datetime import datetime
from config import *

# -----------------------
# TEXT-TO-SPEECH & SPEECH
# -----------------------

# Initialize TTS engine
_engine = pyttsx3.init()
_engine.setProperty("rate", 180)   # Speaking speed
_engine.setProperty("volume", 1.0) # Volume (0.0 - 1.0)

def speak(text: str):
    """Make Sarah speak out loud and log the action"""
    log_message(f"Speaking: {text}", "INFO")
    _engine.say(text)
    _engine.runAndWait()

def listen(timeout=5, phrase_time_limit=10):
    """Listen from microphone and return recognized text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        log_message("Listening for speech...", "DEBUG")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio)
            log_message(f"Recognized speech: {text}", "INFO")
            return text
        except sr.WaitTimeoutError:
            log_message("Listening timed out", "WARNING")
            return None
        except sr.UnknownValueError:
            log_message("Could not understand audio", "WARNING")
            return None
        except sr.RequestError as e:
            log_message(f"Speech recognition error: {e}", "ERROR")
            return None

def confirm_action(prompt="Are you sure? Say yes or no."):
    """Ask user for confirmation via voice"""
    speak(prompt)
    response = listen()
    if response:
        return "yes" in response.lower()
    return False

# -----------------------
# GENERAL UTILITIES
# -----------------------

def get_random_response(response_type):
    """Get a random response from the default responses"""
    responses = DEFAULT_RESPONSES.get(response_type, ["Hello!"])
    return random.choice(responses)

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [SCREENSHOTS_DIR, LOGS_DIR, DATA_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            log_message(f"Created directory: {directory}")

def setup_logging():
    """Setup logging configuration"""
    setup_directories()
    
    log_filename = os.path.join(LOGS_DIR, f"sarah_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler() if DEBUG_MODE else logging.NullHandler()
        ]
    )

def log_message(message, level="INFO"):
    """Log a message with the specified level"""
    logger = logging.getLogger(__name__)
    
    if level.upper() == "DEBUG":
        logger.debug(message)
    elif level.upper() == "INFO":
        logger.info(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "CRITICAL":
        logger.critical(message)

def retry_operation(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Retry an operation with exponential backoff"""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                log_message(f"Operation failed after {max_retries} retries: {e}", "ERROR")
                return None
            
            wait_time = delay * (2 ** attempt)
            log_message(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

def get_current_time():
    """Get current time in a readable format"""
    now = datetime.now()
    return now.strftime("%I:%M %p on %B %d, %Y")

def get_greeting():
    """Get appropriate greeting based on time of day"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    elif 17 <= hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Good night"
    
    return f"{greeting}, {USER_NAME}!"

def parse_time_from_text(text):
    """Parse time from text like 'in 5 minutes', 'at 3 PM', etc."""
    text = text.lower()
    
    if "in" in text and ("minute" in text or "hour" in text):
        parts = text.split()
        try:
            if "minute" in text:
                idx = next(i for i, word in enumerate(parts) if word.isdigit())
                minutes = int(parts[idx])
                return minutes * 60
            elif "hour" in text:
                idx = next(i for i, word in enumerate(parts) if word.isdigit())
                hours = int(parts[idx])
                return hours * 3600
        except (ValueError, StopIteration):
            pass
    
    return None

def clean_filename(filename):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def is_valid_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    """Basic phone number validation"""
    import re
    digits = re.sub(r'\D', '', phone)
    return 10 <= len(digits) <= 15

def normalize_text(text):
    """Normalize text for better command matching"""
    return text.lower().strip()

def extract_contact_from_text(text):
    """Extract contact information from text"""
    words = text.split()
    for word in words:
        if '@' in word and is_valid_email(word):
            return word, 'email'
    for word in words:
        if is_valid_phone(word):
            return word, 'phone'
    return None, None

def get_system_info():
    """Get basic system information"""
    import platform
    import psutil
    
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'python_version': platform.python_version()
    }

def safe_eval(expression, allowed_names=None):
    """Safely evaluate mathematical expressions"""
    if allowed_names is None:
        allowed_names = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "len": len, "pow": pow, "sqrt": lambda x: x**0.5
        }
    
    try:
        import re
        if re.match(r'^[0-9+\-*/.() ]+$', expression):
            return eval(expression, {"__builtins__": {}}, {})
    except:
        pass
    
    return None

# -----------------------
# INIT
# -----------------------

setup_logging()
setup_directories()
log_message("Utils module initialized successfully")
