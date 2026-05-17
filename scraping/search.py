"""
Tavily AI Search Integration.

Uses the Tavily API to search for interview questions, coding problems,
and educational resources for a given topic and difficulty level.
"""

import os
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tavily client (lazy-initialised)
# ---------------------------------------------------------------------------

_tavily_client = None


def _get_client():
    """Return a cached TavilyClient instance."""
    global _tavily_client
    if _tavily_client is None:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is missing. Add it to your .env file.")
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def search_interview_questions(topic: str, level: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web for interview questions on the given topic and level.

    Returns a list of dicts with keys:
      - title   : page title
      - url     : source URL
      - content : snippet / summary
    """
    query = f"{topic} {level} level interview questions and answers"
    logger.info("Tavily search → %s", query)

    try:
        client = _get_client()
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
        )

        results: List[Dict[str, Any]] = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            })

        logger.info("Tavily returned %d results", len(results))
        return results

    except Exception as exc:
        logger.exception("Tavily search failed for topic=%s", topic)
        raise RuntimeError(f"Tavily search error: {exc}") from exc


def search_coding_problems(topic: str, level: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for coding problems (LeetCode, GFG, etc.) on the given topic.

    Returns a list of dicts with keys:
      - title   : problem title
      - url     : problem URL
      - content : short description
    """
    query = f"{topic} {level} coding problems site:leetcode.com OR site:geeksforgeeks.org"
    logger.info("Tavily coding search → %s", query)

    try:
        client = _get_client()
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
        )

        results: List[Dict[str, Any]] = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            })

        logger.info("Tavily coding search returned %d results", len(results))
        return results

    except Exception as exc:
        logger.exception("Tavily coding search failed for topic=%s", topic)
        raise RuntimeError(f"Tavily coding search error: {exc}") from exc


def search_resources(topic: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for learning resources, tutorials, and documentation.

    Returns a list of dicts with keys:
      - title : resource title
      - url   : resource URL
    """
    query = f"{topic} tutorial guide documentation for beginners"
    logger.info("Tavily resource search → %s", query)

    try:
        client = _get_client()
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
        )

        return [
            {"title": item.get("title", ""), "url": item.get("url", "")}
            for item in response.get("results", [])
        ]

    except Exception as exc:
        logger.exception("Tavily resource search failed for topic=%s", topic)
        raise RuntimeError(f"Tavily resource search error: {exc}") from exc


def aggregate_search(topic: str, level: str) -> Dict[str, Any]:
    """
    Run all searches and return a combined payload.

    Returns:
        {
            "interview_results" : [ … ],
            "coding_results"    : [ … ],
            "resource_results"  : [ … ],
        }
    """
    return {
        "interview_results": search_interview_questions(topic, level),
        "coding_results": search_coding_problems(topic, level),
        "resource_results": search_resources(topic),
    }
