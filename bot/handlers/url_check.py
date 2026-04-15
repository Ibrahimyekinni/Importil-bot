"""
URL/link reading utilities for Importil.

Keeps fetch logic isolated so check.py can import these helpers
without introducing any circular dependencies.
"""

import re
import requests

from config.settings import FIRECRAWL_API_KEY

# ── URL detection ─────────────────────────────────────────────────────────────

# Matches http:// and https:// URLs, stopping at whitespace or common
# surrounding characters. Trailing punctuation is stripped separately.
_URL_PATTERN = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)

# Characters that commonly appear after a URL in natural text but are
# not part of the URL itself (e.g. "check this: https://example.com.")
_TRAILING_PUNCT = '.,!?;:)\'\"`'


def extract_url(text):
    """
    Returns the first URL found in the message text, with trailing
    punctuation stripped. Returns None if no URL is present.
    """
    match = _URL_PATTERN.search(text)
    if not match:
        return None
    return match.group(0).rstrip(_TRAILING_PUNCT)


# ── Firecrawl fetch ───────────────────────────────────────────────────────────

def fetch_via_firecrawl(url):
    """
    Scrapes a product page using the Firecrawl v1 API and returns the main
    content as clean Markdown (capped at 3 000 characters).

    Returns None if the request fails, the API returns an error, or the
    scraped content is empty — callers must handle the None case explicitly.
    Never raises; all exceptions are caught and logged internally.
    """
    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
            timeout=15,
        )
        data = response.json()
        if data.get("success") and data.get("data", {}).get("markdown"):
            return data["data"]["markdown"][:3000]
        return None
    except Exception as e:
        print(f"[url_check] Firecrawl error for {url}: {e}")
        return None


# ── Low-confidence detection ──────────────────────────────────────────────────

# The AI SYSTEM_PROMPT produces a fixed Markdown template. These patterns
# match the two markers that reliably indicate the model couldn't identify
# the product from the fetched page content.
_LOW_CONF_PATTERN = re.compile(
    r'\*Confidence\*\s*:\s*LOW'                                  # *Confidence:* LOW
    r'|'
    r'\*Product\*\s*:.*\b(Unknown|N/A|Not\s+identified)\b',     # *Product:* Unknown / N/A
    re.IGNORECASE,
)


def is_low_confidence(response_text):
    """
    Returns True when the AI response signals it couldn't identify the product
    well enough to deliver a reliable verdict.

    Detects:
      - *Confidence:* LOW  (from the fixed response template)
      - *Product:* Unknown / N/A / Not identified
    """
    return bool(_LOW_CONF_PATTERN.search(response_text))
