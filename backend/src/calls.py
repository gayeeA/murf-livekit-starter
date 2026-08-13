"""Call analytics for the Pooja voice agent (Day 8).

A small SQLite-backed log of every call the agent handles, written once per
call when the session closes. This is deliberately separate from
``memory.py`` (regular-caller facts) and ``escalations.py`` (human-handoff
tickets) — it exists purely to answer "how is the agent doing", not to
remember anything about a specific person.

SUCCESS DEFINITION (Financial Services track, from Day 2 objectives):
    A call is successful if the caller reached at least one of the concrete
    outcomes Pooja exists to deliver:
      - completed a government-scheme eligibility check
      - received a scheme's document checklist
      - had a human-escalation ticket created (fraud report / dispute that
        needed a real person — the "appropriate escalation" outcome)
    A call that ends without reaching any of these is recorded as failed,
    even if nothing broke — the caller may simply have hung up, declined to
    continue, or been chatting about something Pooja can't resolve herself.

PRIVACY (Day 8 Step 6): only aggregate, non-identifying fields are stored —
call id, channel, timestamps, duration, outcome, failure type, and which
outcome types were reached. No caller name, no transcript, no phone number,
no account/financial details ever land in this table.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("agent.calls")

_DB_PATH = os.environ.get(
    "CALLS_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calls.db"),
)

_lock = threading.Lock()

VALID_CHANNELS = ("browser", "sip", "unknown")
VALID_OUTCOMES = ("successful", "failed")
# Groupings for the "Advanced" failure-type breakdown (Day 8).
FAILURE_TYPES = (
    "user_hangup",       # caller left before reaching an outcome
    "user_declined",     # caller explicitly asked to stop / opted out
    "no_response",       # caller went silent and the agent closed gracefully
    "error",             # an unrecoverable STT/LLM/TTS error ended the call
    "incomplete",        # call ended for some other reason, no outcome reached
)


def new_call_id() -> str:
    """Generate a fresh call id. Call once per call, at session start."""
    return "CALL-" + uuid.uuid4().hex[:12]


def _connect() -> Any:
    import sqlite3

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the calls table if it does not exist."""
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calls (
                    call_id       TEXT PRIMARY KEY,
                    channel       TEXT NOT NULL DEFAULT 'unknown',
                    language      TEXT NOT NULL DEFAULT '',
                    started_at    TEXT NOT NULL,
                    ended_at      TEXT NOT NULL,
                    duration_secs REAL NOT NULL DEFAULT 0,
                    outcome       TEXT NOT NULL,
                    failure_type  TEXT NOT NULL DEFAULT '',
                    success_signals TEXT NOT NULL DEFAULT '[]',
                    close_reason  TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
    logger.info("Calls database ready at %s", _DB_PATH)


def record_call(
    *,
    call_id: str | None = None,
    channel: str = "unknown",
    language: str = "",
    started_at: datetime,
    ended_at: datetime | None = None,
    outcome: str,
    failure_type: str = "",
    success_signals: list[str] | None = None,
    close_reason: str = "",
) -> dict[str, Any]:
    """Write one completed call to the log. Called once, when a call ends.

    Args:
        call_id: Stable id generated at call start via ``new_call_id()``.
            A fresh one is generated if omitted.
        channel: "browser", "sip", or "unknown".
        language: Best-guess spoken language for the call, if detected.
        started_at / ended_at: Call boundaries (UTC). ``ended_at`` defaults
            to now.
        outcome: "successful" or "failed".
        failure_type: One of ``FAILURE_TYPES``, required when outcome is
            "failed" (ignored otherwise).
        success_signals: Which success condition(s) were reached, e.g.
            ["eligibility_check_completed"]. Empty for a failed call.
        close_reason: Raw session close reason from the framework, kept for
            debugging (e.g. "user_initiated", "error").
    """
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"Invalid outcome: {outcome!r}")
    if channel not in VALID_CHANNELS:
        channel = "unknown"
    if outcome == "failed" and failure_type not in FAILURE_TYPES:
        failure_type = "incomplete"
    if outcome == "successful":
        failure_type = ""

    call_id = call_id or new_call_id()
    ended_at = ended_at or datetime.now(timezone.utc)
    duration_secs = max(0.0, (ended_at - started_at).total_seconds())

    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO calls (
                    call_id, channel, language, started_at, ended_at,
                    duration_secs, outcome, failure_type, success_signals,
                    close_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    channel,
                    language,
                    started_at.isoformat(),
                    ended_at.isoformat(),
                    duration_secs,
                    outcome,
                    failure_type,
                    json.dumps(success_signals or []),
                    close_reason,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    logger.info(
        "Recorded call %s: channel=%s outcome=%s failure_type=%s signals=%s duration=%.1fs",
        call_id, channel, outcome, failure_type, success_signals, duration_secs,
    )
    return {
        "call_id": call_id,
        "channel": channel,
        "outcome": outcome,
        "failure_type": failure_type,
        "duration_secs": duration_secs,
    }


def _row_to_call(row: Any) -> dict[str, Any]:
    try:
        signals = json.loads(row["success_signals"])
    except (json.JSONDecodeError, TypeError):
        signals = []
    return {
        "call_id": row["call_id"],
        "channel": row["channel"],
        "language": row["language"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "duration_secs": row["duration_secs"],
        "outcome": row["outcome"],
        "failure_type": row["failure_type"],
        "success_signals": signals if isinstance(signals, list) else [],
    }


def get_summary() -> dict[str, Any]:
    """Total / successful / failed counts, success rate, and breakdowns.

    This is the data the Day 8 dashboard's three required numbers (and the
    optional success-rate / failure-type extras) come from.
    """
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute("SELECT outcome, failure_type, channel FROM calls").fetchall()
        finally:
            conn.close()

    total = len(rows)
    successful = sum(1 for r in rows if r["outcome"] == "successful")
    failed = total - successful

    by_failure_type: dict[str, int] = {}
    by_channel: dict[str, int] = {}
    for r in rows:
        by_channel[r["channel"]] = by_channel.get(r["channel"], 0) + 1
        if r["outcome"] == "failed":
            ft = r["failure_type"] or "incomplete"
            by_failure_type[ft] = by_failure_type.get(ft, 0) + 1

    return {
        "total_calls": total,
        "successful_calls": successful,
        "failed_calls": failed,
        "success_rate": round((successful / total) * 100, 1) if total else 0.0,
        "by_failure_type": by_failure_type,
        "by_channel": by_channel,
    }


def list_recent_calls(limit: int = 20) -> list[dict[str, Any]]:
    """Recent calls, newest first, for the dashboard's call-history table.

    Only non-sensitive fields (see module docstring) — safe for a public
    dashboard.
    """
    limit = max(1, min(limit, 200))
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM calls ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
        finally:
            conn.close()
    return [_row_to_call(row) for row in rows]
