"""Unit tests for Day 6 outbound-call helpers: opening framing, opt-out
handling, and job-metadata parsing. These are pure-logic tests (no live SIP
trunk or LiveKit server needed) since the telephony plumbing itself can't be
exercised without real Twilio/LiveKit credentials.
"""

import json

import pytest

import agent
import outbound_caller
from agent import Assistant, build_outbound_opening


def test_outbound_opening_states_who_why_and_opt_out():
    message = build_outbound_opening(
        name="Ramesh", scheme_name="Jan Dhan Yojana", deadline="31 August"
    )
    assert "Pooja" in message
    assert "Ramesh" in message
    assert "Jan Dhan Yojana" in message
    assert "31 August" in message
    assert "stop calling" in message.lower()


def test_outbound_opening_handles_missing_name():
    message = build_outbound_opening(name=None, scheme_name="PMSBY", deadline="soon")
    assert "this is Pooja" in message
    assert "PMSBY" in message


def test_parse_outbound_metadata_valid_payload():
    raw = json.dumps(
        {
            "call_type": "outbound_reminder",
            "name": "Ramesh",
            "scheme_name": "Jan Dhan Yojana",
            "deadline": "31 August",
            "phone_number": "+919876543210",
        }
    )
    parsed = agent._parse_outbound_metadata(raw)
    assert parsed is not None
    assert parsed["name"] == "Ramesh"


@pytest.mark.parametrize("raw", ["", None, "not json", json.dumps({"call_type": "other"}), json.dumps([1, 2])])
def test_parse_outbound_metadata_rejects_non_outbound_payloads(raw):
    assert agent._parse_outbound_metadata(raw) is None


def test_assistant_uses_outbound_context_for_greeting_selection():
    ctx = {"call_type": "outbound_reminder", "name": "Ramesh", "phone_number": "+919876543210"}
    assistant = Assistant(outbound_context=ctx)
    assert assistant._outbound_context == ctx


def test_assistant_inbound_has_no_outbound_context():
    assistant = Assistant()
    assert assistant._outbound_context is None


def test_scheme_name_resolves_id_and_partial_name():
    assert "Jan Dhan" in outbound_caller._scheme_name("pmjdy")
    assert "Sukanya" in outbound_caller._scheme_name("sukanya samriddhi")


def test_scheme_name_falls_back_to_input_when_unknown():
    assert outbound_caller._scheme_name("not-a-real-scheme") == "not-a-real-scheme"


@pytest.mark.parametrize(
    "message,expected",
    [
        ("call ended: busy", "busy"),
        ("SIP status: no-answer", "no_answer"),
        ("participant unanswered after ringing", "no_answer"),
        ("routed to voicemail", "voicemail"),
        ("rejected by carrier", "error"),
    ],
)
def test_classify_failure_from_error_message(message, expected):
    exc = Exception()
    exc.message = message
    assert outbound_caller._classify_failure(exc) == expected
