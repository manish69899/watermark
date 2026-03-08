# config.py - Configuration Settings for Watermark Bot (Pyrogram Version)
# Update BOT_TOKEN, API_ID, and API_HASH with your actual details in .env file

import os
from dotenv import load_dotenv

# Local environment variables load karne ke liye
load_dotenv()

# ============================================
# TELEGRAM BOT CREDENTIALS (PYROGRAM)
# ============================================
# Get your token from @BotFather on Telegram
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Get API_ID and API_HASH from my.telegram.org
# API_ID integer hona chahiye, isliye typecast kiya hai
API_ID = int(os.environ.get("API_ID", 0)) 
API_HASH = os.environ.get("API_HASH", "")

# ============================================
# DIRECTORY SETTINGS
# ============================================
# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Download directory for incoming files
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

# Output directory for processed files
OUTPUT_DIR = os.path.join(BASE_DIR, "processed")

# ============================================
# BOT SETTINGS
# ============================================
# Maximum file size in bytes (default: 20MB)
MAX_FILE_SIZE = 100000 * 1024 * 1024

# Session timeout in seconds (default: 1 hour)
SESSION_TIMEOUT = 100000000

# Maximum watermark text length
MAX_WATERMARK_LENGTH = 100000

# ============================================
# WATERMARK DEFAULTS
# ============================================
DEFAULT_OPACITY = 0.3
DEFAULT_COLOR = 'grey'
DEFAULT_STYLE = 'diagonal'
DEFAULT_FONT_SIZE = 48
DEFAULT_ROTATION = 45

# ============================================
# SERVER SETTINGS (for keep_alive)
# ============================================
# Port for web server (for platforms like Replit)
SERVER_PORT = int(os.environ.get("PORT", 8080))

# ============================================
# LOGGING SETTINGS
# ============================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = "bot.log"

# ============================================
# CREATE DIRECTORIES
# ============================================
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================
# VALIDATION
# ============================================
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("BOT_TOKEN not set! Please update .env with your actual token.")
        
    if not API_ID or API_ID == 0:
        errors.append("API_ID not set! Please get it from my.telegram.org and add to .env")
        
    if not API_HASH or API_HASH == "":
        errors.append("API_HASH not set! Please get it from my.telegram.org and add to .env")
    
    if errors:
        for error in errors:
            print(f"⚠️ CONFIG ERROR: {error}")
        return False
    
    return True

# Run validation on import
if __name__ != "__main__":
    if not validate_config():
        print("⚠️ Bot may not work correctly due to configuration errors.")