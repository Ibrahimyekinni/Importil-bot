import asyncio
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Add the project root to sys.path so that 'bot' and 'config' packages are
# importable regardless of which directory the script is run from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.handlers.start import handle_start
from bot.handlers.help import handle_help
from bot.handlers.link import handle_link
from bot.handlers.refresh import handle_refresh
from bot.handlers.language import handle_language_command, handle_language_callback
from bot.handlers.track import ASK_IMPORTER_TYPE, ASK_QUANTITY, receive_importer_type, receive_quantity, start_track
from bot.services.db_service import create_tables
from config.settings import TELEGRAM_BOT_TOKEN


async def setup_bot():
    """
    Initialises the database tables and builds the bot Application with all
    command and message handlers registered. Returns the ready Application.
    """
    # Ensure both 'users' and 'queries' tables exist before handling any update.
    # If the DB is unreachable the bot still starts — DB features will silently
    # no-op until the connection is restored.
    try:
        create_tables()
    except Exception:
        print("⚠️ Warning: Could not connect to database. Bot will run without DB features.")

    # Build the Application — this is the central object for python-telegram-bot v20+
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # /start — registration and status check
    application.add_handler(CommandHandler("start", handle_start))

    # /help — show available commands
    application.add_handler(CommandHandler("help", handle_help))

    # /link — connect an email address to the user's account
    application.add_handler(CommandHandler("link", handle_link))

    # /language — show language picker
    application.add_handler(CommandHandler("language", handle_language_command))

    # /refresh — admin-only: clears and re-fetches the Drive document cache
    application.add_handler(CommandHandler("refresh", handle_refresh))

    # Inline keyboard callbacks for language selection (lang_en / lang_he)
    application.add_handler(CallbackQueryHandler(handle_language_callback, pattern="^lang_"))

    # Collect importer type + quantity before running compliance check
    application.add_handler(ConversationHandler(
        entry_points=[
            MessageHandler(filters.Document.ALL, start_track),
            MessageHandler(filters.PHOTO, start_track),
            MessageHandler(filters.TEXT & ~filters.COMMAND, start_track),
        ],
        states={
            ASK_IMPORTER_TYPE: [
                CallbackQueryHandler(receive_importer_type, pattern="^track_"),
            ],
            ASK_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity),
            ],
        },
        fallbacks=[CommandHandler("start", handle_start)],
    ))

    print(f"[webhook] Registered handlers: {application.handlers}")

    return application


class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless handler. Vercel calls this class for every incoming HTTP
    request, so it must be a BaseHTTPRequestHandler subclass named 'handler'.
    """

    def do_POST(self):
        """
        Receives the JSON payload that Telegram sends to the webhook URL,
        deserialises it into a python-telegram-bot Update object, processes it
        through the bot application, then responds with 200 OK.
        """
        # Read the raw request body using the Content-Length header
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Parse the JSON payload from Telegram
        update_data = json.loads(body.decode("utf-8"))

        # Initialise the bot and process the update synchronously within this request
        async def process():
            application = await setup_bot()
            await application.initialize()
            update = Update.de_json(update_data, application.bot)
            await application.process_update(update)
            await application.shutdown()

        asyncio.run(process())

        # Always return 200 so Telegram doesn't retry the webhook call
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

    def do_GET(self):
        """Health-check endpoint — useful for confirming the function is deployed."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "Importil webhook is running"}).encode("utf-8"))


# ── Local development ────────────────────────────────────────────────────────
# Run  `python api/webhook.py`  to start the bot in polling mode.
# Polling repeatedly asks Telegram for new updates instead of waiting for a
# webhook push — perfect for testing locally without a public URL.
if __name__ == "__main__":
    app = asyncio.run(setup_bot())
    app.run_polling()
