import os
from dotenv import load_dotenv

# Local environment variables load karne ke liye
load_dotenv()

# Apna Token ab Environment Variable se aayega
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Agar token nahi mila toh error dikhayega taaki aapko pata chal jaye
if not BOT_TOKEN:
    raise ValueError("⚠️ BOT_TOKEN is missing! Kripya .env file ya Render ke Environment Variables mein token daalein.")

# Folders
DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "processed"

# Ensure folders exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)