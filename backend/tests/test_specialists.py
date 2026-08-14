"""Unit tests for the Day 9 main-agent <-> scheme-specialist handoff.

These call the function_tool-decorated methods directly (they remain plain
coroutine methods) rather than going through an LLM, so they run offline
with no model/API keys needed.
"""

import pytest

from agent import Assistant
from specialists import SchemeSpecialistAgent


@pytest.mark.asyncio
async def test_transfer_returns_specialist_agent_with_shared_state():
    call_state = {"signals": []}
    assistant = Assistant(call_state=call_state)

    result = await assistant.transfer_to_scheme_specialist(None)

    assert isinstance(result, tuple)
    message, specialist = result
    assert isinstance(message, str) and message
    assert isinstance(specialist, SchemeSpecialistAgent)
    # The same call_state object is shared, so a success signal recorded by
    # either agent counts toward the same call (Day 8 analytics).
    assert specialist._call_state is call_state


@pytest.mark.asyncio
async def test_transfer_carries_outbound_context():
    outbound_ctx = {"call_type": "outbound_reminder", "phone_number": "+919876543210"}
    assistant = Assistant(outbound_context=outbound_ctx)

    _, specialist = await assistant.transfer_to_scheme_specialist(None)

    assert specialist._outbound_context == outbound_ctx


@pytest.mark.asyncio
async def test_transfer_handles_construction_failure_gracefully(monkeypatch):
    assistant = Assistant()

    def _boom(*args, **kwargs):
        raise RuntimeError("specialist unavailable")

    monkeypatch.setattr("agent.SchemeSpecialistAgent", _boom)

    result = await assistant.transfer_to_scheme_specialist(None)
    assert result == "HANDOFF_FAILED"


@pytest.mark.asyncio
async def test_specialist_eligibility_check_marks_shared_call_state_success():
    call_state = {"signals": []}
    specialist = SchemeSpecialistAgent(call_state=call_state)

    result = await specialist.check_scheme_eligibility(None, age=25, has_bank_account=False)

    assert "eligible" in result
    assert "eligibility_check_completed" in call_state["signals"]


@pytest.mark.asyncio
async def test_specialist_documents_lookup_marks_shared_call_state_success():
    call_state = {"signals": []}
    specialist = SchemeSpecialistAgent(call_state=call_state)

    result = await specialist.get_scheme_documents(None, scheme_name="pmjdy")

    assert result["id"] == "pmjdy"
    assert "documents_delivered" in call_state["signals"]


@pytest.mark.asyncio
async def test_return_to_pooja_hands_back_with_shared_state_and_context():
    call_state = {"signals": ["eligibility_check_completed"]}
    outbound_ctx = {"call_type": "outbound_reminder"}
    specialist = SchemeSpecialistAgent(call_state=call_state, outbound_context=outbound_ctx)

    result = await specialist.return_to_pooja(None)

    assert isinstance(result, tuple)
    message, main_agent = result
    assert isinstance(message, str) and message
    assert isinstance(main_agent, Assistant)
    assert main_agent._call_state is call_state
    assert main_agent._outbound_context == outbound_ctx
