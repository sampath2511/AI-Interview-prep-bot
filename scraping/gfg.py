"""
GeeksforGeeks (GFG) Problem Scraper.

Scrapes practice problems and article content from GeeksforGeeks
using BeautifulSoup + requests.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GFG_BASE_URL = "https://www.geeksforgeeks.org"
GFG_PRACTICE_API = "https://practiceapi.geeksforgeeks.org/api/v1/problems"
GFG_SEARCH_URL = "https://www.geeksforgeeks.org/search/{query}/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json",
}

# GFG difficulty mapping
DIFFICULTY_MAP = {
    "beginner": "school",
    "easy": "easy",
    "intermediate": "medium",
    "medium": "medium",
    "advanced": "hard",
    "hard": "hard",
}


# ---------------------------------------------------------------------------
# Practice-problems API
# ---------------------------------------------------------------------------


def fetch_practice_problems(
    topic: str,
    difficulty: str = "medium",
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Fetch coding problems from the GFG Practice API.

    Args:
        topic: Topic to search (e.g. "binary-tree").
        difficulty: One of beginner / easy / intermediate / medium / advanced / hard.
        limit: Max number of problems to return.

    Returns:
        List of dicts: title, url, difficulty, accuracy (if available).
    """
    gfg_diff = DIFFICULTY_MAP.get(difficulty.lower().strip(), "medium")
    tag_slug = topic.lower().strip().replace(" ", "-")

    params = {
        "page": 1,
        "difficulty[]": gfg_diff,
        "topic[]": tag_slug,
        "sortBy": "submissions",
        "count": limit,
    }

    logger.info("GFG Practice API → topic=%s, difficulty=%s", tag_slug, gfg_diff)

    try:
        resp = requests.get(GFG_PRACTICE_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("GFG Practice API failed: %s", exc)
        return []
    except ValueError:
        logger.warning("GFG Practice API returned non-JSON")
        return []

    results = data.get("results", [])

    return [
        {
            "title": p.get("problem_name", ""),
            "url": f"{GFG_BASE_URL}/problems/{p.get('problem_url', '')}/1",
            "difficulty": p.get("difficulty", gfg_diff).capitalize(),
            "accuracy": p.get("accuracy", "N/A"),
        }
        for p in results[:limit]
    ]


# ---------------------------------------------------------------------------
# Article / page scraping
# ---------------------------------------------------------------------------


def scrape_article(url: str) -> Optional[Dict[str, Any]]:
    """
    Scrape a GFG article page and extract structured content.

    Returns:
        Dict with keys: title, url, content, code_snippets
        or None on failure.
    """
    logger.info("Scraping GFG article: %s", url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch GFG page %s: %s", url, exc)
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Title
    title = ""
    title_tag = soup.find("h1") or soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Main article body
    article_div = (
        soup.find("article")
        or soup.find("div", class_=re.compile(r"article", re.I))
        or soup.find("div", {"id": "main"})
    )

    content = ""
    if article_div:
        # Remove script / style tags before extracting text
        for tag in article_div.find_all(["script", "style", "nav", "footer"]):
            tag.decompose()
        content = article_div.get_text(separator="\n", strip=True)

    # Extract code blocks
    code_snippets: List[str] = []
    for code_tag in soup.find_all("code"):
        code_text = code_tag.get_text(strip=True)
        if len(code_text) > 20:  # skip tiny inline code
            code_snippets.append(code_text)

    return {
        "title": title,
        "url": url,
        "content": content[:3000],  # cap length
        "code_snippets": code_snippets[:5],  # limit snippets
    }


# ---------------------------------------------------------------------------
# Search-based scraping
# ---------------------------------------------------------------------------


def search_gfg_problems(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Search GFG via its search page and scrape result links.

    Args:
        query: Free-text search query.
        limit: Max results.

    Returns:
        List of dicts: title, url
    """
    search_url = GFG_SEARCH_URL.format(query=quote_plus(query))
    logger.info("GFG search → %s", search_url)

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("GFG search request failed: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    results: List[Dict[str, str]] = []
    # GFG search results are usually in <a> tags within gcse result divs
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)
        if (
            "geeksforgeeks.org" in href
            and text
            and "/problems/" in href or "/practice/" in href or len(text) > 10
        ):
            if not any(r["url"] == href for r in results):
                results.append({"title": text, "url": href})
        if len(results) >= limit:
            break

    return results


# ---------------------------------------------------------------------------
# High-level helper
# ---------------------------------------------------------------------------


def get_problems(topic: str, level: str = "medium", limit: int = 5) -> List[Dict[str, Any]]:
    """
    High-level helper: fetch GFG practice problems for a topic + level.

    Tries the Practice API first, then falls back to search-based scraping.

    Args:
        topic: Topic name (e.g. "Binary Search Tree").
        level: Difficulty — "beginner", "easy", "intermediate", "advanced", etc.
        limit: Max problems.

    Returns:
        List of problem dicts.
    """
    problems = fetch_practice_problems(topic, difficulty=level, limit=limit)

    if not problems:
        logger.info("GFG Practice API returned nothing; trying search fallback")
        search_results = search_gfg_problems(f"{topic} {level} practice problems", limit=limit)
        problems = [
            {
                "title": r["title"],
                "url": r["url"],
                "difficulty": level.capitalize(),
                "accuracy": "N/A",
            }
            for r in search_results
        ]

    return problems
