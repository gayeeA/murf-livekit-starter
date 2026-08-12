"""Human-escalation requests for the Pooja voice agent (Day 7).

Pooja should not try to resolve everything herself. Two situations always
go to a human (Financial Services track):
    1. The caller reports possible fraud — money already lost, or a
       transaction/impersonation attempt underway.
    2. The caller needs a decision Pooja cannot make on her own — a
       disputed eligibility result, a rejected application, or an explicit
       request to speak with a human advisor.

This module is the storage + notification layer behind the "create_escalation"
tool in agent.py: it keeps a small SQLite ticket queue (so open requests can
be listed/checked even without the notification channel), and best-effort
notifies a real channel (a Discord webhook) when one is configured.

Financial Services privacy rule: the free-text summary fields are stripped
of anything that looks like an OTP/PIN/CVV/password/account number/Aadhaar/
PAN before they are stored or sent anywhere. Contact details in
`follow_up_value` are intentionally NOT stripped — the whole point of an
escalation is for a human to be able to reach the caller back — but the
agent should only ever put a phone number there with the caller's explicit,
just-given consent (see `SYSTEM_PROMPT`'s HUMAN ESCALATION section).
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

logger = logging.getLogger("agent.escalations")

_DB_PATH = os.environ.get(
    "ESCALATIONS_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "escalations.db"),
)

_lock = threading.Lock()

VALID_URGENCIES = ("low", "medium", "high", "emergency")
VALID_STATUSES = ("open", "in_progress", "resolved")

# Same category of redaction as memory.py's _sanitize(), applied to the
# free-text summary fields rather than a facts dict.
_SENSITIVE_PATTERNS = [
    re.compile(r"\botp\b", re.IGNORECASE),
    re.compile(r"\bpin\b", re.IGNORECASE),
    re.compile(r"\bcvv\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\b\d{12}\b"),  # 12-digit Aadhaar-like number
    re.compile(r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b"),  # Aadhaar written with spaces/dashes
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),  # PAN-like format
    re.compile(r"\b\d{4,16}\b"),  # OTP/PIN/CVV/account/card-like digit runs.
    # Errs toward over-redacting (e.g. a 4-digit rupee amount) rather than
    # ever leaking a 4-6 digit OTP or PIN the caller read out loud.
]


def _redact(text: str) -> str:
    """Strip anything that looks like a secret or an identifier from free text."""
    if not text:
        return text
    cleaned = text
    for pattern in _SENSITIVE_PATTERNS:
        cleaned = pattern.sub("[redacted]", cleaned)
    return cleaned


def _connect() -> Any:
    import sqlite3

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the escalations table if it does not exist."""
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS escalations (
                    reference_id     TEXT PRIMARY KEY,
                    caller_name      TEXT NOT NULL,
                    issue_summary    TEXT NOT NULL,
                    already_checked  TEXT NOT NULL DEFAULT '',
                    urgency          TEXT NOT NULL,
                    language         TEXT NOT NULL DEFAULT '',
                    follow_up_method TEXT NOT NULL DEFAULT '',
                    follow_up_value  TEXT NOT NULL DEFAULT '',
                    status           TEXT NOT NULL DEFAULT 'open',
                    notes            TEXT NOT NULL DEFAULT '[]',
                    created_at       TEXT NOT NULL,
                    updated_at       TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
    logger.info("Escalations database ready at %s", _DB_PATH)


def _row_to_escalation(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    try:
        notes = json.loads(row["notes"])
    except (json.JSONDecodeError, TypeError):
        notes = []
    return {
        "reference_id": row["reference_id"],
        "caller_name": row["caller_name"],
        "issue_summary": row["issue_summary"],
        "already_checked": row["already_checked"],
        "urgency": row["urgency"],
        "language": row["language"],
        "follow_up_method": row["follow_up_method"],
        "follow_up_value": row["follow_up_value"],
        "status": row["status"],
        "notes": notes if isinstance(notes, list) else [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def find_open_escalation(caller_name: str) -> dict[str, Any] | None:
    """Find an already-open (not resolved) escalation for this caller, if any."""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM escalations WHERE lower(caller_name) = ? AND status != 'resolved' "
                "ORDER BY created_at DESC LIMIT 1",
                (caller_name.strip().lower(),),
            ).fetchone()
        finally:
            conn.close()
    return _row_to_escalation(row)


def get_escalation(reference_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM escalations WHERE reference_id = ?", (reference_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_escalation(row)


def list_open_escalations() -> list[dict[str, Any]]:
    """List every escalation that isn't resolved yet, newest first."""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM escalations WHERE status != 'resolved' ORDER BY created_at DESC"
            ).fetchall()
        finally:
            conn.close()
    return [r for r in (_row_to_escalation(row) for row in rows) if r]


def list_all_escalations() -> list[dict[str, Any]]:
    """List every escalation regardless of status, newest first."""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
        finally:
            conn.close()
    return [r for r in (_row_to_escalation(row) for row in rows) if r]


def update_status(reference_id: str, status: str) -> bool:
    """Move an escalation to a new status (open / in_progress / resolved)."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status!r}")
    now = datetime.now(timezone.utc).isoformat()
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "UPDATE escalations SET status = ?, updated_at = ? WHERE reference_id = ?",
                (status, now, reference_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def create_or_update_escalation(
    *,
    caller_name: str,
    issue_summary: str,
    already_checked: str = "",
    urgency: str = "medium",
    language: str = "",
    follow_up_method: str = "",
    follow_up_value: str = "",
) -> dict[str, Any]:
    """Create a new escalation, or update the caller's existing open one.

    If the same caller already has an open (non-resolved) escalation, this
    appends a note to it instead of creating a duplicate ticket — a caller
    calling back about the same unresolved problem should not fragment into
    multiple open requests.

    All free-text fields are redacted of anything that looks like an OTP,
    PIN, CVV, password, or account/Aadhaar/PAN-like number before storage.
    """
    if urgency not in VALID_URGENCIES:
        urgency = "medium"

    issue_summary = _redact(issue_summary)
    already_checked = _redact(already_checked)
    now = datetime.now(timezone.utc).isoformat()

    existing = find_open_escalation(caller_name)
    if existing is not None:
        notes = existing["notes"] + [
            {"at": now, "issue_summary": issue_summary, "urgency": urgency}
        ]
        with _lock:
            conn = _connect()
            try:
                conn.execute(
                    "UPDATE escalations SET notes = ?, urgency = ?, updated_at = ? WHERE reference_id = ?",
                    (json.dumps(notes), urgency, now, existing["reference_id"]),
                )
                conn.commit()
            finally:
                conn.close()
        record = get_escalation(existing["reference_id"])
        logger.info("Updated existing escalation %s for %s", existing["reference_id"], caller_name)
        assert record is not None
        return record

    reference_id = "ESC-" + uuid.uuid4().hex[:8].upper()
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO escalations (
                    reference_id, caller_name, issue_summary, already_checked,
                    urgency, language, follow_up_method, follow_up_value,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', '[]', ?, ?)
                """,
                (
                    reference_id,
                    caller_name,
                    issue_summary,
                    already_checked,
                    urgency,
                    language,
                    follow_up_method,
                    follow_up_value,
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    logger.info("Created escalation %s for %s (urgency=%s)", reference_id, caller_name, urgency)
    record = get_escalation(reference_id)
    assert record is not None
    return record


async def notify_discord(record: dict[str, Any], webhook_url: str | None = None) -> bool:
    """Best-effort post the escalation to a Discord webhook. Returns True on success.

    Never raises — a notification failure should not break the call. If no
    webhook URL is configured, this is a no-op (the ticket still exists in
    the local queue and can be read via ``list_open_escalations``).
    """
    webhook_url = webhook_url or os.environ.get("DISCORD_ESCALATION_WEBHOOK_URL")
    if not webhook_url:
        logger.info(
            "No DISCORD_ESCALATION_WEBHOOK_URL configured; escalation %s stored locally only",
            record["reference_id"],
        )
        return False

    content = (
        f"**New escalation `{record['reference_id']}`** — urgency: **{record['urgency']}**\n"
        f"Caller: {record['caller_name']} (language: {record['language'] or 'unknown'})\n"
        f"Issue: {record['issue_summary']}\n"
        f"Already checked: {record['already_checked'] or '—'}\n"
        f"Follow-up: {record['follow_up_method'] or 'unspecified'}"
        + (f" ({record['follow_up_value']})" if record["follow_up_value"] else "")
    )

    try:
        import aiohttp

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                webhook_url, json={"content": content}, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp,
        ):
            if resp.status >= 300:
                logger.warning("Discord webhook returned status %s", resp.status)
                return False
        return True
    except Exception:
        logger.exception("Failed to notify Discord for escalation %s", record["reference_id"])
        return False
