"""
mongo_writer.py — MongoDB Atlas writer for the SWFL Arrest Scrapers pipeline.

Architecture:
    Scraper → Normalizer → Lead Scorer → mongo_writer → MongoDB Atlas

The writer connects directly to MongoDB Atlas using the pymongo driver and the
standard (non-SRV) connection string stored in the MONGODB_URI environment
variable. This avoids the SRV DNS resolution issues that affect Docker
environments.

Deduplication is enforced via a compound unique index on (County, Booking_Number).
Records are upserted — existing records are updated, new records are inserted.

Usage:
    from core.writers.mongo_writer import write_to_mongo

    stats = write_to_mongo(records, county="CHARLOTTE")

Environment Variables:
    MONGODB_URI     — Standard mongodb:// connection string (required)
    MONGO_DB        — Database name (default: shamrock_arrests)
    MONGO_COLL      — Collection name (default: arrests)

Dependencies:
    pip install pymongo
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
DEFAULT_DB   = "shamrock_arrests"
DEFAULT_COLL = "arrests"

# Fields that form the compound dedup key
DEDUP_KEY_FIELDS = ("County", "Booking_Number")


# ── Connection helper ──────────────────────────────────────────────────────────
def _get_collection(
    mongodb_uri: Optional[str] = None,
    db_name: Optional[str] = None,
    coll_name: Optional[str] = None,
):
    """
    Return a pymongo Collection object.
    Raises ValueError if MONGODB_URI is not set.
    """
    try:
        from pymongo import MongoClient, ASCENDING
        from pymongo.errors import CollectionInvalid
    except ImportError as exc:
        raise ImportError(
            "pymongo is required for mongo_writer. "
            "Install it with: pip install pymongo"
        ) from exc

    uri  = mongodb_uri or os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError(
            "MONGODB_URI environment variable is not set. "
            "Set it to the standard (non-SRV) MongoDB connection string."
        )

    db_name   = db_name   or os.getenv("MONGO_DB",   DEFAULT_DB)
    coll_name = coll_name or os.getenv("MONGO_COLL", DEFAULT_COLL)

    client     = MongoClient(uri, serverSelectionTimeoutMS=8000)
    db         = client[db_name]
    collection = db[coll_name]

    # Ensure the compound unique index exists (idempotent)
    try:
        collection.create_index(
            [(f, ASCENDING) for f in DEDUP_KEY_FIELDS],
            unique=True,
            name="county_booking_unique",
            background=True,
        )
    except Exception as idx_err:
        logger.warning(f"[mongo_writer] Could not ensure index: {idx_err}")

    return collection


# ── Public Writer ──────────────────────────────────────────────────────────────
def write_to_mongo(
    records: List[Dict[str, Any]],
    county: str,
    mongodb_uri: Optional[str] = None,
    db_name: Optional[str] = None,
    coll_name: Optional[str] = None,
) -> Dict[str, int]:
    """
    Upsert a list of normalised arrest records into MongoDB Atlas.

    Each record is matched by (County, Booking_Number). If a matching document
    already exists it is updated; otherwise a new document is inserted.

    Args:
        records:     List of record dicts conforming to the 34-column schema.
        county:      County name (e.g. "CHARLOTTE"). Used to fill the County
                     field if it is missing from a record.
        mongodb_uri: Override for MONGODB_URI env var.
        db_name:     Override for MONGO_DB env var.
        coll_name:   Override for MONGO_COLL env var.

    Returns:
        Dict with keys: inserted, updated, skipped, errors, total
    """
    from pymongo import UpdateOne
    from pymongo.errors import BulkWriteError

    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "total": len(records)}

    if not records:
        logger.info("[mongo_writer] No records to write.")
        return stats

    try:
        collection = _get_collection(mongodb_uri, db_name, coll_name)
    except Exception as conn_err:
        logger.error(f"[mongo_writer] Connection failed: {conn_err}")
        stats["errors"] = len(records)
        return stats

    now_iso = datetime.now(timezone.utc).isoformat()
    operations: List[UpdateOne] = []

    for record in records:
        # Ensure County is set
        if not record.get("County"):
            record["County"] = county.upper()

        booking_number = record.get("Booking_Number", "").strip()
        county_val     = record.get("County", "").strip().upper()

        if not booking_number or not county_val:
            logger.warning(
                f"[mongo_writer] Skipping record missing County or Booking_Number: "
                f"{record.get('Full_Name', 'UNKNOWN')}"
            )
            stats["skipped"] += 1
            continue

        # Build the update document
        doc = {k: v for k, v in record.items() if v not in (None, "")}
        doc["County"]         = county_val
        doc["Booking_Number"] = booking_number
        doc["updated_at"]     = now_iso

        filter_doc = {"County": county_val, "Booking_Number": booking_number}
        update_doc = {
            "$set":         doc,
            "$setOnInsert": {"created_at": now_iso},
        }

        operations.append(UpdateOne(filter_doc, update_doc, upsert=True))

    if not operations:
        logger.info("[mongo_writer] All records skipped (missing keys).")
        return stats

    try:
        result = collection.bulk_write(operations, ordered=False)
        stats["inserted"] = result.upserted_count
        stats["updated"]  = result.modified_count
        logger.info(
            f"[mongo_writer] {county.upper()}: "
            f"{stats['inserted']} inserted, {stats['updated']} updated, "
            f"{stats['skipped']} skipped, {stats['errors']} errors "
            f"out of {stats['total']} records."
        )
    except BulkWriteError as bwe:
        # Partial success — some ops may have succeeded
        details = bwe.details
        stats["inserted"] = details.get("nUpserted", 0)
        stats["updated"]  = details.get("nModified", 0)
        stats["errors"]   = len(details.get("writeErrors", []))
        logger.error(
            f"[mongo_writer] BulkWriteError for {county.upper()}: "
            f"{stats['errors']} errors. First: "
            f"{details.get('writeErrors', [{}])[0].get('errmsg', 'unknown')}"
        )
    except Exception as exc:
        logger.error(f"[mongo_writer] Unexpected error for {county.upper()}: {exc}")
        stats["errors"] = len(operations)

    return stats


# ── Convenience ping ───────────────────────────────────────────────────────────
def ping_mongo(mongodb_uri: Optional[str] = None) -> bool:
    """
    Test the MongoDB connection. Returns True on success, False on failure.
    """
    try:
        coll = _get_collection(mongodb_uri)
        coll.database.client.admin.command("ping")
        logger.info("[mongo_writer] ✅ MongoDB Atlas connection OK.")
        return True
    except Exception as exc:
        logger.error(f"[mongo_writer] ❌ MongoDB Atlas connection FAILED: {exc}")
        return False
