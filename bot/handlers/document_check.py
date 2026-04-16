import asyncio
import io
import traceback

from bot.services.db_service import is_approved, save_query, get_user_language
from bot.services.ai_service import analyze_text_query
from bot.utils.messages import get_message
from bot.handlers.check import keep_typing, extract_verdict

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _extract_text_from_pdf(file_bytes):
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_text_from_docx(file_bytes):
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)


async def handle_document_check(update, context):
    """
    Handles PDF and DOCX files sent directly in the chat.
    Extracts text and feeds it into the same compliance check as text queries.
    Logged as query_type='document'.
    """
    try:
        telegram_id = update.effective_user.id
        chat_id     = update.effective_chat.id
        language    = get_user_language(telegram_id)

        if not is_approved(telegram_id):
            await update.message.reply_text(get_message('no_access', language))
            return

        document  = update.message.document
        mime_type = document.mime_type or ""

        print(f"[document_check] triggered for file: {document.file_name}")
        print(f"[document_check] mime_type: {document.mime_type}")

        if mime_type not in SUPPORTED_MIME_TYPES:
            await update.message.reply_text(get_message('document_error', language))
            return

        await update.message.reply_text(get_message('analyzing_document', language))

        lang_instruction = (
            "Respond in Hebrew (עברית)." if language == "he" else "Respond in English."
        )

        stop_event  = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop_event))

        try:
            file       = await context.bot.get_file(document.file_id)
            file_bytes = bytes(await file.download_as_bytearray())

            if mime_type == "application/pdf":
                text = _extract_text_from_pdf(file_bytes)
            else:
                text = _extract_text_from_docx(file_bytes)

            text = text.strip()
            if not text or len(text) < 20:
                raise ValueError("Extracted text is too short to be useful")

            filename = document.file_name or "document"
            product_description = (
                f"The following product information was extracted from a document ({filename}):\n\n"
                f"{text[:8000]}"
            )

            response = analyze_text_query(
                product_description,
                conversation_history=None,
                lang_instruction=lang_instruction,
            )
            verdict = extract_verdict(response)

            save_query(
                telegram_id=telegram_id,
                query_type="document",
                query_content=f"document:{filename}",
                verdict=verdict,
                full_response=response,
            )

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception:
            traceback.print_exc()
            await update.message.reply_text(get_message('document_error', language))

        finally:
            stop_event.set()
            typing_task.cancel()

    except Exception as e:
        print(f"[document_check] ERROR: {e}")
