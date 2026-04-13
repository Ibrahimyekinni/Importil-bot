import base64
import io

from groq import Groq

from config.settings import GROQ_API_KEY
from bot.services.drive_service import get_all_documents_text

TEXT_MODEL   = "llama-3.3-70b-versatile"
VISION_MODEL = "llama-3.2-90b-vision-preview"

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
- Be decisive and confident in every verdict"""


def get_client():
    """
    Creates and returns an authenticated Groq client using GROQ_API_KEY.
    """
    return Groq(api_key=GROQ_API_KEY)


def get_compliance_context():
    """
    Loads all compliance documents from Google Drive and returns their combined
    text. Injected into every prompt as the knowledge base.
    Returns an empty string if documents can't be fetched so the bot degrades
    gracefully rather than crashing.
    """
    try:
        # get_all_documents_text returns (combined_text, image_file_ids)
        # We only need the text portion here
        combined_text, _ = get_all_documents_text()
        return combined_text
    except Exception as e:
        print(f"[ai_service] Warning: could not load compliance documents: {e}")
        return ""


def analyze_text_query(product_description):
    """
    Analyses a text-based product query against Israeli customs compliance rules.

    Uses llama-3.3-70b-versatile via the Groq chat completions API.
    The system message carries the persona; the user message carries the
    compliance documents and the product query combined.

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

        user_message = f"""--- COMPLIANCE DOCUMENTS ---
{context_block}
--- END OF DOCUMENTS ---

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

    Steps:
      1. Encodes image_bytes as a base64 data URL
      2. Loads compliance documents as text context
      3. Sends both to Groq using the vision messages format
      4. Returns the formatted verdict string

    additional_text — optional caption the user sent alongside the photo.

    Returns the formatted verdict string, or a friendly error message on failure.
    """
    try:
        client  = get_client()
        context = get_compliance_context()

        # Encode raw bytes to base64 so they can be embedded in the JSON payload
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
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

        # Vision messages format: content is a list containing image_url and text parts
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url},
                        },
                        {
                            "type": "text",
                            "text": text_prompt,
                        },
                    ],
                },
            ]
        )

        return format_verdict(response.choices[0].message.content)

    except Exception as e:
        print(f"[ai_service] Error in analyze_image_query: {e}")
        return (
            "⚠️ Sorry, I couldn't analyse the image right now. "
            "Please try again or send the product name as text instead."
        )


def format_verdict(raw_response):
    """
    Returns the Groq response trimmed of surrounding whitespace.
    The model is instructed to format the full response itself (including the
    header), so no wrapper is added here to avoid duplication.
    """
    return raw_response.strip()
