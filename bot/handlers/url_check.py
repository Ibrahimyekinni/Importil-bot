"""
URL/link reading utilities for Importil.

Keeps fetch logic isolated so check.py can import these helpers
without introducing any circular dependencies.
"""

import re
import requests

from config.settings import FIRECRAWL_API_KEY

# ── URL detection ─────────────────────────────────────────────────────────────

_URL_PATTERN = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)
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


# ── Step 1: lightweight meta tag extraction ───────────────────────────────────

def fetch_page_meta(url):
    """
    Fetches the page HTML directly and extracts product-identifying meta tags:
    og:title, og:description, <title>, and meta description.

    Returns a pipe-joined string of whatever was found, or None if the request
    fails or no meta tags are present. Never raises.

    This is intentionally lightweight — no API key, no external service, fast.
    It works well for most e-commerce product pages that embed structured meta
    tags (AliExpress, Amazon, eBay, manufacturer sites, etc.).
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=10)

        html = response.text
        text_parts = []

        # Try both attribute orderings so we catch whichever the page uses
        og_title  = (re.findall(r'property="og:title"\s+content="([^"]+)"', html) or
                     re.findall(r'content="([^"]+)"\s+property="og:title"', html))
        og_desc   = (re.findall(r'property="og:description"\s+content="([^"]+)"', html) or
                     re.findall(r'content="([^"]+)"\s+property="og:description"', html))
        title     = re.findall(r'<title[^>]*>([^<]+)</title>', html)
        meta_desc = (re.findall(r'name="description"\s+content="([^"]+)"', html) or
                     re.findall(r'content="([^"]+)"\s+name="description"', html))

        for items in [og_title, title, og_desc, meta_desc]:
            if items:
                text_parts.append(items[0].strip())

        return " | ".join(text_parts) if text_parts else None

    except Exception as e:
        print(f"[url_check] Meta extraction failed for {url}: {e}")
        return None


# ── Step 2: Firecrawl fallback ────────────────────────────────────────────────

def fetch_via_firecrawl(url):
    """
    Scrapes a product page using the Firecrawl v1 API and returns the main
    content as clean Markdown (capped at 3 000 characters).

    Returns None if the request fails, the API returns an error, or the
    scraped content is empty. Never raises.
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


# ── Orchestrator: try meta first, Firecrawl as fallback ───────────────────────

# Phrases that indicate Firecrawl got a login wall, redirect page, or generic
# site shell instead of actual product content.
_JUNK_PHRASES = [
    "I'm shopping for",
    "Sign in",
    "Shopping for",
    "Smarter Shopping",
    "Back to top",
    "Customer Service",
    "All Categories",
]


def _is_junk_content(text):
    """Returns True if the text looks like a login wall or generic site page."""
    return any(phrase.lower() in text.lower() for phrase in _JUNK_PHRASES)


def fetch_product_content(url):
    """
    Two-step content extraction strategy:

      1. fetch_page_meta()  — direct HTTP + regex meta-tag extraction.
                              Fast, free, no API key.
                              Works for most e-commerce pages.
      2. fetch_via_firecrawl() — full-page scrape via Firecrawl API.
                              Slower, uses API credits, but handles
                              JS-heavy or auth-walled pages better.
                              Result is discarded if it looks like a
                              login wall or generic site shell.

    Returns the first result with >= 30 characters and real product
    content, or None if both strategies fail or return junk.
    """
    meta = fetch_page_meta(url)
    if meta and len(meta.strip()) >= 30:
        print(f"[url_check] Meta extraction succeeded ({len(meta)} chars): {url}")
        return meta

    print(f"[url_check] Meta insufficient ({len(meta) if meta else 0} chars), trying Firecrawl: {url}")
    result = fetch_via_firecrawl(url)

    if result and _is_junk_content(result):
        print(f"[url_check] Firecrawl returned junk/login-wall content — discarding: {url}")
        return None

    if not result:
        print(f"[url_check] Both methods failed — returning None for: {url}")

    return result


# ── Low-confidence detection ──────────────────────────────────────────────────

_LOW_CONF_PATTERN = re.compile(
    r'\*Confidence\*\s*:\s*LOW'
    r'|'
    r'\*Product\*\s*:.*\b(Unknown|N/A|Not\s+identified)\b',
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
