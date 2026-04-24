from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.db_service import get_user, update_user_language
from bot.utils.messages import get_message


async def handle_language_command(update, context):
    """
    Handles the /language command.
    Sends an inline keyboard so the user can pick English or Hebrew.
    """
    telegram_id = update.effective_user.id
    user     = get_user(telegram_id)
    language = user.get('language', 'en') if user else 'en'

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("עברית 🇮🇱",   callback_data="lang_he"),
        ]
    ])

    await update.message.reply_text(
        get_message('language_prompt', language),
        reply_markup=keyboard,
    )


async def handle_language_callback(update, context):
    """
    Handles the inline keyboard callback for language selection.
    Updates the user's language preference in the database.
    """
    query = update.callback_query
    telegram_id = query.from_user.id

    chosen = query.data  # 'lang_en' or 'lang_he'
    language = "he" if chosen == "lang_he" else "en"

    update_user_language(telegram_id, language)

    await query.answer()
    await query.message.reply_text(get_message('language_set', language))
