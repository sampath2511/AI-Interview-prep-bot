"""
LeetCode Problem Scraper.

Extracts structured problem data from LeetCode problem pages
using BeautifulSoup and the public LeetCode GraphQL API.
"""

import logging
import re
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
LEETCODE_PROBLEM_URL = "https://leetcode.com/problems/{slug}/"
LEETCODE_TAG_URL = "https://leetcode.com/tag/{tag}/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
}

# Difficulty mapping from LeetCode's API
DIFFICULTY_MAP = {1: "Easy", 2: "Medium", 3: "Hard"}


# ---------------------------------------------------------------------------
# GraphQL helpers
# ---------------------------------------------------------------------------


def _graphql_query(query: str, variables: Dict[str, Any] = None) -> Optional[Dict]:
    """Execute a GraphQL query against LeetCode's public API."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        resp = requests.post(LEETCODE_GRAPHQL_URL, json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data")
    except requests.RequestException as exc:
        logger.warning("LeetCode GraphQL request failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_problem_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single LeetCode problem by its URL slug.

    Args:
        slug: The problem slug (e.g. "two-sum").

    Returns:
        Dict with keys: title, slug, url, difficulty, tags, description
        or None if the request fails.
    """
    query = """
    query getQuestionDetail($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            title
            titleSlug
            difficulty
            content
            topicTags {
                name
                slug
            }
        }
    }
    """
    data = _graphql_query(query, {"titleSlug": slug})
    if not data or not data.get("question"):
        logger.warning("No data returned for slug=%s", slug)
        return None

    q = data["question"]

    # Strip HTML from the description for a clean text version
    description = ""
    if q.get("content"):
        soup = BeautifulSoup(q["content"], "lxml")
        description = soup.get_text(separator="\n", strip=True)

    return {
        "title": q.get("title", ""),
        "slug": q.get("titleSlug", slug),
        "url": LEETCODE_PROBLEM_URL.format(slug=q.get("titleSlug", slug)),
        "difficulty": q.get("difficulty", "Unknown"),
        "tags": [tag["name"] for tag in q.get("topicTags", [])],
        "description": description,
    }


def fetch_problems_by_topic(topic: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch a list of LeetCode problems filtered by topic tag.

    Args:
        topic: A topic tag slug (e.g. "binary-tree", "dynamic-programming").
        limit: Maximum number of problems to return.

    Returns:
        List of dicts with keys: title, slug, url, difficulty, tags
    """
    # Normalise topic to a slug
    tag_slug = topic.lower().strip().replace(" ", "-")

    query = """
    query getTopicTag($slug: String!) {
        topicTag(slug: $slug) {
            questions {
                title
                titleSlug
                difficulty
                topicTags {
                    name
                }
            }
        }
    }
    """
    data = _graphql_query(query, {"slug": tag_slug})
    if not data or not data.get("topicTag"):
        logger.warning("No problems found for topic=%s", topic)
        return []

    questions = data["topicTag"].get("questions", [])[:limit]

    return [
        {
            "title": q.get("title", ""),
            "slug": q.get("titleSlug", ""),
            "url": LEETCODE_PROBLEM_URL.format(slug=q.get("titleSlug", "")),
            "difficulty": q.get("difficulty", "Unknown"),
            "tags": [t["name"] for t in q.get("topicTags", [])],
        }
        for q in questions
    ]


def extract_slug_from_url(url: str) -> Optional[str]:
    """
    Extract the problem slug from a LeetCode URL.

    >>> extract_slug_from_url("https://leetcode.com/problems/two-sum/")
    'two-sum'
    """
    match = re.search(r"leetcode\.com/problems/([^/?#]+)", url)
    return match.group(1) if match else None


def scrape_problem_page(url: str) -> Optional[Dict[str, Any]]:
    """
    Scrape a LeetCode problem page via HTTP and BeautifulSoup as a fallback
    when the GraphQL API is unavailable.

    Returns a dict with: title, url, difficulty (if found), description.
    """
    logger.info("Scraping LeetCode page: %s", url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch LeetCode page %s: %s", url, exc)
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Try to pull the title from the <title> tag
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True).replace(" - LeetCode", "")

    # Try to find difficulty badge
    difficulty = "Unknown"
    diff_el = soup.find("div", class_=re.compile(r"text-(easy|medium|hard)", re.I))
    if diff_el:
        difficulty = diff_el.get_text(strip=True).capitalize()

    # Extract visible text from the problem description area
    description = ""
    desc_div = soup.find("div", class_=re.compile(r"content", re.I))
    if desc_div:
        description = desc_div.get_text(separator="\n", strip=True)

    return {
        "title": title,
        "url": url,
        "difficulty": difficulty,
        "description": description[:2000],  # cap length
    }


def get_problems(topic: str, level: str = "medium", limit: int = 5) -> List[Dict[str, Any]]:
    """
    High-level helper: get LeetCode problems for a topic + difficulty.

    Tries the GraphQL API first; falls back to returning an empty list
    with a warning if the API is unreachable.

    Args:
        topic: Topic name (e.g. "Binary Tree").
        level: Difficulty filter — "easy", "medium", or "hard".
        limit: Max problems to return.

    Returns:
        Filtered list of problem dicts.
    """
    level_normalised = level.strip().capitalize()

    problems = fetch_problems_by_topic(topic, limit=limit * 3)  # over-fetch to filter

    if not problems:
        logger.info("GraphQL returned nothing for topic=%s; returning empty list", topic)
        return []

    # Filter by difficulty
    filtered = [p for p in problems if p.get("difficulty", "").capitalize() == level_normalised]

    return filtered[:limit]
