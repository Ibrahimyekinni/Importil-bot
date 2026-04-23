import base64
import io
import re
import traceback

from groq import Groq, APITimeoutError


class AIServiceError(Exception):
    """Raised when the AI backend fails. Callers catch this and show a bilingual error."""

from config.settings import GROQ_API_KEY
from bot.services.drive_service import get_all_documents_text

TEXT_MODEL   = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

FREQUENCY_MAP = {
    "2.4ghz":    ("2400",  "2483.5", "EN 300 328"),
    "wifi":      ("2400",  "2483.5", "EN 300 328"),
    "bluetooth": ("2400",  "2483.5", "EN 300 328"),
    "bt":        ("2400",  "2483.5", "EN 300 328"),
    "ble":       ("2400",  "2483.5", "EN 300 328"),
    "5ghz":      ("5150",  "5350",   "EN 301 893"),
    "zigbee":    ("2400",  "2483.5", "EN 300 440"),
    "thread":    ("2400",  "2483.5", "EN 300 440"),
    "nfc":       ("13.56", "13.56",  "EN 300 330"),
    "rfid":      ("13.56", "13.56",  "EN 300 330"),
    "lora":      ("868",   "868.6",  "EN 300 220"),
    "433mhz":    ("433",   "434.79", "EN 300 220"),
    "433":       ("433",   "434.79", "EN 300 220"),
    "868mhz":    ("868",   "868.6",  "EN 300 220"),
    "868":       ("868",   "868.6",  "EN 300 220"),
}

HARD_STOPS = [
    ("5.8ghz", "⚠️ WARNING: 5.8GHz (5725-5875 MHz) is restricted in Israel. High risk of rejection."),
    ("5725",   "⚠️ WARNING: 5725-5875 MHz is restricted in Israel. High risk of rejection."),
    ("5875",   "⚠️ WARNING: 5725-5875 MHz is restricted in Israel. High risk of rejection."),
]

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
- Never mention documents, files, or knowledge base in your responses. Speak as an expert who inherently knows Israeli telecommunications regulations. Never say "based on the provided documents" or similar phrases.
- If product info is insufficient, ask ONE specific technical question
- When CONDITIONAL, always ask for: exact frequency/MHz, power output in mW or W, intended use (personal/commercial)
- Be conversational and direct like a knowledgeable colleague
- Format verdicts clearly with the exact template provided below — always include every field
- Confidence should be HIGH when you know the frequency, MEDIUM when inferring from product category

FORMATTING RULES (Telegram bot — strictly enforced):
- NEVER use markdown headers: no #, ##, ### — Telegram renders them as raw text
- NEVER use **double asterisk bold** — use *single asterisk* for bold instead
- NEVER use --- or === dividers
- Only Telegram-compatible formatting is allowed: *bold*, _italic_, `code`

RESPONSE FORMAT - ALWAYS USE THIS EXACTLY (all 7 fields required):
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


def normalize_frequencies(product_text, ai_response):
    """
    Appends hard-stop warnings and frequency reference blocks to the AI response
    based on keywords found in the product description. Called after every AI
    call so the user always gets gov.il form data when a known frequency is mentioned.
    """
    text = product_text.lower()
    result = ai_response

    for keyword, warning in HARD_STOPS:
        if keyword in text:
            result += f"\n\n{warning}"

    seen = set()
    for keyword, (from_mhz, to_mhz, standard) in FREQUENCY_MAP.items():
        if keyword in text:
            entry = (from_mhz, to_mhz, standard)
            if entry not in seen:
                seen.add(entry)
                result += (
                    f"\n\n📡 Frequency Reference (for gov.il form):\n"
                    f"From: {from_mhz} MHz | To: {to_mhz} MHz | Standard: {standard}"
                )

    return result


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


def analyze_text_query(product_description, conversation_history=None, lang_instruction=""):
    """
    Analyses a text-based product query against Israeli customs compliance rules.

    conversation_history — optional list of previous {'role', 'content'} dicts.
    When provided the full history is injected above the current query so the
    model understands this is a follow-up exchange.

    lang_instruction — e.g. "Respond in Hebrew (עברית)." appended to the prompt.

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

        user_message = f"""--- CONTEXT ---
{context_block}
--- END CONTEXT ---
{f'''
--- PREVIOUS CONVERSATION ---
{history_block}
--- END OF PREVIOUS CONVERSATION ---
''' if history_block else ''}
USER QUERY:
The user wants to import the following product into Israel:
"{product_description}"

Please provide a full compliance verdict using the required format:
1. Verdict: ALLOWED / REJECTED / CONDITIONAL
2. Product identification
3. Frequency/Band
4. Reason (cite the specific regulation)
5. Regulation
6. Action Required
7. Confidence
{lang_instruction}"""

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            timeout=30,
        )

        ai_response = format_verdict(response.choices[0].message.content)
        return normalize_frequencies(product_description, ai_response)

    except APITimeoutError as e:
        print(f"[ai_service] Timeout in analyze_text_query: {e}")
        raise AIServiceError("ai_timeout") from e
    except Exception as e:
        print(f"[ai_service] Error in analyze_text_query: {e}")
        raise AIServiceError("ai_unavailable") from e


def analyze_image_query(image_bytes, additional_text="", lang_instruction="", conversation_history=None):
    """
    Analyses a product image against Israeli customs compliance rules using
    Groq's vision model (llama-4-scout).

    additional_text   — optional caption the user sent alongside the photo.
    lang_instruction  — e.g. "Respond in Hebrew (עברית)." appended to the prompt.

    Returns the formatted verdict string, or raises AIServiceError on failure.
    """
    try:
        client = get_client()

        # Ensure image_bytes is raw bytes before encoding
        if hasattr(image_bytes, "read"):
            image_bytes = image_bytes.read()

        print(f"[ai_service] analyze_image_query: image size={len(image_bytes)} bytes, model={VISION_MODEL}")

        b64_image      = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{b64_image}"

        caption_line = f'They also wrote: "{additional_text}"' if additional_text else ""

        history_block = _build_history_block(conversation_history)
        prior_context = (
            f"PRIOR CONVERSATION CONTEXT:\n{history_block}\n--- END OF PRIOR CONTEXT ---\n\n"
            if history_block else ""
        )

        # Do NOT inject the Drive compliance context here — the SYSTEM_PROMPT already
        # contains every rule and the image itself already consumes significant tokens.
        # Adding thousands of Drive-doc tokens on top pushes the call over the model's
        # context limit, which is the root cause of silent vision failures.
        text_prompt = f"""{prior_context}IMAGE ANALYSIS TASK:
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

2. PROVIDE a full compliance verdict using the required format:
   - Verdict: ALLOWED / REJECTED / CONDITIONAL
   - Product identification
   - Frequency/Band
   - Reason (cite the specific regulation)
   - Regulation
   - Action Required
   - Confidence
{lang_instruction}"""

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
            ],
            timeout=60,
        )

        ai_response = format_verdict(response.choices[0].message.content)
        print(f"[ai_service] analyze_image_query: success, response length={len(ai_response)}")
        return normalize_frequencies(additional_text, ai_response)

    except APITimeoutError as e:
        print(f"[ai_service] Timeout in analyze_image_query: {e}")
        raise AIServiceError("ai_timeout") from e
    except Exception as e:
        print(f"[ai_service] Error in analyze_image_query: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise AIServiceError("ai_unavailable") from e


def format_verdict(raw_response):
    """
    Cleans the Groq response for Telegram: strips unsupported markdown
    (# headers, **double-star bold**, --- dividers) and normalises whitespace.
    """
    text = raw_response.strip()
    print(f"[format_verdict] RAW: {repr(text[:300])}")
    # Strip #{1,6} followed by a space wherever they appear (inline or line-start).
    # The previous ^-anchored pattern missed headers Groq emits mid-string.
    text = re.sub(r'#{1,6}\s+', '', text)
    # **bold** → *bold* (Telegram uses single asterisks)
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text, flags=re.DOTALL)
    # Standalone --- or === divider lines → removed
    text = re.sub(r'^[-=]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Collapse runs of 3+ blank lines left by removals
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    print(f"[format_verdict] CLEANED: {repr(text[:300])}")
    return text
