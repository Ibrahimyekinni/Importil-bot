from bot.services.db_service import get_user, get_query_count
from bot.utils.messages import get_message


async def handle_status(update, context):
    telegram_id = update.effective_user.id
    user        = get_user(telegram_id)
    language    = user.get('language', 'en') if user else 'en'

    if language == 'he':
        access_status  = "✅ מאושר" if (user and user['approved']) else "⏳ ממתין לאישור"
        language_label = "🇮🇱 עברית"
    else:
        access_status  = "✅ Approved" if (user and user['approved']) else "⏳ Pending approval"
        language_label = "🇬🇧 English"

    query_count = get_query_count(telegram_id) if user else 0

    await update.message.reply_text(
        get_message('status', language,
                    access_status=access_status,
                    language_label=language_label,
                    query_count=query_count),
        parse_mode="Markdown",
    )
