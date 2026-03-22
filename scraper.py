"""
scraper.py
----------
Layer 1: Pure data extraction. Zero AI involved.
Fetches webpage HTML and extracts factual metrics using BeautifulSoup.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re


def fetch_page(url: str) -> tuple[str, BeautifulSoup]:
    """Fetch raw HTML and return both raw text and parsed soup."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return response.text, soup


def extract_metrics(url: str) -> dict:
    """
    Extract all factual metrics from a webpage.
    Returns a structured dict organized by domain (ontological structure).
    """
    raw_html, soup = fetch_page(url)
    parsed_url = urlparse(url)
    base_domain = parsed_url.netloc

    # ── Word Count ────────────────────────────────────────────────────────────
    body_text = soup.get_text(separator=" ", strip=True)
    word_count = len(body_text.split())

    # ── Headings ──────────────────────────────────────────────────────────────
    h1_tags = soup.find_all("h1")
    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")

    # ── Meta Tags ─────────────────────────────────────────────────────────────
    meta_title_tag = soup.find("title")
    meta_title = meta_title_tag.get_text(strip=True) if meta_title_tag else ""

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = (
        meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""
    )

    # ── Links ─────────────────────────────────────────────────────────────────
    all_links = soup.find_all("a", href=True)
    internal_links = []
    external_links = []

    for link in all_links:
        href = link["href"]
        full_url = urljoin(url, href)
        link_domain = urlparse(full_url).netloc
        if link_domain == base_domain or href.startswith("/") or href.startswith("#"):
            internal_links.append(href)
        elif href.startswith("http"):
            external_links.append(href)

    # ── Images ────────────────────────────────────────────────────────────────
    all_images = soup.find_all("img")
    images_missing_alt = [
        img for img in all_images
        if not img.get("alt") or img.get("alt", "").strip() == ""
    ]
    missing_alt_pct = (
        round((len(images_missing_alt) / len(all_images)) * 100, 1)
        if all_images else 0
    )

    # ── CTAs ──────────────────────────────────────────────────────────────────
    cta_keywords = [
        "get started", "sign up", "buy now", "learn more", "contact us",
        "request a quote", "book a demo", "try free", "get a quote",
        "schedule", "download", "subscribe", "start free", "get access",
        "talk to us", "free trial", "see pricing", "watch demo", "apply now"
    ]

    cta_elements = []

    # Buttons
    for btn in soup.find_all("button"):
        text = btn.get_text(strip=True).lower()
        if any(kw in text for kw in cta_keywords) or len(text) < 40:
            cta_elements.append(btn.get_text(strip=True))

    # Links that act as CTAs
    for link in soup.find_all("a"):
        text = link.get_text(strip=True).lower()
        if any(kw in text for kw in cta_keywords):
            cta_elements.append(link.get_text(strip=True))

    # Remove duplicates
    cta_elements = list(set(cta_elements))[:20]

    # ── Page Content Sample (for AI) ──────────────────────────────────────────
    # Remove script/style tags for cleaner text
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    clean_text = soup.get_text(separator=" ", strip=True)
    clean_text = re.sub(r'\s+', ' ', clean_text)

    # ── Structured Metrics Dict (Ontological Organization) ────────────────────
    metrics = {
        "url": url,
        "seo": {
            "meta_title": meta_title,
            "meta_title_length": len(meta_title),
            "meta_description": meta_description,
            "meta_description_length": len(meta_description),
            "h1_count": len(h1_tags),
            "h1_texts": [h.get_text(strip=True) for h in h1_tags[:3]],
            "h2_count": len(h2_tags),
            "h3_count": len(h3_tags),
            "missing_alt_pct": missing_alt_pct,
        },
        "content": {
            "word_count": word_count,
            "page_text_sample": clean_text[:3000],
        },
        "cta": {
            "cta_count": len(cta_elements),
            "cta_examples": cta_elements[:5],
            "cta_density": round(len(cta_elements) / max(word_count, 1), 4),
        },
        "links": {
            "internal_count": len(internal_links),
            "external_count": len(external_links),
        },
        "images": {
            "total_count": len(all_images),
            "missing_alt_count": len(images_missing_alt),
            "missing_alt_pct": missing_alt_pct,
        },
    }

    return metrics
