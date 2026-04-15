"""
URL/link reading utilities for Importil.

Keeps fetch logic isolated so check.py can import these helpers
without introducing any circular dependencies.
"""

import re
import requests

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


# ── Jina fetch + text cleaning ────────────────────────────────────────────────

# Words that strongly indicate product-relevant content on a page.
# Lines containing these are prioritised over generic page content.
_PRODUCT_KEYWORDS = re.compile(
    r'\b(price|MHz|GHz|WiFi|Bluetooth|frequency|model|brand|watt|'
    r'specification|spec|wireless|radio|antenna|power|transmit|receive|'
    r'band|channel|certification|CE|FCC|ISM|voltage|dBm|weight|dimension)\b',
    re.IGNORECASE,
)


def clean_jina_text(raw_text):
    """
    Cleans raw Jina AI Reader output to surface the most product-relevant content.

    Steps:
      1. Truncate to the first 2 000 characters (fast pages already fit; noisy
         pages are cut before the boilerplate bloat compounds).
      2. Split into lines, strip leading/trailing whitespace.
      3. Drop blank lines and any line containing "%" — these are almost always
         URL-encoded slugs, tracking parameters, or breadcrumb noise.
      4. Separate the remaining lines into two buckets:
           - keyword_lines: contain at least one product-relevant term
           - other_lines:   everything else that passed the "%" filter
      5. Return keyword lines first, then other lines — so the AI sees the most
         signal-dense content at the top of its context window.

    Returns a single cleaned string (may be empty if the page was pure noise).
    """
    raw_text = raw_text[:2000]

    lines = [line.strip() for line in raw_text.splitlines()]

    clean_lines = [line for line in lines if line and '%' not in line]

    keyword_lines = [l for l in clean_lines if _PRODUCT_KEYWORDS.search(l)]
    other_lines   = [l for l in clean_lines if not _PRODUCT_KEYWORDS.search(l)]

    return '\n'.join(keyword_lines + other_lines)


def fetch_via_jina(url, timeout=20):
    """
    Fetches clean, readable page text from any URL using Jina AI Reader.
    Jina requires no API key — just prepend https://r.jina.ai/ to the URL.

    Returns the cleaned text produced by clean_jina_text().
    Raises requests.RequestException on network or HTTP errors.
    """
    jina_url = f"https://r.jina.ai/{url}"
    response = requests.get(
        jina_url,
        timeout=timeout,
        headers={"Accept": "text/plain", "X-Return-Format": "text"},
    )
    response.raise_for_status()
    return clean_jina_text(response.text)


# ── Low-confidence detection ──────────────────────────────────────────────────

# The AI SYSTEM_PROMPT produces a fixed Markdown template.  These patterns
# match the two markers that reliably indicate the model couldn't identify
# the product from the fetched page text.
_LOW_CONF_PATTERN = re.compile(
    r'\*Confidence\*\s*:\s*LOW'           # *Confidence:* LOW
    r'|'
    r'\*Product\*\s*:.*\b(Unknown|N/A|Not\s+identified)\b',  # *Product:* Unknown / N/A
    re.IGNORECASE,
)


def is_low_confidence(response_text):
    """
    Returns True when the AI response signals that it couldn't identify the
    product well enough to deliver a reliable verdict.

    Detects:
      - *Confidence:* LOW  (from the fixed response template)
      - *Product:* Unknown / N/A / Not identified
    """
    return bool(_LOW_CONF_PATTERN.search(response_text))
