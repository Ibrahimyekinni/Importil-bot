import asyncio
import base64
import json
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from bot.services.db_service import (
    get_user, set_user_state, save_query,
)
from bot.utils.messages import get_message, get_error_message

# (label shown in the exemption message, list of lowercase keywords to match)
_EXEMPT_CATEGORIES = [
    (
        "Mouse, keyboard, computer peripherals",
        ["mouse", "keyboard", "trackpad", "trackball", "webcam", "joystick",
         "computer peripheral"],
    ),
    (
        "Computer monitor, video projector",
        ["computer monitor", "video projector", "projector", "monitor"],
    ),
    (
        "Streamer, gaming console, PlayStation, Xbox, Nintendo",
        ["streamer", "gaming console", "playstation", "ps4", "ps5",
         "xbox", "nintendo", "nintendo switch"],
    ),
    (
        "E-reader, Kindle",
        ["e-reader", "ereader", "kindle", "e reader"],
    ),
    (
        "GPS receiver (non-transmitting)",
        ["gps receiver"],
    ),
    (
        "Bluetooth speaker, headphones, earbuds, AirPods",
        ["bluetooth speaker", "headphones", "earbuds", "airpods",
         "earphones", "headset"],
    ),
    (
        "Smartphone, mobile phone (EU/US compliant)",
        ["smartphone", "mobile phone", "iphone", "cell phone"],
    ),
]


def _extract_description(original_update_data):
    """Return a single lowercase string with all searchable text from the stored update dict."""
    msg = original_update_data.get("message", {})
    parts = []
    if msg.get("text"):
        parts.append(msg["text"])
    if msg.get("caption"):
        parts.append(msg["caption"])
    doc = msg.get("document", {})
    if doc.get("file_name"):
        parts.append(doc["file_name"])
    return " ".join(parts).lower()


def _check_exemption(description):
    """Return (True, category_label) on first keyword match, else (False, None)."""
    for label, keywords in _EXEMPT_CATEGORIES:
        for kw in keywords:
            if kw in description:
                return True, label
    return False, None


def _extract_query_meta(original_update_data):
    """Return (query_type, query_content) strings for DB logging, mirroring handle_check."""
    msg = original_update_data.get("message", {})
    if msg.get("document"):
        fname = msg["document"].get("file_name", "document")
        return "document", f"document:{fname}"
    if msg.get("photo"):
        file_id = msg["photo"][-1].get("file_id", "")
        return "photo", f"photo:{file_id}"
    return "text", msg.get("text", "")


async def handle_track(update, context):
    """
    Stateful track-classification handler safe for serverless deployments.
    Conversation state is persisted in Neon DB instead of in-process memory.

    State machine:
      NULL        → show importer-type keyboard, set conv_state='ASK_TYPE'
      ASK_TYPE    → user sent text while waiting for keyboard; re-show keyboard
      ASK_QUANTITY→ validate quantity, classify track, exemption check, compliance check
    """
    telegram_id = update.effective_user.id

    # Single DB round-trip for all user fields (approved, language, conv_state, conv_data).
    # Three separate calls (get_user_language + is_approved + get_user_state) meant three
    # independent Neon connections; if the third failed it returned (None, None) and the
    # handler silently restarted the flow, causing the repeated-keyboard and short-text bugs.
    user = get_user(telegram_id)
    if not (user and user.get('approved')):
        lang = (user.get('language') if user else None) or 'en'
        await update.message.reply_text(get_message('no_access', lang))
        return

    language   = user.get('language') or 'en'
    conv_state = user.get('conv_state')
    conv_data  = user.get('conv_data')

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

        try:
            set_user_state(telegram_id, None)
        except Exception as e:
            print(f"[track] failed to clear conv_state: {type(e).__name__}: {e}")
            traceback.print_exc()

        if allowed and original_update_data:
            description = _extract_description(original_update_data)
            is_exempt, category = _check_exemption(description)

            if is_exempt:
                query_type, query_content = _extract_query_meta(original_update_data)
                msg = get_message('exempt_product', language, category=category)
                save_query(
                    telegram_id=telegram_id,
                    query_type=query_type,
                    query_content=query_content,
                    verdict="exempt",
                    full_response=msg,
                )
                await update.message.reply_text(msg)
                return

            image_b64 = data.get('image_b64')

            if image_b64:
                # Photo query — use bytes downloaded at message-receipt time.
                # Re-downloading via Update.de_json + get_file produces empty bytes
                # in the serverless env, causing Groq to report "image not provided".
                from bot.services.ai_service import analyze_image_query, AIServiceError
                from bot.handlers.check import keep_typing, extract_verdict

                caption = (original_update_data.get('message') or {}).get('caption') or ''
                lang_instruction = (
                    "Respond in Hebrew (עברית)." if language == "he" else "Respond in English."
                )
                photo_list   = (original_update_data.get('message') or {}).get('photo') or []
                query_content = f"photo:{photo_list[-1].get('file_id', '')}" if photo_list else "photo"

                await update.message.reply_text(get_message('analyzing_image', language))

                stop_event  = asyncio.Event()
                typing_task = asyncio.create_task(
                    keep_typing(context.bot, update.effective_chat.id, stop_event)
                )
                try:
                    img_bytes = base64.b64decode(image_b64)
                    print(f"[track] calling analyze_image_query with {len(img_bytes)} bytes")
                    response = analyze_image_query(
                        img_bytes,
                        additional_text=caption,
                        lang_instruction=lang_instruction,
                    )
                    verdict = extract_verdict(response)
                    save_query(
                        telegram_id=telegram_id,
                        query_type='photo',
                        query_content=query_content,
                        verdict=verdict,
                        full_response=response,
                    )
                    await update.message.reply_text(response, parse_mode="Markdown")
                except AIServiceError as e:
                    await update.message.reply_text(get_error_message(str(e), language))
                except Exception:
                    traceback.print_exc()
                    await update.message.reply_text(get_message('image_error', language))
                finally:
                    stop_event.set()
                    typing_task.cancel()

            else:
                # Text or document query — replay through the standard handlers.
                from bot.handlers.check import handle_check
                from bot.handlers.document_check import handle_document_check

                original_update = Update.de_json(original_update_data, context.bot)
                if original_update.message and original_update.message.document:
                    await handle_document_check(original_update, context)
                else:
                    await handle_check(original_update, context)

    elif conv_state == 'ASK_TYPE':
        keyboard = [[
            InlineKeyboardButton("🧍 Private Person", callback_data="track_private"),
            InlineKeyboardButton("🏢 Company", callback_data="track_company"),
        ]]
        await update.message.reply_text(
            get_message('ask_importer_type', language),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    else:
        # conv_state is None (or unexpected) → start a fresh classification flow.
        data = {"update": update.to_dict()}

        # For photo messages, download the bytes NOW and store them as base64 in
        # conv_data. Relying on file_id to re-download later (via Update.de_json +
        # get_file) produces empty or invalid bytes in the serverless environment,
        # which causes Groq to receive an empty image_url and reply "image not provided".
        if update.message and update.message.photo:
            try:
                photo   = update.message.photo[-1]
                tg_file = await context.bot.get_file(photo.file_id)
                img_bytes = bytes(await tg_file.download_as_bytearray())
                data['image_b64'] = base64.b64encode(img_bytes).decode('utf-8')
                print(f"[track] pre-downloaded photo: {len(img_bytes)} bytes stored in conv_data")
            except Exception as e:
                print(f"[track] photo pre-download failed: {type(e).__name__}: {e}")
                traceback.print_exc()

        try:
            set_user_state(telegram_id, 'ASK_TYPE', json.dumps(data))
        except Exception as e:
            print(f"[track] failed to save ASK_TYPE state: {type(e).__name__}: {e}")
            traceback.print_exc()

        keyboard = [[
            InlineKeyboardButton("🧍 Private Person", callback_data="track_private"),
            InlineKeyboardButton("🏢 Company", callback_data="track_company"),
        ]]
        await update.message.reply_text(
            get_message('ask_importer_type', language),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_track_callback(update, context):
    """
    Handles the track_private / track_company inline keyboard selection.
    Reads conv_state from DB; if not ASK_TYPE, ignores silently.
    """
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id

    # Single DB round-trip (same reason as handle_track above).
    user = get_user(telegram_id)
    if not (user and user.get('approved')):
        return

    language   = user.get('language') or 'en'
    conv_state = user.get('conv_state')
    conv_data  = user.get('conv_data')

    if conv_state != 'ASK_TYPE':
        return

    importer_type = "private" if query.data == "track_private" else "company"

    data = json.loads(conv_data) if conv_data else {}
    data['importer_type'] = importer_type

    try:
        set_user_state(telegram_id, 'ASK_QUANTITY', json.dumps(data))
    except Exception as e:
        print(f"[track_callback] failed to save ASK_QUANTITY state: {type(e).__name__}: {e}")
        traceback.print_exc()
        await query.message.reply_text(get_message('error', language))
        return

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(get_message('ask_quantity', language))
