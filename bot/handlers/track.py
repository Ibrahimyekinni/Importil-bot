import asyncio
import base64
import json
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from bot.services.db_service import (
    get_user, set_user_state, save_query,
)
from bot.utils.messages import get_message, get_error_message
from bot.utils.helpers import split_message


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

    if conv_state == 'AWAITING_FOLLOWUP':
        print(f"[track] AWAITING_FOLLOWUP: conv_data raw = {user.get('conv_data')}")
        from bot.services.ai_service import (
            analyze_text_query, analyze_image_query, analyze_followup_query, AIServiceError,
        )
        from bot.handlers.check import keep_typing, extract_verdict

        try:
            try:
                data = json.loads(conv_data) if conv_data else {}
            except (json.JSONDecodeError, TypeError):
                print("[track] AWAITING_FOLLOWUP: conv_data parse error, using empty dict")
                data = {}
            history = data.get('history', [])
            lang_instruction = (
                "Respond in Hebrew (עברית)." if language == "he" else "Respond in English."
            )

            if update.message and update.message.photo:
                try:
                    photo     = update.message.photo[-1]
                    tg_file   = await context.bot.get_file(photo.file_id)
                    img_bytes = bytes(await tg_file.download_as_bytearray())
                except Exception as e:
                    print(f"[track] AWAITING_FOLLOWUP photo download failed: {e}")
                    await update.message.reply_text(get_message('image_error', language))
                    return

                caption = update.message.caption or ""
                proc_msg = await update.message.reply_text(get_message('analyzing_image', language))

                stop_event  = asyncio.Event()
                typing_task = asyncio.create_task(
                    keep_typing(context.bot, update.effective_chat.id, stop_event)
                )
                try:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                    response = analyze_image_query(
                        img_bytes,
                        additional_text=caption,
                        lang_instruction=lang_instruction,
                        conversation_history=history,
                    )
                    verdict = extract_verdict(response)
                    save_query(
                        telegram_id=telegram_id,
                        query_type='photo',
                        query_content=f"photo:{photo.file_id}",
                        verdict=verdict,
                        full_response=response,
                    )
                    history.append({"role": "user",      "content": f"[Image]{(' ' + caption) if caption else ''}"})
                    history.append({"role": "assistant",  "content": response})
                    data['history'] = history[-10:]
                    set_user_state(telegram_id, 'AWAITING_FOLLOWUP', json.dumps(data))
                    chunks = split_message(response)
                    for i, chunk in enumerate(chunks):
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="Markdown")
                        if i < len(chunks) - 1:
                            await asyncio.sleep(0.3)
                    try:
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=proc_msg.message_id)
                    except Exception:
                        pass
                except AIServiceError as e:
                    await update.message.reply_text(get_error_message(str(e), language))
                except Exception:
                    traceback.print_exc()
                    await update.message.reply_text(get_message('image_error', language))
                finally:
                    stop_event.set()
                    typing_task.cancel()

            elif update.message and update.message.document:
                from bot.handlers.document_check import (
                    _extract_text_from_pdf, _extract_text_from_docx, SUPPORTED_MIME_TYPES,
                )
                document  = update.message.document
                mime_type = document.mime_type or ""

                if mime_type not in SUPPORTED_MIME_TYPES:
                    await update.message.reply_text(get_error_message('unsupported_file', language))
                    return

                await update.message.reply_text(get_message('analyzing_document', language))

                stop_event  = asyncio.Event()
                typing_task = asyncio.create_task(
                    keep_typing(context.bot, update.effective_chat.id, stop_event)
                )
                try:
                    file       = await context.bot.get_file(document.file_id)
                    file_bytes = bytes(await file.download_as_bytearray())

                    if mime_type == "application/pdf":
                        text = _extract_text_from_pdf(file_bytes)
                    else:
                        text = _extract_text_from_docx(file_bytes)

                    text = text.strip()
                    if not text or len(text) < 20:
                        await update.message.reply_text(get_message('document_error', language))
                        return

                    filename = document.file_name or "document"
                    product_description = (
                        f"The following product information was extracted from a document ({filename}):\n\n"
                        f"{text[:8000]}"
                    )
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                    response = analyze_text_query(
                        product_description,
                        conversation_history=history,
                        lang_instruction=lang_instruction,
                    )
                    verdict = extract_verdict(response)
                    save_query(
                        telegram_id=telegram_id,
                        query_type='document',
                        query_content=f"document:{filename}",
                        verdict=verdict,
                        full_response=response,
                    )
                    history.append({"role": "user",      "content": product_description[:500]})
                    history.append({"role": "assistant",  "content": response})
                    data['history'] = history[-10:]
                    set_user_state(telegram_id, 'AWAITING_FOLLOWUP', json.dumps(data))
                    chunks = split_message(response)
                    for i, chunk in enumerate(chunks):
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="Markdown")
                        if i < len(chunks) - 1:
                            await asyncio.sleep(0.3)
                except AIServiceError as e:
                    await update.message.reply_text(get_error_message(str(e), language))
                except Exception:
                    traceback.print_exc()
                    await update.message.reply_text(get_message('document_error', language))
                finally:
                    stop_event.set()
                    typing_task.cancel()

            else:
                text = (update.message.text or "").strip() if update.message else ""
                if len(text) < 3:
                    await update.message.reply_text(get_error_message('invalid_input', language))
                    return

                proc_msg = await update.message.reply_text(get_message('analyzing_followup', language))

                stop_event  = asyncio.Event()
                typing_task = asyncio.create_task(
                    keep_typing(context.bot, update.effective_chat.id, stop_event)
                )
                try:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                    response = analyze_followup_query(
                        text,
                        conversation_history=history,
                        lang_instruction=lang_instruction,
                    )
                    save_query(
                        telegram_id=telegram_id,
                        query_type='text',
                        query_content=text,
                        verdict='followup',
                        full_response=response,
                    )
                    history.append({"role": "user",      "content": text})
                    history.append({"role": "assistant",  "content": response})
                    data['history'] = history[-10:]
                    set_user_state(telegram_id, 'AWAITING_FOLLOWUP', json.dumps(data))
                    chunks = split_message(response)
                    for i, chunk in enumerate(chunks):
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk, parse_mode="Markdown")
                        if i < len(chunks) - 1:
                            await asyncio.sleep(0.3)
                    try:
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=proc_msg.message_id)
                    except Exception:
                        pass
                except AIServiceError as e:
                    await update.message.reply_text(get_error_message(str(e), language))
                except Exception:
                    traceback.print_exc()
                    await update.message.reply_text(get_message('error', language))
                finally:
                    stop_event.set()
                    typing_task.cancel()

        except Exception as e:
            print(f"[track] AWAITING_FOLLOWUP error: {e}")
            traceback.print_exc()
            await update.message.reply_text(get_message('error', language))

    elif conv_state == 'ASK_QUANTITY':
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
                try:
                    set_user_state(telegram_id, 'AWAITING_FOLLOWUP', json.dumps({
                        'history': [
                            {"role": "user",      "content": description[:500]},
                            {"role": "assistant",  "content": msg},
                        ]
                    }))
                except Exception as e:
                    print(f"[track] failed to save AWAITING_FOLLOWUP after exempt: {e}")
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
                    try:
                        set_user_state(telegram_id, 'AWAITING_FOLLOWUP', json.dumps({
                            'history': [
                                {"role": "user",      "content": f"[Image]{(' ' + caption) if caption else ''}"},
                                {"role": "assistant",  "content": response},
                            ]
                        }))
                    except Exception as e:
                        print(f"[track] failed to save AWAITING_FOLLOWUP after photo: {e}")
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
