from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.db_service import get_user, save_user, get_user_language
from bot.utils.messages import get_message
from config.settings import ADMIN_TELEGRAM_ID


def _language_keyboard():
    """Returns the inline keyboard for language selection."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("עברית 🇮🇱",   callback_data="lang_he"),
        ]
    ])


async def handle_start(update, context):
    """
    Handles the /start command.
    Checks if the user is registered and approved, and responds accordingly.
    Registers new users automatically on first contact.
    Shows the language picker if the user hasn't set a preference yet.
    """
    telegram_id = update.effective_user.id
    username    = update.effective_user.username or update.effective_user.first_name

    user     = get_user(telegram_id)
    language = get_user_language(telegram_id)

    if user and user["approved"]:
        # Returning approved user — greet them in their chosen language
        await update.message.reply_text(
            get_message('welcome_back', language, username=username)
        )

    elif user and not user["approved"]:
        # Registered but awaiting admin approval
        await update.message.reply_text(get_message('pending', language))

    else:
        # First-time user — register them and notify admin
        save_user(telegram_id, username, email=None)
        await update.message.reply_text(
            get_message('welcome_new', language),
            reply_markup=_language_keyboard(),
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=get_message(
                    'new_user_admin', 'en',
                    username=username,
                    telegram_id=telegram_id,
                ),
            )
        except Exception as e:
            print(f"[start] Failed to notify admin of new user: {e}")
