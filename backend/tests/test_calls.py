"""Unit tests for the SQLite-backed call analytics layer (Day 8)."""

import os
from datetime import datetime, timedelta, timezone

import pytest

import calls


@pytest.fixture()
def db(tmp_path):
    """Point the calls layer at a throwaway database per test."""
    old = calls._DB_PATH
    calls._DB_PATH = os.path.join(str(tmp_path), "test_calls.db")
    calls.init_db()
    yield calls
    calls._DB_PATH = old


def _record(db, **overrides):
    started = overrides.pop("started_at", datetime.now(timezone.utc) - timedelta(seconds=42))
    defaults = {
        "call_id": None,
        "channel": "browser",
        "language": "te",
        "started_at": started,
        "outcome": "successful",
        "success_signals": ["eligibility_check_completed"],
    }
    defaults.update(overrides)
    return db.record_call(**defaults)


def test_record_and_summary_counts(db):
    _record(db, outcome="successful", success_signals=["eligibility_check_completed"])
    _record(db, outcome="successful", success_signals=["documents_delivered"])
    _record(db, outcome="failed", success_signals=[], failure_type="user_hangup")

    summary = db.get_summary()
    assert summary["total_calls"] == 3
    assert summary["successful_calls"] == 2
    assert summary["failed_calls"] == 1
    assert summary["success_rate"] == pytest.approx(66.7, abs=0.1)


def test_empty_summary_has_zero_rate(db):
    summary = db.get_summary()
    assert summary == {
        "total_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "success_rate": 0.0,
        "by_failure_type": {},
        "by_channel": {},
    }


def test_failure_type_defaults_to_incomplete_when_missing(db):
    _record(db, outcome="failed", success_signals=[], failure_type="not_a_real_type")
    summary = db.get_summary()
    assert summary["by_failure_type"] == {"incomplete": 1}


def test_successful_outcome_ignores_failure_type(db):
    record = _record(
        db,
        outcome="successful",
        success_signals=["documents_delivered"],
        failure_type="user_hangup",
    )
    assert record["failure_type"] == ""
    calls_list = db.list_recent_calls()
    assert calls_list[0]["failure_type"] == ""


def test_by_channel_breakdown(db):
    _record(db, channel="browser")
    _record(db, channel="sip")
    _record(db, channel="sip")
    summary = db.get_summary()
    assert summary["by_channel"] == {"browser": 1, "sip": 2}


def test_list_recent_calls_orders_newest_first(db):
    now = datetime.now(timezone.utc)
    _record(db, call_id="CALL-old", started_at=now - timedelta(hours=1))
    _record(db, call_id="CALL-new", started_at=now)

    recent = db.list_recent_calls(limit=10)
    assert [c["call_id"] for c in recent] == ["CALL-new", "CALL-old"]


def test_list_recent_calls_respects_limit(db):
    for i in range(5):
        _record(db, call_id=f"CALL-{i}")
    assert len(db.list_recent_calls(limit=2)) == 2


def test_duration_is_computed_from_timestamps(db):
    started = datetime.now(timezone.utc) - timedelta(seconds=90)
    ended = started + timedelta(seconds=30)
    record = db.record_call(
        call_id="CALL-dur",
        channel="browser",
        started_at=started,
        ended_at=ended,
        outcome="successful",
        success_signals=["eligibility_check_completed"],
    )
    assert record["duration_secs"] == pytest.approx(30.0, abs=0.01)


def test_invalid_outcome_raises(db):
    with pytest.raises(ValueError):
        _record(db, outcome="maybe")


def test_unknown_channel_falls_back_to_unknown(db):
    record = _record(db, channel="carrier_pigeon")
    assert record["channel"] == "unknown"


def test_no_sensitive_fields_in_stored_record(db):
    """Privacy check (Day 8 Step 6): the calls table only has aggregate,
    non-identifying columns — there's no column to even accidentally put a
    caller name, phone number, or transcript into."""
    _record(db)
    stored = db.list_recent_calls()[0]
    assert set(stored.keys()) == {
        "call_id",
        "channel",
        "language",
        "started_at",
        "ended_at",
        "duration_secs",
        "outcome",
        "failure_type",
        "success_signals",
    }
