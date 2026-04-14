from bot.services.db_service import get_user_language
from bot.utils.messages import get_message


async def notify_user_approved(bot, telegram_id: int):
    """
    Sends an approval notification to a user after Dekel approves them
    from the dashboard. Called directly from the Flask dashboard route.
    Uses the user's preferred language if set.
    """
    language = get_user_language(telegram_id)
    await bot.send_message(
        chat_id=telegram_id,
        text=get_message('approved_notification', language),
    )
