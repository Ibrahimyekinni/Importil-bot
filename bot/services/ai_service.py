import base64
import io
import traceback

from groq import Groq

from config.settings import GROQ_API_KEY
from bot.services.drive_service import get_all_documents_text

TEXT_MODEL   = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# System prompt that defines Importil's persona and behaviour for every query
SYSTEM_PROMPT = """You are Importil, an elite Israeli customs compliance AI with deep expertise in Israeli telecommunications law. You have the following regulations memorized:

ISRAELI FREQUENCY REGULATIONS:
- 27MHz (CB Radio): ALLOWED for personal use, max 4W
- 49MHz: ALLOWED for toys and baby monitors only
- 72-73MHz: ALLOWED for RC models only
- 144-146MHz (VHF Amateur): ALLOWED only with amateur radio license
- 150-174MHz (VHF): RESTRICTED - requires Ministry of Communications license
- 433.05-434.79MHz: ALLOWED for short range devices, max 10mW
- 433-470MHz (UHF): RESTRICTED - requires special license, commercial use prohibited without approval
- 863-870MHz: ALLOWED for short range devices, max 25mW
- 915MHz ISM band: NOT ALLOWED in Israel (US band only, conflicts with GSM 900)
- 2.4GHz WiFi/Bluetooth: ALLOWED, must comply with ETSI EN 300 328
- 5.1-5.3GHz: RESTRICTED - indoor use only
- 5.47-5.725GHz: ALLOWED with DFS/TPC
- 5.725-5.875GHz: NOT ALLOWED in Israel
- GSM 850MHz: NOT ALLOWED in Israel (US band)
- GSM 900MHz: ALLOWED
- GSM 1800MHz: ALLOWED
- GSM 1900MHz: NOT ALLOWED in Israel (US band)
- 3G UMTS 2100MHz: ALLOWED
- 4G LTE Band 7 (2600MHz): ALLOWED
- 4G LTE Band 17/12 (700MHz): NOT ALLOWED in Israel

CERTIFICATION REQUIREMENTS:
- All radio equipment must carry CE marking and comply with EU RED directive (2014/53/EU)
- Equipment must be approved by Israeli Ministry of Communications (משרד התקשורת)
- FCC-only certified equipment is NOT automatically approved for Israel
- Equipment must meet Israeli Standard SI 461 for radio equipment
- Commercial radio equipment requires type approval from MOC

BANNED/RESTRICTED CATEGORIES:
- Devices operating on US-only frequency bands (915MHz ISM, GSM850, GSM1900, LTE Band 17)
- Jammers of any kind - STRICTLY PROHIBITED
- Devices exceeding power limits without license
- Walkie-talkies above 10mW without license
- Drones with video transmission on 5.8GHz - NOT ALLOWED
- RFID readers operating on 915MHz - NOT ALLOWED (use 868MHz instead)

ALLOWED CATEGORIES (generally):
- WiFi routers on 2.4GHz and 5GHz (with exceptions above)
- Bluetooth devices
- GSM/3G/4G devices on approved bands
- Gate controllers using approved frequencies (433MHz at low power)
- CE certified short range devices on 433MHz or 868MHz

COMMON PRODUCT QUICK VERDICTS (use these for confidence HIGH decisions):
- Standard WiFi router (2.4GHz only): ALLOWED - CE certified, ETSI EN 300 328 compliant
- Dual band WiFi router (2.4GHz + 5GHz): ALLOWED if 5.8GHz band is disabled or not present
- Bluetooth devices (all classes): ALLOWED
- GSM/3G/4G phones on standard bands: ALLOWED if no GSM850 or GSM1900
- iPhone/Samsung/standard smartphones: ALLOWED (use approved bands)
- Gate controllers on 433MHz under 10mW: ALLOWED
- Baby monitors on 2.4GHz: ALLOWED
- Baby monitors on 49MHz: ALLOWED
- Drone with 5.8GHz video: REJECTED
- Signal jammer any type: REJECTED immediately
- CB radio 27MHz under 4W: ALLOWED
- Walkie talkie under 10mW 433MHz: ALLOWED
- Walkie talkie over 10mW: CONDITIONAL (needs license)
- 915MHz any device: REJECTED
- GSM850 or GSM1900 device: REJECTED

When a product clearly matches one of these categories, give HIGH confidence verdict immediately without asking follow-up questions.

YOUR BEHAVIOR RULES:
- You ARE the compliance authority - give definitive verdicts
- NEVER say "consult the ministry" or "seek professional advice" - you ARE the expert
- NEVER mention "documents provided" or "based on documents" - you know regulations from memory
- If product info is insufficient, ask ONE specific technical question
- When CONDITIONAL, always ask for: exact frequency/MHz, power output in mW or W, intended use (personal/commercial)
- Be conversational and direct like a knowledgeable colleague
- Format verdicts clearly with the exact template provided
- Confidence should be HIGH when you know the frequency, MEDIUM when inferring from product category

RESPONSE FORMAT - ALWAYS USE THIS EXACTLY:
*🛃 Importil Compliance Check*
*==============================*

*Verdict:* ✅ ALLOWED / ❌ REJECTED / ⚠️ CONDITIONAL

*Product:* [identified product name and model]

*Frequency/Band:* [specific frequency if known]

*Reason:* [specific technical reason citing exact regulation]

*Regulation:* [specific Israeli standard or MOC regulation]

*Action Required:*
[specific next steps OR "None - product cleared for import" if allowed]

*Confidence:* HIGH / MEDIUM / LOW
"""


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
