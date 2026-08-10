"""Unit tests for the local government-scheme eligibility/document lookup."""

import schemes


def test_eligible_scheme_for_new_adult_without_bank_account():
    result = schemes.check_eligibility(age=25, has_bank_account=False)
    ids = {s["id"] for s in result["eligible"]}
    assert "pmjdy" in ids
    assert result["data_as_of"] == schemes.DATA_AS_OF


def test_insurance_schemes_require_bank_account():
    result = schemes.check_eligibility(age=25, has_bank_account=False)
    close_ids = {s["id"]: s["reason_not_eligible"] for s in result["close_but_not_eligible"]}
    assert "pmsby" in close_ids
    assert "bank account" in close_ids["pmsby"]


def test_ssy_only_for_young_girls():
    result = schemes.check_eligibility(age=5, gender="female")
    ids = {s["id"] for s in result["eligible"]}
    assert "ssy" in ids

    result_boy = schemes.check_eligibility(age=5, gender="male")
    ids_boy = {s["id"] for s in result_boy["eligible"]}
    assert "ssy" not in ids_boy


def test_apy_age_window():
    too_old = schemes.check_eligibility(age=45, has_bank_account=True)
    assert "apy" not in {s["id"] for s in too_old["eligible"]}

    in_range = schemes.check_eligibility(age=30, has_bank_account=True)
    assert "apy" in {s["id"] for s in in_range["eligible"]}


def test_occupation_gated_scheme():
    tailor = schemes.check_eligibility(age=30, occupation="tailor")
    assert "pm_vishwakarma" in {s["id"] for s in tailor["eligible"]}

    unrelated = schemes.check_eligibility(age=30, occupation="software engineer")
    assert "pm_vishwakarma" not in {s["id"] for s in unrelated["eligible"]}


def test_unspecified_answers_are_skipped_not_failed():
    # No answers given at all -> schemes with no hard requirements still show up.
    result = schemes.check_eligibility()
    ids = {s["id"] for s in result["eligible"]}
    assert "pmjdy" in ids


def test_get_documents_by_partial_name():
    doc = schemes.get_documents("Jan Dhan")
    assert doc is not None
    assert doc["id"] == "pmjdy"
    assert len(doc["documents"]) > 0
    assert doc["data_as_of"] == schemes.DATA_AS_OF


def test_get_documents_by_id():
    doc = schemes.get_documents("mudra")
    assert doc is not None
    assert doc["id"] == "mudra"


def test_get_documents_unknown_scheme_returns_none():
    assert schemes.get_documents("some scheme that does not exist") is None
