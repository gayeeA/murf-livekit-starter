"""Unit tests for the escalation-ticket layer (Day 7)."""

import os

import pytest

import escalations


@pytest.fixture()
def db(tmp_path):
    """Point the escalations layer at a throwaway database per test."""
    old = escalations._DB_PATH
    escalations._DB_PATH = os.path.join(str(tmp_path), "test_escalations.db")
    escalations.init_db()
    yield escalations
    escalations._DB_PATH = old


def test_create_escalation_returns_reference_id(db):
    record = db.create_or_update_escalation(
        caller_name="Ramesh",
        issue_summary="Lost 5000 rupees to a fake bank call",
        already_checked="Told caller to report via Sachet and 1930",
        urgency="high",
        language="Telugu",
        follow_up_method="call back",
    )
    assert record["reference_id"].startswith("ESC-")
    assert record["status"] == "open"
    assert record["urgency"] == "high"


def test_get_escalation_by_reference_id(db):
    created = db.create_or_update_escalation(
        caller_name="Ramesh", issue_summary="Disputed eligibility result", urgency="medium"
    )
    fetched = db.get_escalation(created["reference_id"])
    assert fetched is not None
    assert fetched["caller_name"] == "Ramesh"


def test_duplicate_report_updates_existing_open_ticket(db):
    first = db.create_or_update_escalation(
        caller_name="Ramesh", issue_summary="Suspicious UPI transaction", urgency="medium"
    )
    second = db.create_or_update_escalation(
        caller_name="Ramesh", issue_summary="Same issue, calling again", urgency="high"
    )
    assert first["reference_id"] == second["reference_id"]
    assert second["urgency"] == "high"
    assert len(second["notes"]) == 1

    all_tickets = db.list_all_escalations()
    assert len(all_tickets) == 1


def test_resolved_ticket_does_not_get_reused(db):
    first = db.create_or_update_escalation(caller_name="Ramesh", issue_summary="Issue A")
    db.update_status(first["reference_id"], "resolved")

    second = db.create_or_update_escalation(caller_name="Ramesh", issue_summary="Issue B")
    assert second["reference_id"] != first["reference_id"]


def test_list_open_escalations_excludes_resolved(db):
    open_ticket = db.create_or_update_escalation(caller_name="Ramesh", issue_summary="Open issue")
    resolved_ticket = db.create_or_update_escalation(caller_name="Suresh", issue_summary="Resolved issue")
    db.update_status(resolved_ticket["reference_id"], "resolved")

    open_list = db.list_open_escalations()
    ids = [r["reference_id"] for r in open_list]
    assert open_ticket["reference_id"] in ids
    assert resolved_ticket["reference_id"] not in ids


def test_update_status_rejects_invalid_status(db):
    ticket = db.create_or_update_escalation(caller_name="Ramesh", issue_summary="Issue")
    with pytest.raises(ValueError):
        db.update_status(ticket["reference_id"], "closed")


def test_invalid_urgency_falls_back_to_medium(db):
    record = db.create_or_update_escalation(
        caller_name="Ramesh", issue_summary="Issue", urgency="super-urgent"
    )
    assert record["urgency"] == "medium"


def test_sensitive_data_is_redacted_from_summary(db):
    record = db.create_or_update_escalation(
        caller_name="Ramesh",
        issue_summary="My OTP is 482913 and account number 9876543210 was used",
        already_checked="Aadhaar 1234 5678 9012 mentioned by caller",
    )
    assert "482913" not in record["issue_summary"]
    assert "9876543210" not in record["issue_summary"]
    assert "123456789012" not in record["already_checked"].replace(" ", "")
    assert "[redacted]" in record["issue_summary"]


@pytest.mark.asyncio
async def test_notify_discord_noop_without_webhook_url(db, monkeypatch):
    monkeypatch.delenv("DISCORD_ESCALATION_WEBHOOK_URL", raising=False)
    record = db.create_or_update_escalation(caller_name="Ramesh", issue_summary="Issue")
    sent = await db.notify_discord(record)
    assert sent is False
