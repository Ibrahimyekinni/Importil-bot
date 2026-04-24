from bot.services.db_service import get_user
from bot.utils.messages import get_message


async def handle_help(update, context):
    """
    Handles the /help command.
    Sends the user a summary of all available bot commands and usage instructions.
    """
    telegram_id = update.effective_user.id
    user     = get_user(telegram_id)
    language = user.get('language', 'en') if user else 'en'

    await update.message.reply_text(get_message('help', language))
