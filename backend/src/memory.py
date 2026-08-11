"""Persistent caller memory for the Pooja voice agent.

A small SQLite-backed storage layer that lets the agent remember regular
callers between calls. The interface is deliberately small and storage-agnostic
(lookup / save / forget) so a MongoDB or Postgres backend could be swapped in
later without changing the agent tools in ``agent.py``.

Financial Services rule (hard requirement):
    We may store schemes already checked and eligibility answers, but we must
    NEVER store account numbers, ID numbers (Aadhaar/PAN), cards, OTPs, PINs,
    passwords, or phone numbers. ``_sanitize()`` strips any such values before
    anything is written to disk.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("agent.memory")

# Keys that must never be persisted for the Financial Services track.
# A fact whose key (or value) matches one of these is dropped before saving.
_SENSITIVE_KEY_PATTERNS = [
    re.compile(r"aadhaar", re.IGNORECASE),
    re.compile(r"pan\b", re.IGNORECASE),
    re.compile(r"account", re.IGNORECASE),
    re.compile(r"card", re.IGNORECASE),
    re.compile(r"cvv", re.IGNORECASE),
    re.compile(r"otp", re.IGNORECASE),
    re.compile(r"pin\b", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"phone", re.IGNORECASE),
    re.compile(r"mobile", re.IGNORECASE),
    re.compile(r"ifsc", re.IGNORECASE),
    re.compile(r"upi.?id", re.IGNORECASE),
]

# Value-level patterns that look like identifiers and should never be stored.
_SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"\b\d{12}\b"),  # 12-digit Aadhaar-like number
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),  # PAN-like format
    re.compile(r"\b\d{9,16}\b"),  # long account/phone-like digit runs
]

_DB_PATH = os.environ.get(
    "MEMORY_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.db"),
)

_lock = threading.Lock()


def _normalize_name(name: str) -> str:
    """Lowercase + strip for a case-insensitive name lookup key."""
    return " ".join(name.strip().lower().split())


def _is_sensitive_key(key: str) -> bool:
    return any(p.search(key) for p in _SENSITIVE_KEY_PATTERNS)


def _is_sensitive_value(value: str) -> bool:
    return any(p.search(value) for p in _SENSITIVE_VALUE_PATTERNS)


def _sanitize(facts: dict[str, Any]) -> dict[str, Any]:
    """Drop any fact that could reveal sensitive personal data.

    Works at both the key level (e.g. ``"aadhaar"``) and the value level
    (e.g. a 12-digit number hidden in a generic key). Returns a safe copy.
    """
    cleaned: dict[str, Any] = {}
    for key, value in facts.items():
        if _is_sensitive_key(key):
            logger.info("Dropping fact with sensitive key: %r", key)
            continue
        if isinstance(value, str):
            if _is_sensitive_key(value) or _is_sensitive_value(value):
                logger.info("Dropping fact with sensitive value under key: %r", key)
                continue
        elif isinstance(value, (int, float)) and abs(value) >= 10**9:
            # Long numeric runs (account/phone-like) are considered sensitive.
            logger.info("Dropping fact with long numeric value under key: %r", key)
            continue
        cleaned[key] = value
    return cleaned


def _connect() -> Any:
    import sqlite3

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users and do-not-call tables if they do not exist."""
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id         TEXT PRIMARY KEY,
                    name            TEXT NOT NULL,
                    facts           TEXT NOT NULL DEFAULT '{}',
                    last_interaction TEXT NOT NULL
                )
                """
            )
            # Outbound-call opt-out registry (Day 6). Kept separate from
            # `users.facts` because a phone number is exactly the kind of
            # identifier `_sanitize()` refuses to store as a caller "fact" —
            # this table exists purely so we stop dialing a number, not to
            # remember anything about the person.
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS do_not_call (
                    phone_number TEXT PRIMARY KEY,
                    created_at   TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
    logger.info("Memory database ready at %s", _DB_PATH)


def add_do_not_call(phone_number: str) -> None:
    """Record that this phone number must never be called again."""
    if not phone_number:
        return
    now = datetime.now(timezone.utc).isoformat()
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO do_not_call (phone_number, created_at) VALUES (?, ?)",
                (phone_number, now),
            )
            conn.commit()
        finally:
            conn.close()
    logger.info("Added %s to the do-not-call list", phone_number)


def is_do_not_call(phone_number: str) -> bool:
    """Check whether this phone number has opted out of outbound calls."""
    if not phone_number:
        return False
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM do_not_call WHERE phone_number = ?", (phone_number,)
            ).fetchone()
        finally:
            conn.close()
    return row is not None


def _row_to_user(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    try:
        facts = json.loads(row["facts"])
    except (json.JSONDecodeError, TypeError):
        facts = {}
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "facts": facts if isinstance(facts, dict) else {},
        "last_interaction": row["last_interaction"],
    }


def lookup_user(name: str) -> dict[str, Any] | None:
    """Find a caller by name (case-insensitive). Returns None if unknown."""
    key = _normalize_name(name)
    if not key:
        return None
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE lower(name) = ?", (key,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_user(row)


def lookup_user_by_id(user_id: str) -> dict[str, Any] | None:
    """Find a caller by their stable user_id."""
    if not user_id:
        return None
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_user(row)


def save_user(
    name: str,
    user_id: str | None = None,
    facts: dict[str, Any] | None = None,
    merge: bool = True,
) -> dict[str, Any]:
    """Save or update a caller's record.

    Args:
        name: Caller's display name.
        user_id: Stable id. If omitted, one is generated and the caller is
            treated as returning (their existing record is looked up by name).
        facts: Non-sensitive facts to persist (always sanitized).
        merge: When True, new facts are merged over any existing record;
            otherwise the existing record is replaced.

    Returns:
        The saved record.
    """
    facts = _sanitize(facts or {})
    key = _normalize_name(name)
    now = datetime.now(timezone.utc).isoformat()

    with _lock:
        conn = _connect()
        try:
            existing = None
            if user_id:
                existing = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
            if existing is None:
                existing = conn.execute(
                    "SELECT * FROM users WHERE lower(name) = ?", (key,)
                ).fetchone()

            if existing is not None:
                uid = existing["user_id"]
                stored_name = existing["name"]
                try:
                    stored_facts = json.loads(existing["facts"])
                except (json.JSONDecodeError, TypeError):
                    stored_facts = {}
                merged = {**stored_facts, **facts} if (merge and isinstance(stored_facts, dict)) else facts
                conn.execute(
                    "UPDATE users SET name = ?, facts = ?, last_interaction = ? WHERE user_id = ?",
                    (stored_name, json.dumps(merged), now, uid),
                )
            else:
                uid = user_id or uuid.uuid4().hex
                conn.execute(
                    "INSERT INTO users (user_id, name, facts, last_interaction) VALUES (?, ?, ?, ?)",
                    (uid, name, json.dumps(facts), now),
                )
            conn.commit()
        finally:
            conn.close()

    return {"user_id": uid, "name": name, "facts": facts, "last_interaction": now}


def forget_user(user_id: str) -> bool:
    """Delete a caller's record. Returns True if a record was removed."""
    if not user_id:
        return False
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def forget_user_by_name(name: str) -> bool:
    """Delete a caller's record looked up by name. Returns True if removed."""
    key = _normalize_name(name)
    if not key:
        return False
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM users WHERE lower(name) = ?", (key,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()
