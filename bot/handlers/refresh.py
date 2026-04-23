from bot.services.drive_service import refresh_cache
from bot.services.db_service import get_user_language, set_user_state
from bot.utils.messages import get_message
from config.settings import ADMIN_TELEGRAM_ID


async def handle_refresh(update, context):
    """
    Handles the /refresh command.
    Clears and re-fetches the Drive document cache, and clears the caller's
    conversation memory. Only the admin (ADMIN_TELEGRAM_ID) is allowed to run this.
    """
    telegram_id = update.effective_user.id
    language    = get_user_language(telegram_id)

    if telegram_id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text(get_message('no_permission', language))
        return

    try:
        refresh_cache()
        set_user_state(telegram_id, None)
        await update.message.reply_text(get_message('refresh_success', language))
    except Exception as e:
        print(f"[refresh] Error refreshing cache: {e}")
        await update.message.reply_text(get_message('refresh_error', language))
