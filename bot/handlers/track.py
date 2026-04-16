import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from bot.services.db_service import is_approved, get_user_language, get_user_state, set_user_state
from bot.utils.messages import get_message


async def handle_track(update, context):
    """
    Stateful track-classification handler safe for serverless deployments.
    Conversation state is persisted in Neon DB instead of in-process memory.

    State machine:
      NULL        → show importer-type keyboard, set conv_state='ASK_TYPE'
      ASK_TYPE    → user sent text while waiting for keyboard; re-show keyboard
      ASK_QUANTITY→ validate quantity, classify track, run compliance check
    """
    telegram_id = update.effective_user.id
    language = get_user_language(telegram_id)

    if not is_approved(telegram_id):
        await update.message.reply_text(get_message('no_access', language))
        return

    conv_state, conv_data = get_user_state(telegram_id)

    if conv_state is None:
        data = {"update": update.to_dict()}
        set_user_state(telegram_id, 'ASK_TYPE', json.dumps(data))

        keyboard = [[
            InlineKeyboardButton("🧍 Private Person", callback_data="track_private"),
            InlineKeyboardButton("🏢 Company", callback_data="track_company"),
        ]]
        await update.message.reply_text(
            get_message('ask_importer_type', language),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if conv_state == 'ASK_TYPE':
        keyboard = [[
            InlineKeyboardButton("🧍 Private Person", callback_data="track_private"),
            InlineKeyboardButton("🏢 Company", callback_data="track_company"),
        ]]
        await update.message.reply_text(
            get_message('ask_importer_type', language),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if conv_state == 'ASK_QUANTITY':
        text = update.message.text.strip() if update.message.text else ""
        try:
            quantity = int(text)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text(get_message('invalid_quantity', language))
            return

        data = json.loads(conv_data) if conv_data else {}
        importer_type = data.get('importer_type', 'private')
        original_update_data = data.get('update')

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

        set_user_state(telegram_id, None)

        if allowed and original_update_data:
            from bot.handlers.check import handle_check
            from bot.handlers.document_check import handle_document_check

            original_update = Update.de_json(original_update_data, context.bot)
            if original_update.message and original_update.message.document:
                await handle_document_check(original_update, context)
            else:
                await handle_check(original_update, context)


async def handle_track_callback(update, context):
    """
    Handles the track_private / track_company inline keyboard selection.
    Reads conv_state from DB; if not ASK_TYPE, ignores silently.
    """
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    language = get_user_language(telegram_id)

    conv_state, conv_data = get_user_state(telegram_id)

    if conv_state != 'ASK_TYPE':
        return

    importer_type = "private" if query.data == "track_private" else "company"

    data = json.loads(conv_data) if conv_data else {}
    data['importer_type'] = importer_type

    set_user_state(telegram_id, 'ASK_QUANTITY', json.dumps(data))

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(get_message('ask_quantity', language))
