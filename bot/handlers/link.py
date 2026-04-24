import re

from bot.services.db_service import get_user, save_user
from bot.utils.messages import get_message


async def handle_link(update, context):
    """
    Handles the /link command.
    Expects the user to provide their email as an argument: /link your@email.com
    Saves or updates the email on their user record.
    """
    telegram_id = update.effective_user.id
    username    = update.effective_user.username or update.effective_user.first_name
    user     = get_user(telegram_id)
    language = user.get('language', 'en') if user else 'en'

    if not context.args:
        await update.message.reply_text(get_message('link_usage', language))
        return

    email = context.args[0]
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        await update.message.reply_text(
            "Invalid email address. Please provide a valid email."
        )
        return
    save_user(telegram_id, username, email)

    await update.message.reply_text(get_message('link_success', language))
