"""
FastAPI backend for the Interview Preparation Bot.
Provides endpoints for generating interview prep material.

Pipeline:
  1. Tavily AI search  → raw interview questions + coding problem links
  2. LeetCode / GFG scrapers → structured problem data
  3. Gemini AI          → summarise, deduplicate, format JSON
  4. MongoDB            → persist search history
  5. Return structured  → {questions, answers, coding_problems, sources}
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.models import PrepareRequest, PrepareResponse, CodingProblem

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

# Validate required API keys are present (never hardcode them)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Interview Prep Bot API",
    description="AI-powered interview preparation backend",
    version="1.0.0",
)

# CORS middleware — allow the frontend to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Catch unhandled exceptions and return a clean JSON error."""
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.exception("Unhandled error during request: %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."},
        )


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return consistent JSON for HTTP exceptions."""
    logger.warning("HTTP %s on %s: %s", exc.status_code, request.url, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for any unhandled exception."""
    logger.exception("Unexpected error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root():
    """Health-check endpoint."""
    return {"status": "ok", "message": "Interview Prep Bot API is running"}


@app.post("/prepare", response_model=PrepareResponse, tags=["Preparation"])
async def prepare(payload: PrepareRequest):
    """
    Generate interview preparation material for a given topic and level.

    **Full pipeline:**
    1. Search the web via Tavily for interview questions & coding problems
    2. Scrape LeetCode and GeeksforGeeks for practice problems
    3. Send all raw data to Gemini AI for summarisation & deduplication
    4. Save the result to MongoDB
    5. Return the structured JSON response

    Accepts a JSON body with:
    - **topic**: The subject to prepare (e.g. "Binary Trees")
    - **level**: Difficulty level (e.g. "beginner", "intermediate", "advanced")

    Returns structured JSON with questions, answers, coding_problems, and sources.
    """
    topic = payload.topic
    level = payload.level
    logger.info("=== /prepare START === topic=%s, level=%s", topic, level)

    try:
        # ---------------------------------------------------------------
        # Step 1 — Tavily AI Search
        # ---------------------------------------------------------------
        logger.info("[1/4] Running Tavily search...")
        from scraping.search import search_interview_questions, search_coding_problems

        interview_results = search_interview_questions(topic, level)
        coding_search_results = search_coding_problems(topic, level)

        logger.info(
            "  Tavily returned %d interview results, %d coding results",
            len(interview_results), len(coding_search_results),
        )

        # ---------------------------------------------------------------
        # Step 2 — Scrape LeetCode + GFG for practice problems
        # ---------------------------------------------------------------
        logger.info("[2/4] Scraping LeetCode & GFG...")
        from scraping.leetcode import get_problems as lc_get_problems
        from scraping.gfg import get_problems as gfg_get_problems

        lc_problems = []
        gfg_problems = []

        try:
            lc_problems = lc_get_problems(topic, level, limit=5)
            logger.info("  LeetCode: %d problems", len(lc_problems))
        except Exception as exc:
            logger.warning("  LeetCode scraping failed (non-fatal): %s", exc)

        try:
            gfg_problems = gfg_get_problems(topic, level, limit=5)
            logger.info("  GFG: %d problems", len(gfg_problems))
        except Exception as exc:
            logger.warning("  GFG scraping failed (non-fatal): %s", exc)

        # Merge all coding problem results for Gemini
        all_coding_results = coding_search_results + [
            {"title": p.get("title", ""), "url": p.get("url", ""), "content": ""}
            for p in lc_problems + gfg_problems
        ]

        # ---------------------------------------------------------------
        # Step 3 — Gemini AI: summarise, deduplicate, format
        # ---------------------------------------------------------------
        logger.info("[3/4] Sending to Gemini AI for processing...")
        from ai.gemini_service import generate_prep_material

        ai_result = generate_prep_material(
            topic=topic,
            level=level,
            search_results=interview_results,
            coding_results=all_coding_results,
        )

        logger.info(
            "  Gemini returned %d questions, %d coding problems, %d sources",
            len(ai_result.get("questions", [])),
            len(ai_result.get("coding_problems", [])),
            len(ai_result.get("sources", [])),
        )

        # ---------------------------------------------------------------
        # Step 4 — Save to MongoDB
        # ---------------------------------------------------------------
        logger.info("[4/4] Saving to MongoDB...")
        try:
            from database.mongo import save_search
            doc_id = save_search(topic, level, ai_result)
            logger.info("  Saved to MongoDB — id=%s", doc_id)
        except Exception as exc:
            # DB failure is non-fatal; we still return the result
            logger.warning("  MongoDB save failed (non-fatal): %s", exc)

        # ---------------------------------------------------------------
        # Build response
        # ---------------------------------------------------------------
        response = PrepareResponse(
            topic=topic,
            level=level,
            questions=ai_result.get("questions", []),
            coding_problems=ai_result.get("coding_problems", []),
            sources=ai_result.get("sources", []),
        )

        logger.info("=== /prepare DONE === topic=%s", topic)
        return response

    except Exception as exc:
        logger.exception("Failed to process /prepare for topic=%s", topic)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/history", tags=["History"])
async def history(limit: int = 20):
    """Retrieve recent search history from MongoDB."""
    try:
        from database.mongo import get_search_history
        records = get_search_history(limit=limit)
        return {"history": records}
    except Exception as exc:
        logger.exception("Failed to fetch history")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/history/{doc_id}", tags=["History"])
async def history_detail(doc_id: str):
    """Retrieve a single past search result by its ID."""
    try:
        from database.mongo import get_search_by_id
        record = get_search_by_id(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Search not found")
        return record
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch history detail for id=%s", doc_id)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Entry point (for development)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
