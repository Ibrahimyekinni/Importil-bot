import asyncio
import traceback

from bot.services.db_service import is_approved, save_query
from bot.services.ai_service import analyze_text_query, analyze_image_query


def extract_verdict(response_text):
    """
    Infers a short verdict keyword from the AI response.
    Looks for verdict markers that the model is prompted to include.
    Falls back to 'conditional' when neither clear marker is present.
    """
    upper = response_text.upper()
    if "ALLOWED" in upper:
        return "allowed"
    if "REJECTED" in upper:
        return "rejected"
    return "conditional"


async def keep_typing(bot, chat_id, stop_event):
    """
    Sends a typing chat action every 4 seconds until stop_event is set.
    Runs as a background asyncio task while the AI is processing so the
    Telegram 'typing...' indicator stays visible for the full duration.
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

    Flow:
      1. Gate on approval status
      2. Send a "thinking" message immediately
      3. Start a background typing loop so the indicator stays alive
      4. Run the AI analysis (text or vision)
      5. Stop the typing loop, send the verdict with Markdown formatting
      6. Persist the query and verdict to the database
    """
    telegram_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Block unapproved users before doing anything else
    if not is_approved(telegram_id):
        await update.message.reply_text(
            "⛔ You don't have access yet. Please wait for approval."
        )
        return

    if update.message.photo:
        # ── Photo query ──────────────────────────────────────────────────────

        await update.message.reply_text("📸 Analyzing image... please wait")

        # Grab the highest-resolution version (Telegram sends multiple sizes; last = largest)
        photo = update.message.photo[-1]
        query_content = f"photo:{photo.file_id}"

        # Optional caption the user may have typed alongside the photo
        additional_text = update.message.caption or ""

        # Start the background typing loop before the slow AI call
        stop_event = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_event))

        try:
            # Download the photo as raw bytes for the vision model
            file = await context.bot.get_file(photo.file_id)
            image_bytes = bytes(await file.download_as_bytearray())

            # Run vision analysis — blocks until Groq responds
            response = analyze_image_query(image_bytes, additional_text=additional_text)

            verdict = extract_verdict(response)

            save_query(
                telegram_id=telegram_id,
                query_type="photo",
                query_content=query_content,
                verdict=verdict,
                full_response=response
            )

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception:
            traceback.print_exc()
            await update.message.reply_text(
                "⚠️ Something went wrong while analyzing. Please try again in a moment."
            )

        finally:
            # Always stop the typing loop, whether the AI succeeded or failed
            stop_event.set()
            typing_task.cancel()

    elif update.message.text:
        # ── Text query ───────────────────────────────────────────────────────

        query_content = update.message.text

        await update.message.reply_text("🔍 Analyzing product compliance... please wait")

        # Start the background typing loop before the slow AI call
        stop_event = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_event))

        try:
            # Run text analysis — blocks until Groq responds
            response = analyze_text_query(query_content)

            verdict = extract_verdict(response)

            save_query(
                telegram_id=telegram_id,
                query_type="text",
                query_content=query_content,
                verdict=verdict,
                full_response=response
            )

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception:
            traceback.print_exc()
            await update.message.reply_text(
                "⚠️ Something went wrong while analyzing. Please try again in a moment."
            )

        finally:
            # Always stop the typing loop, whether the AI succeeded or failed
            stop_event.set()
            typing_task.cancel()
