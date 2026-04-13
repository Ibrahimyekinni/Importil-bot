from bot.services.db_service import get_user, save_user
from config.settings import ADMIN_TELEGRAM_ID


async def handle_start(update, context):
    """
    Handles the /start command.
    Checks if the user is registered and approved, and responds accordingly.
    Registers new users automatically on first contact.
    """
    # Extract Telegram identity from the incoming update
    telegram_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    # Look up the user in the database
    user = get_user(telegram_id)

    if user and user["approved"]:
        # User is registered and has been approved by the admin
        await update.message.reply_text(
            f"Welcome back {username}! 👋 You're verified. "
            "Send me a product name or photo to check customs compliance."
        )

    elif user and not user["approved"]:
        # User registered but still waiting for admin approval
        await update.message.reply_text(
            "Your account is pending approval. "
            "We'll notify you once you're verified. ⏳"
        )

    else:
        # First time user — register them with no email yet
        save_user(telegram_id, username, email=None)
        await update.message.reply_text(
            "Welcome to Importil! 🛃 Your registration has been received. "
            "Dekel will approve your access shortly. "
            "Use /link your@email.com to connect your email."
        )
        # Notify the admin about the new registration
        try:
            await context.bot.send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=(
                    f"🆕 New importer registered!\n\n"
                    f"Name: @{username}\n"
                    f"Telegram ID: {telegram_id}\n\n"
                    "Go to the dashboard to approve or reject them."
                )
            )
        except Exception as e:
            print(f"[start] Failed to notify admin of new user: {e}")
