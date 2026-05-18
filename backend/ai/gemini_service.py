"""
OpenRouter AI Service.

Uses the OpenAI Python SDK to communicate with OpenRouter.
  - Summarise raw internet content into concise Q&A pairs
  - Remove duplicate / near-duplicate answers
  - Return a final structured JSON payload
"""

import json
import os
import logging
import re
import time
from typing import Dict, List, Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

# Initialise the OpenAI client pointing to OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Models to try in order (fallback chain on OpenRouter)
MODEL_CHAIN = [   
    "baidu/cobuddy:free",
    "openrouter/owl-alpha"
]

# Retry settings
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 5


def _generate_with_retry(system_prompt: str, user_prompt: str, temperature: float = 0.4, max_tokens: int = 4096) -> str:
    """
    Call OpenRouter with automatic retry and model fallback.
    Tries each model in MODEL_CHAIN, retrying up to MAX_RETRIES times total.
    """
    last_exc = None

    for model_name in MODEL_CHAIN:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info("OpenRouter request → model=%s (attempt %d)", model_name, attempt)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as exc:
                last_exc = exc
                exc_str = str(exc)
                if "429" in exc_str or "rate limit" in exc_str.lower():
                    logger.warning(
                        "Rate limited on %s (attempt %d/%d). Waiting %ds before retry...",
                        model_name, attempt, MAX_RETRIES, RETRY_DELAY_SECONDS,
                    )
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    # Non-rate-limit error — don't retry, try next model
                    logger.warning("OpenRouter error on %s: %s. Trying next model...", model_name, exc)
                    break

    raise RuntimeError(f"All OpenRouter models exhausted. Last error: {last_exc}")

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert interview preparation assistant.

You will receive raw search results about a programming topic.
Your job is to:
1. Extract top 5 unique, high-quality interview QUESTIONS (no duplicates).
2. Write clear, concise ANSWERS for each question.
3. Provide the original SOURCE URL for each question.
4. List top 5 relevant CODING PROBLEMS for hands-on practice, including title, difficulty, platform, and link.
5. List all unique SOURCE URLs you drew information from.

IMPORTANT RULES:
- Remove duplicate or near-duplicate questions; keep only the best version.
- Keep answers concise (3-5 sentences max) but technically accurate.
- Return ONLY valid JSON — no markdown fences, no extra text.
- Follow this exact schema:

{
  "questions": [
    {
      "question": "What is Virtual DOM?",
      "answer": "Virtual DOM improves rendering performance...",
      "source": "https://..."
    }
  ],
  "coding_problems": [
    {
      "title": "Two Sum",
      "difficulty": "Easy",
      "platform": "LeetCode",
      "link": "https://..."
    }
  ],
  "sources": [
    "https://..."
  ]
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_user_prompt(
    topic: str,
    level: str,
    search_results: List[Dict[str, Any]],
    coding_results: List[Dict[str, Any]],
) -> str:
    """Build the user-facing prompt from raw search data."""

    search_block = "\n\n".join(
        f"### {r.get('title', 'Untitled')}\nURL: {r.get('url', '')}\n{r.get('content', '')}"
        for r in search_results
    )

    coding_block = "\n".join(
        f"- {r.get('title', 'Untitled')} → {r.get('url', '')}"
        for r in coding_results
    )

    return (
        f"Topic: {topic}\n"
        f"Level: {level}\n\n"
        f"--- RAW SEARCH RESULTS ---\n{search_block}\n\n"
        f"--- CODING PROBLEMS FOUND ---\n{coding_block}\n\n"
        "Now produce the final structured JSON."
    )


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Parse JSON from the model response, stripping markdown fences if present.
    """
    if not text:
        return {
            "questions": [],
            "coding_problems": [],
            "sources": [],
        }

    # Remove ```json ... ``` wrappers
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI JSON response: %s", exc)
        logger.debug("Raw response: %s", text[:500])
        # Return empty structure as safe fallback
        return {
            "questions": [],
            "coding_problems": [],
            "sources": [],
        }


def _deduplicate(items: List[str]) -> List[str]:
    """Remove exact-duplicate strings while preserving order."""
    seen = set()
    unique = []
    for item in items:
        normalised = item.strip().lower()
        if normalised not in seen:
            seen.add(normalised)
            unique.append(item)
    return unique


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_prep_material(
    topic: str,
    level: str,
    search_results: List[Dict[str, Any]],
    coding_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Send raw search data to OpenRouter and return structured prep material.
    """
    logger.info("Generating prep material via OpenRouter — topic=%s, level=%s", topic, level)

    user_prompt = _build_user_prompt(topic, level, search_results, coding_results)

    try:
        raw_text = _generate_with_retry(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.4,
            max_tokens=4096,
        )
        logger.debug("AI raw response length: %d chars", len(raw_text or ""))

    except Exception as exc:
        logger.exception("OpenRouter API call failed")
        raise RuntimeError(f"OpenRouter API error: {exc}") from exc

    # Parse + clean up
    data = _extract_json(raw_text)

    # Deduplicate questions by question text
    questions_raw = data.get("questions", [])
    questions_clean = []
    seen_q = set()
    for q_item in questions_raw:
        if isinstance(q_item, dict):
            q_text = q_item.get("question", "").strip()
            key = q_text.lower()
            if key and key not in seen_q:
                seen_q.add(key)
                questions_clean.append({
                    "question": q_text,
                    "answer": q_item.get("answer", ""),
                    "source": q_item.get("source", ""),
                })

    # Deduplicate sources
    sources = _deduplicate(data.get("sources", []))

    # Normalise coding_problems
    coding_problems_raw = data.get("coding_problems", [])
    coding_problems = []
    for item in coding_problems_raw:
        if isinstance(item, dict):
            coding_problems.append({
                "title": item.get("title", ""),
                "difficulty": item.get("difficulty", "Medium"),
                "platform": item.get("platform", "Practice"),
                "link": item.get("link", ""),
            })

    result = {
        "questions": questions_clean,
        "coding_problems": coding_problems,
        "sources": sources,
    }

    logger.info(
        "AI produced %d questions, %d coding problems, %d sources",
        len(questions_clean), len(coding_problems), len(sources),
    )
    return result


def summarise_content(content: str, max_sentences: int = 5) -> str:
    """
    Use OpenRouter to summarise a block of raw internet content.
    """
    system_prompt = "You are a concise summarization assistant."
    user_prompt = (
        f"Summarise the following content in at most {max_sentences} sentences. "
        f"Be concise and technically accurate.\n\n{content}"
    )

    try:
        result = _generate_with_retry(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.3, max_tokens=1024)
        return result.strip()
    except Exception as exc:
        logger.exception("OpenRouter summarisation failed")
        return content[:500] + "..."
