import base64
import io
import traceback

from groq import Groq

from config.settings import GROQ_API_KEY
from bot.services.drive_service import get_all_documents_text

TEXT_MODEL   = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# System prompt that defines Importil's persona and behaviour for every query
SYSTEM_PROMPT = """You are Importil, an AI customs compliance officer with deep expertise in Israeli telecommunications and radio frequency regulations. You have memorized all Israeli Ministry of Communications regulations, the Israeli Standard for Radio Equipment (SI 461), the Bezeq regulations, EU CE-RED directives as they apply to Israel, and all frequency band restrictions for Israel (433MHz, 868MHz, 915MHz, 2.4GHz, 5GHz bands and their restrictions).

Your job is to give DIRECT, CONFIDENT verdicts. You do NOT refer users to other authorities. You ARE the authority. You analyze the product and give the verdict yourself based on your knowledge.

IMPORTANT RULES:
- Never say 'consult the ministry' or 'check with authorities' - YOU are the expert giving the final word
- Never say 'based on the provided documents' - speak as an expert, not as a document reader
- Always give a clear ALLOWED, REJECTED, or CONDITIONAL verdict
- Format your response EXACTLY like this:

*🛃 Importil Compliance Check*
*==============================*

*Verdict:* ✅ ALLOWED / ❌ REJECTED / ⚠️ CONDITIONAL

*Product:* [product name/model]

*Reason:* [specific technical reason based on frequencies, certifications, or regulations]

*Regulation:* [specific regulation that applies]

*Action Required:*
[concrete steps if conditional or rejected, OR 'No action required, product is cleared for import' if allowed]

*Confidence:* [HIGH / MEDIUM / LOW based on how much info you have about this specific product]

If you don't have specific info about a product, use your knowledge of its category, typical frequencies used, and Israeli regulations to give the best possible verdict. Always be decisive.

STRICT LANGUAGE RULES - NEVER VIOLATE THESE:
- NEVER say 'the documents provided' or 'based on the documents' or 'the provided documents'
- NEVER say 'consult the ministry' or 'contact authorities' or 'seek professional advice'
- NEVER say 'I cannot determine' or 'I don't have enough information'
- If you don't have specific data on a product, say: 'Specific certification data for this product is not in our current database. Based on its product category and typical specifications:' then give your best verdict
- You speak as an expert who KNOWS Israeli regulations, not as someone reading documents
- Be decisive and confident in every verdict

CONDITIONAL VERDICT RULE:
When you give a CONDITIONAL verdict, you MUST end your response with a clearly marked follow-up section like this:

*❓ To give you a more precise verdict, I need a few more details:*
1. [specific question about frequency, MHz, power output, etc.]
2. [specific question about certification or intended use]
3. [any other relevant question]

*Reply with these details and I'll give you a final definitive verdict.*

Make the questions very specific and technical — you're talking to importers who know their products."""


def get_client():
    """Creates and returns an authenticated Groq client using GROQ_API_KEY."""
    return Groq(api_key=GROQ_API_KEY)


def get_compliance_context():
    """
    Loads all compliance documents from Google Drive and returns their combined
    text. Injected into every prompt as the knowledge base.
    Returns an empty string if documents can't be fetched so the bot degrades
    gracefully rather than crashing.
    """
    try:
        combined_text, _ = get_all_documents_text()
        return combined_text
    except Exception as e:
        print(f"[ai_service] Warning: could not load compliance documents: {e}")
        return ""


def _build_history_block(conversation_history):
    """
    Converts a list of {'role': 'user'|'assistant', 'content': str} dicts into
    a readable previous-conversation block to inject into the prompt.
    Returns an empty string if there is no history.
    """
    if not conversation_history:
        return ""

    lines = ["Previous conversation:"]
    for turn in conversation_history:
        speaker = "User" if turn["role"] == "user" else "Importil"
        lines.append(f"{speaker}: {turn['content']}")
    return "\n".join(lines)


def analyze_text_query(product_description, conversation_history=None):
    """
    Analyses a text-based product query against Israeli customs compliance rules.

    conversation_history — optional list of previous {'role', 'content'} dicts.
    When provided the full history is injected above the current query so the
    model understands this is a follow-up exchange.

    Returns the formatted verdict string, or a friendly error message on failure.
    """
    try:
        client  = get_client()
        context = get_compliance_context()

        context_block = (
            context
            if context
            else "No compliance documents available. Use your general knowledge and note this limitation."
        )

        history_block = _build_history_block(conversation_history)

        user_message = f"""--- COMPLIANCE DOCUMENTS ---
{context_block}
--- END OF DOCUMENTS ---
{f'''
--- PREVIOUS CONVERSATION ---
{history_block}
--- END OF PREVIOUS CONVERSATION ---
''' if history_block else ''}
USER QUERY:
The user wants to import the following product into Israel:
"{product_description}"

Please provide:
1. A clear verdict: ALLOWED / REJECTED / CONDITIONAL
2. The specific reason based on the documents above
3. Which regulation or list applies
4. What the user should do next
"""

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ]
        )

        return format_verdict(response.choices[0].message.content)

    except Exception as e:
        print(f"[ai_service] Error in analyze_text_query: {e}")
        return (
            "⚠️ Sorry, I couldn't complete the compliance check right now. "
            "Please try again in a moment or contact support."
        )


def analyze_image_query(image_bytes, additional_text=""):
    """
    Analyses a product image against Israeli customs compliance rules using
    Groq's vision model (llama-3.2-90b-vision-preview).

    additional_text — optional caption the user sent alongside the photo.

    Returns the formatted verdict string, or a friendly error message on failure.
    """
    try:
        client  = get_client()
        context = get_compliance_context()

        # Ensure image_bytes is raw bytes before encoding
        if hasattr(image_bytes, "read"):
            image_bytes = image_bytes.read()
        b64_image      = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{b64_image}"

        context_block = (
            context
            if context
            else "No compliance documents available. Use your general knowledge and note this limitation."
        )

        caption_line = f'They also wrote: "{additional_text}"' if additional_text else ""

        text_prompt = f"""--- COMPLIANCE DOCUMENTS ---
{context_block}
--- END OF DOCUMENTS ---

IMAGE ANALYSIS TASK:
The user has uploaded a photo of a product they wish to import into Israel.
{caption_line}

Please do the following in order:
1. EXTRACT all visible product information from the image:
   - Brand and model number
   - Frequency bands or RF specifications (if visible)
   - Certifications or approval marks (CE, FCC, PTCRB, etc.)
   - Voltage, wattage, or other technical specs
   - Country of manufacture
   - Any other relevant details

2. CROSS-REFERENCE the extracted details with the compliance documents above.

3. PROVIDE a full compliance verdict:
   - Clear verdict: ALLOWED / REJECTED / CONDITIONAL
   - Specific reason based on the documents
   - Which regulation or list applies
   - What the user should do next
"""

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                        {"type": "text",      "text": text_prompt},
                    ],
                },
            ]
        )

        return format_verdict(response.choices[0].message.content)

    except Exception as e:
        print(f"[ai_service] Error in analyze_image_query: {type(e).__name__}: {e}")
        traceback.print_exc()
        return (
            "⚠️ Sorry, I couldn't analyse the image right now. "
            "Please try again or send the product name as text instead."
        )


def format_verdict(raw_response):
    """
    Returns the Groq response trimmed of surrounding whitespace.
    The model formats the full response itself including the header.
    """
    return raw_response.strip()
