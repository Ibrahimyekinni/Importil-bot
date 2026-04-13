import os
from dotenv import load_dotenv

load_dotenv()

# Telegram bot token from BotFather — used to authenticate the bot with the Telegram API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Neon PostgreSQL connection string — used by db_service to connect to the database
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

# Groq API key — used by ai_service to run LLaMA text and vision models via Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Google Drive folder ID — used by drive_service to upload and store document files
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Flask secret key — used to sign session cookies for the admin dashboard
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# Admin dashboard password — used to protect the /login route on the Flask dashboard
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Telegram ID of the bot admin (Dekel) — used to restrict /refresh and send new-user alerts
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
