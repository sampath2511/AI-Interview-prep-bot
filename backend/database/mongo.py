"""
MongoDB Database Service.

Handles connection to MongoDB Atlas and provides helpers to
save and retrieve search history.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

MONGODB_URI = os.getenv("MONGODB_URI")

_client: Optional[MongoClient] = None
_db = None


def get_database():
    """
    Return the MongoDB database instance (lazy-initialised singleton).

    Raises RuntimeError if MONGODB_URI is not set or connection fails.
    """
    global _client, _db

    if _db is not None:
        return _db

    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI is missing. Add it to your .env file.")

    try:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Force a connection check
        _client.admin.command("ping")
        logger.info("Connected to MongoDB Atlas successfully ✓")
    except ConnectionFailure as exc:
        logger.exception("MongoDB connection failed")
        raise RuntimeError(f"MongoDB connection error: {exc}") from exc

    _db = _client["interview_bot"]
    return _db


def close_connection():
    """Gracefully close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


def _search_history_collection():
    """Return the search_history collection."""
    return get_database()["search_history"]


# ---------------------------------------------------------------------------
# CRUD — Search History
# ---------------------------------------------------------------------------


def save_search(
    topic: str,
    level: str,
    result: Dict[str, Any],
) -> str:
    """
    Save a search result to the database.

    Args:
        topic: The topic that was searched.
        level: The difficulty level.
        result: The structured JSON response
                (questions, answers, coding_problems, sources).

    Returns:
        The inserted document's _id as a string.
    """
    document = {
        "topic": topic,
        "level": level,
        "result": result,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        inserted = _search_history_collection().insert_one(document)
        doc_id = str(inserted.inserted_id)
        logger.info("Saved search to MongoDB — id=%s, topic=%s", doc_id, topic)
        return doc_id
    except PyMongoError as exc:
        logger.exception("Failed to save search to MongoDB")
        raise RuntimeError(f"Database save error: {exc}") from exc


def get_search_history(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve the most recent search history entries.

    Args:
        limit: Max number of records to return.

    Returns:
        List of history dicts (most recent first).
    """
    try:
        cursor = (
            _search_history_collection()
            .find({}, {"_id": 1, "topic": 1, "level": 1, "created_at": 1})
            .sort("created_at", -1)
            .limit(limit)
        )
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except PyMongoError as exc:
        logger.exception("Failed to fetch search history")
        raise RuntimeError(f"Database read error: {exc}") from exc


def get_search_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single search result by its document ID.

    Args:
        doc_id: The MongoDB _id string.

    Returns:
        The full document dict, or None if not found.
    """
    from bson import ObjectId

    try:
        doc = _search_history_collection().find_one({"_id": ObjectId(doc_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    except PyMongoError as exc:
        logger.exception("Failed to fetch search by id=%s", doc_id)
        raise RuntimeError(f"Database read error: {exc}") from exc


def find_searches_by_topic(topic: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search history by topic (case-insensitive substring match).

    Args:
        topic: Partial or full topic string.
        limit: Max results.

    Returns:
        List of matching history dicts.
    """
    try:
        cursor = (
            _search_history_collection()
            .find(
                {"topic": {"$regex": topic, "$options": "i"}},
            )
            .sort("created_at", -1)
            .limit(limit)
        )
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except PyMongoError as exc:
        logger.exception("Failed to search by topic=%s", topic)
        raise RuntimeError(f"Database search error: {exc}") from exc


def delete_search(doc_id: str) -> bool:
    """
    Delete a single search history entry.

    Returns True if a document was deleted, False otherwise.
    """
    from bson import ObjectId

    try:
        result = _search_history_collection().delete_one({"_id": ObjectId(doc_id)})
        deleted = result.deleted_count > 0
        if deleted:
            logger.info("Deleted search history id=%s", doc_id)
        return deleted
    except PyMongoError as exc:
        logger.exception("Failed to delete search id=%s", doc_id)
        raise RuntimeError(f"Database delete error: {exc}") from exc
