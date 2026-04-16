from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.services.db_service import is_approved, get_user_language
from bot.utils.messages import get_message

ASK_IMPORTER_TYPE = 0
ASK_QUANTITY = 1

# Stores original Update objects between conversation steps (in-memory, per worker process).
_original_updates: dict = {}


async def start_track(update, context):
    telegram_id = update.effective_user.id
    language = get_user_language(telegram_id)

    if not is_approved(telegram_id):
        await update.message.reply_text(get_message('no_access', language))
        return ConversationHandler.END

    _original_updates[telegram_id] = update

    keyboard = [[
        InlineKeyboardButton("🧍 Private Person", callback_data="track_private"),
        InlineKeyboardButton("🏢 Company", callback_data="track_company"),
    ]]
    await update.message.reply_text(
        get_message('ask_importer_type', language),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ASK_IMPORTER_TYPE


async def receive_importer_type(update, context):
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    language = get_user_language(telegram_id)

    context.user_data['importer_type'] = (
        "private" if query.data == "track_private" else "company"
    )
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(get_message('ask_quantity', language))
    return ASK_QUANTITY


async def receive_quantity(update, context):
    from bot.handlers.check import handle_check
    from bot.handlers.document_check import handle_document_check

    telegram_id = update.effective_user.id
    language = get_user_language(telegram_id)

    text = update.message.text.strip()
    try:
        quantity = int(text)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(get_message('invalid_quantity', language))
        return ASK_QUANTITY

    importer_type = context.user_data.get('importer_type', 'private')
    original_update = _original_updates.pop(telegram_id, None)

    allowed = False
    if importer_type == "private":
        if quantity <= 5:
            context.user_data['track'] = 'personal'
            allowed = True
        else:
            await update.message.reply_text(get_message('private_limit_exceeded', language))
    else:
        if quantity <= 50:
            context.user_data['track'] = 'commercial_one_time'
            allowed = True
        else:
            await update.message.reply_text(get_message('commercial_license_required', language))

    if allowed and original_update:
        if original_update.message.document:
            await handle_document_check(original_update, context)
        else:
            await handle_check(original_update, context)

    return ConversationHandler.END
