#!/usr/bin/env python3
"""
MongoDB Writer — core/writers/mongo_writer.py

Writes normalized arrest records to MongoDB Atlas using bulk upsert.
Dedup key: (County, Booking_Number)

Usage:
    from core.writers.mongo_writer import write_to_mongo, ping_mongo

    stats = write_to_mongo(records, county="Lee")
    ok = ping_mongo()
"""

import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _get_client():
    """Get a MongoClient using MONGODB_URI from environment."""
    try:
        from pymongo import MongoClient
    except ImportError:
        logger.warning("pymongo not installed — pip install pymongo")
        return None

    uri = os.getenv("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI not set — skipping MongoDB write")
        return None

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return None


def ping_mongo() -> bool:
    """Test MongoDB connection. Returns True if reachable."""
    client = _get_client()
    if not client:
        return False
    try:
        client.admin.command("ping")
        logger.info("MongoDB ping: OK")
        return True
    except Exception as e:
        logger.error(f"MongoDB ping failed: {e}")
        return False
    finally:
        client.close()


def write_to_mongo(records: list, county: str = "Unknown") -> dict:
    """
    Bulk upsert arrest records into MongoDB Atlas.

    Args:
        records: List of normalized arrest record dicts.
        county: County name (used as fallback if not in record).

    Returns:
        dict with stats: { inserted, updated, errors, total }
    """
    stats = {"inserted": 0, "updated": 0, "errors": 0, "total": len(records)}

    if not records:
        logger.info("No records to write to MongoDB")
        return stats

    client = _get_client()
    if not client:
        logger.warning("MongoDB unavailable — records not written")
        return stats

    try:
        from pymongo import UpdateOne

        db = client["shamrock_arrests"]
        collection = db["arrests"]

        # Ensure compound index exists for dedup
        collection.create_index(
            [("County", 1), ("Booking_Number", 1)],
            unique=True,
            name="county_booking_dedup",
        )

        operations = []
        now = datetime.now(timezone.utc).isoformat()

        for record in records:
            rec_county = record.get("County") or county
            booking_num = record.get("Booking_Number") or record.get("booking_number")

            if not booking_num:
                stats["errors"] += 1
                continue

            # Normalize the record for MongoDB
            doc = {**record}
            doc["County"] = rec_county
            doc["Booking_Number"] = booking_num
            doc["_updated_at"] = now
            doc.setdefault("_source", "swfl-arrest-scrapers")
            doc.setdefault("_pipeline_version", "2.0")

            operations.append(
                UpdateOne(
                    {"County": rec_county, "Booking_Number": booking_num},
                    {"$set": doc, "$setOnInsert": {"_created_at": now}},
                    upsert=True,
                )
            )

        if operations:
            result = collection.bulk_write(operations, ordered=False)
            stats["inserted"] = result.upserted_count
            stats["updated"] = result.modified_count
            logger.info(
                f"MongoDB: {stats['inserted']} inserted, "
                f"{stats['updated']} updated, "
                f"{stats['errors']} errors "
                f"({len(operations)} total ops)"
            )
        else:
            logger.warning("No valid operations to write to MongoDB")

    except Exception as e:
        logger.error(f"MongoDB bulk write failed: {e}", exc_info=True)
        stats["errors"] = len(records)
    finally:
        client.close()

    return stats
