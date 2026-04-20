import asyncio
import traceback

from bot.services.db_service import is_approved, save_query, get_user_language
from bot.services.ai_service import analyze_text_query, analyze_image_query, AIServiceError
from bot.utils.messages import get_message, get_error_message
from bot.handlers.url_check import extract_url, fetch_product_content, is_low_confidence

# Per-user conversation history for CONDITIONAL follow-ups.
# Structure: { telegram_id: [{"role": "user"|"assistant", "content": str}, ...] }
# Cleared automatically when a final ALLOWED or REJECTED verdict is reached.
user_context = {}


def extract_verdict(response_text):
    """
    Infers a short verdict keyword from the AI response.
    Falls back to 'conditional' when neither ALLOWED nor REJECTED appears.
    """
    upper = response_text.upper()
    if "ALLOWED" in upper:
        return "allowed"
    if "REJECTED" in upper:
        return "rejected"
    return "conditional"


def is_final_verdict(verdict):
    """Returns True for verdicts that close the conversation (not conditional)."""
    return verdict in ("allowed", "rejected")


async def keep_typing(bot, chat_id, stop_event):
    """
    Sends a typing chat action every 4 seconds until stop_event is set.
    Runs as a background asyncio task so the Telegram 'typing...' indicator
    stays visible for the full duration of the AI call.
    """
    while not stop_event.is_set():
        try:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception:
            pass  # Never let a failed indicator kill the analysis
        await asyncio.sleep(4)


async def handle_check(update, context):
    """
    Handles incoming messages (text or photo) for compliance checking.
    Only approved users can submit queries.

    Conversation flow:
      - First text message → fresh analysis
      - If verdict is CONDITIONAL, history is saved so the next message from
        this user is treated as a follow-up and the full context is passed to AI
      - When verdict reaches ALLOWED or REJECTED, context is cleared
      - Photos always start a fresh analysis (no history threading for vision)
    """
    telegram_id = update.effective_user.id
    chat_id     = update.effective_chat.id
    language    = get_user_language(telegram_id)

    # Block unapproved users before doing anything else
    if not is_approved(telegram_id):
        await update.message.reply_text(get_message('no_access', language))
        return

    # Suffix injected into the AI system prompt to steer response language
    lang_instruction = (
        "Respond in Hebrew (עברית)." if language == "he" else "Respond in English."
    )

    if update.message.photo:
        # ── Photo query ──────────────────────────────────────────────────────
        # Photos always trigger a fresh analysis — no conversation threading

        await update.message.reply_text(get_message('analyzing_image', language))

        photo          = update.message.photo[-1]
        query_content  = f"photo:{photo.file_id}"
        additional_text = update.message.caption or ""

        stop_event  = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_event))

        try:
            file        = await context.bot.get_file(photo.file_id)
            image_bytes = bytes(await file.download_as_bytearray())

            response = analyze_image_query(
                image_bytes,
                additional_text=additional_text,
                lang_instruction=lang_instruction,
            )
            verdict = extract_verdict(response)

            save_query(
                telegram_id=telegram_id,
                query_type="photo",
                query_content=query_content,
                verdict=verdict,
                full_response=response,
            )

            await update.message.reply_text(response, parse_mode="Markdown")

        except AIServiceError:
            await update.message.reply_text(get_error_message('ai_unavailable', language))
        except Exception:
            traceback.print_exc()
            await update.message.reply_text(get_message('image_error', language))

        finally:
            stop_event.set()
            typing_task.cancel()

    elif update.message.text:
        # ── Text query ───────────────────────────────────────────────────────

        query_content = update.message.text.strip()

        if len(query_content) < 3:
            await update.message.reply_text(get_error_message('invalid_input', language))
            return

        url = extract_url(query_content)

        if url:
            # ── URL/link query ────────────────────────────────────────────────
            # Try meta-tag extraction first; fall back to Firecrawl if needed.
            # Logged as query_type='link'.

            await update.message.reply_text(get_message('fetching_link', language))

            stop_event  = asyncio.Event()
            typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_event))

            try:
                page_text = fetch_product_content(url)

                # ── Debug: always visible in Vercel logs ──────────────────────
                print(f"[DEBUG] fetch_product_content returned: {repr(page_text[:120] if page_text else page_text)}")

                if not page_text or len(page_text.strip()) < 30:
                    # Both fetch methods failed or returned too little content
                    # (short strings are generic site titles, not product data)
                    save_query(
                        telegram_id=telegram_id,
                        query_type="link",
                        query_content=url,
                        verdict="unclear",
                        full_response=f"Fetch returned insufficient content: {repr(page_text)}",
                    )
                    await update.message.reply_text(get_message('link_fetch_failed', language))
                    await update.message.reply_text(get_message('link_fetch_tip', language))
                    return

                # Build a product description the AI understands
                product_description = (
                    f"The following product information was fetched from this URL: {url}\n\n"
                    f"{page_text}"
                )

                response = analyze_text_query(
                    product_description,
                    conversation_history=None,
                    lang_instruction=lang_instruction,
                )

                if is_low_confidence(response):
                    # AI couldn't identify the product from the page content —
                    # ask the user to supply specifics rather than a shaky verdict
                    save_query(
                        telegram_id=telegram_id,
                        query_type="link",
                        query_content=url,
                        verdict="unclear",
                        full_response=response,
                    )
                    await update.message.reply_text(get_message('link_unclear', language))
                else:
                    verdict = extract_verdict(response)
                    save_query(
                        telegram_id=telegram_id,
                        query_type="link",
                        query_content=url,
                        verdict=verdict,
                        full_response=response,
                    )
                    await update.message.reply_text(response, parse_mode="Markdown")

            except AIServiceError:
                await update.message.reply_text(get_error_message('ai_unavailable', language))
            except Exception:
                traceback.print_exc()
                await update.message.reply_text(get_message('link_error', language))

            finally:
                stop_event.set()
                typing_task.cancel()

            return  # URL handling is always a fresh check — no conversation context

        # ── Plain-text query (with optional follow-up context) ────────────────

        # Check if we have a pending CONDITIONAL conversation for this user
        history = user_context.get(telegram_id)

        if history:
            await update.message.reply_text(get_message('analyzing_followup', language))
        else:
            await update.message.reply_text(get_message('analyzing_text', language))

        stop_event  = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_event))

        try:
            response = analyze_text_query(
                query_content,
                conversation_history=history,
                lang_instruction=lang_instruction,
            )
            verdict = extract_verdict(response)

            save_query(
                telegram_id=telegram_id,
                query_type="text",
                query_content=query_content,
                verdict=verdict,
                full_response=response,
            )

            await update.message.reply_text(response, parse_mode="Markdown")

            # ── Update conversation context ───────────────────────────────────
            if is_final_verdict(verdict):
                # Final verdict reached — clear context so the next message
                # starts a completely fresh analysis
                user_context.pop(telegram_id, None)
            else:
                # Verdict is CONDITIONAL — append this exchange to history so
                # the next message is treated as a follow-up
                if telegram_id not in user_context:
                    user_context[telegram_id] = []

                user_context[telegram_id].append(
                    {"role": "user",      "content": query_content}
                )
                user_context[telegram_id].append(
                    {"role": "assistant", "content": response}
                )

        except AIServiceError:
            await update.message.reply_text(get_error_message('ai_unavailable', language))
        except Exception:
            traceback.print_exc()
            await update.message.reply_text(get_message('error', language))

        finally:
            stop_event.set()
            typing_task.cancel()
