"""
URL/link reading utilities for Importil.

Keeps fetch logic isolated so check.py can import these helpers
without introducing any circular dependencies.
"""

import re
import requests

# Matches http:// and https:// URLs, stopping at whitespace or common
# surrounding characters. Trailing punctuation is stripped separately.
_URL_PATTERN = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)

# Characters that commonly appear after a URL in natural text but are
# not part of the URL itself (e.g. "check this: https://example.com.")
_TRAILING_PUNCT = '.,!?;:)\'\"'

# Max characters of Jina output fed to the AI — keeps prompts fast and cheap
JINA_MAX_CHARS = 4000


def extract_url(text):
    """
    Returns the first URL found in the message text, with trailing
    punctuation stripped. Returns None if no URL is present.
    """
    match = _URL_PATTERN.search(text)
    if not match:
        return None
    return match.group(0).rstrip(_TRAILING_PUNCT)


def fetch_via_jina(url, timeout=20):
    """
    Fetches clean, readable page text from any URL using Jina AI Reader.
    Jina requires no API key — just prepend https://r.jina.ai/ to the URL.

    Returns the extracted text (truncated to JINA_MAX_CHARS).
    Raises requests.RequestException on network or HTTP errors.
    """
    jina_url = f"https://r.jina.ai/{url}"
    response = requests.get(
        jina_url,
        timeout=timeout,
        headers={"Accept": "text/plain", "X-Return-Format": "text"},
    )
    response.raise_for_status()
    return response.text.strip()[:JINA_MAX_CHARS]
