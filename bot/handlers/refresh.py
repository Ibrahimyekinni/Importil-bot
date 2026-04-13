from bot.services.drive_service import refresh_cache
from config.settings import ADMIN_TELEGRAM_ID


async def handle_refresh(update, context):
    """
    Handles the /refresh command.
    Clears and re-fetches the Drive document cache.
    Only the admin (ADMIN_TELEGRAM_ID) is allowed to run this.
    """
    telegram_id = update.effective_user.id

    if telegram_id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⛔ You don't have permission to do this.")
        return

    try:
        refresh_cache()
        await update.message.reply_text(
            "🔄 Document cache refreshed successfully! AI brain updated."
        )
    except Exception as e:
        print(f"[refresh] Error refreshing cache: {e}")
        await update.message.reply_text(
            "❌ Failed to refresh the cache. Check logs for details."
        )
