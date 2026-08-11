"""Unit tests for the SQLite-backed caller memory layer."""

import os

import pytest

import memory


@pytest.fixture()
def db(tmp_path):
    """Point the memory layer at a throwaway database per test."""
    old = memory._DB_PATH
    memory._DB_PATH = os.path.join(str(tmp_path), "test_memory.db")
    memory.init_db()
    yield memory
    memory._DB_PATH = old


def test_save_and_lookup_roundtrip(db):
    db.save_user(name="Ramesh", facts={"savings_plan": "started", "language": "telugu"})
    record = db.lookup_user("Ramesh")
    assert record is not None
    assert record["name"] == "Ramesh"
    assert record["facts"] == {"savings_plan": "started", "language": "telugu"}
    assert record["user_id"]
    assert record["last_interaction"]


def test_lookup_is_case_insensitive(db):
    db.save_user(name="Ramesh", facts={"topic": "savings"})
    assert db.lookup_user("ramesh") is not None
    assert db.lookup_user(" RAMESH ") is not None
    assert db.lookup_user("Suresh") is None


def test_merge_facts_on_second_save(db):
    db.save_user(name="Ramesh", facts={"topic": "savings"})
    db.save_user(name="Ramesh", facts={"checked_scheme": "ppf"})
    record = db.lookup_user("Ramesh")
    assert record["facts"] == {"topic": "savings", "checked_scheme": "ppf"}


def test_forget_user_by_name(db):
    db.save_user(name="Ramesh", facts={"topic": "savings"})
    assert db.forget_user_by_name("Ramesh") is True
    assert db.lookup_user("Ramesh") is None
    assert db.forget_user_by_name("Ramesh") is False


def test_forget_user_by_id(db):
    record = db.save_user(name="Ramesh", facts={"topic": "savings"})
    assert db.forget_user(record["user_id"]) is True
    assert db.lookup_user_by_id(record["user_id"]) is None


def test_sensitive_key_is_dropped(db):
    db.save_user(
        name="Ramesh",
        facts={
            "checked_scheme": "ppf",
            "aadhaar": "1234 5678 9012",
            "account_number": "9876543210",
        },
    )
    record = db.lookup_user("Ramesh")
    assert record["facts"] == {"checked_scheme": "ppf"}
    assert "aadhaar" not in record["facts"]
    assert "account_number" not in record["facts"]


def test_sensitive_value_is_dropped(db):
    db.save_user(
        name="Ramesh",
        facts={
            "note": "my number is 9876543210",
            "pan": "ABCDE1234F",
            "safe": "wants to learn about UPI",
        },
    )
    record = db.lookup_user("Ramesh")
    assert "note" not in record["facts"]
    assert "pan" not in record["facts"]
    assert record["facts"] == {"safe": "wants to learn about UPI"}


def test_long_numeric_value_is_dropped(db):
    db.save_user(name="Ramesh", facts={"phone_like": 9876543210, "age": 30})
    record = db.lookup_user("Ramesh")
    assert record["facts"] == {"age": 30}


def test_do_not_call_roundtrip(db):
    assert db.is_do_not_call("+919876543210") is False
    db.add_do_not_call("+919876543210")
    assert db.is_do_not_call("+919876543210") is True
    # Unrelated numbers are unaffected.
    assert db.is_do_not_call("+911234567890") is False


def test_do_not_call_is_idempotent(db):
    db.add_do_not_call("+919876543210")
    db.add_do_not_call("+919876543210")
    assert db.is_do_not_call("+919876543210") is True
