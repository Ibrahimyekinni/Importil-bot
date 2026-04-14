from bot.services.db_service import get_user_language
from bot.utils.messages import get_message


async def handle_help(update, context):
    """
    Handles the /help command.
    Sends the user a summary of all available bot commands and usage instructions.
    """
    telegram_id = update.effective_user.id
    language    = get_user_language(telegram_id)

    await update.message.reply_text(get_message('help', language))
