"""Day 6 — outbound reminder calls for Pooja.

Places an outbound phone call through a LiveKit SIP outbound trunk (backed
by a telephony provider such as Twilio, or Linphone as a free fallback — see
backend/README.md "Day 6 — Outbound calling" for setup) so Pooja can remind
someone who was already found eligible for a government scheme
(``schemes.check_eligibility``) that its enrollment window is closing soon.

Usage:
    uv run python src/outbound_caller.py \\
        --name "Ramesh" --phone "+919876543210" \\
        --scheme pmjdy --deadline "31 August"

This dispatches the "my-agent" job into a fresh room with the call's
context as job metadata, then dials the phone number into that same room
via the SIP outbound trunk in ``SIP_OUTBOUND_TRUNK_ID``. ``agent.py`` reads
that metadata and opens the call with the required who/why/opt-out framing
instead of the normal inbound greeting.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import uuid
from datetime import timedelta

from dotenv import load_dotenv
from livekit import api

from memory import init_db, is_do_not_call
from schemes import SCHEMES

load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbound_caller")

AGENT_NAME = "my-agent"
MAX_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 45

# Outcome handling (Day 6 advanced): no-answer and busy are worth exactly
# one retry after a short delay, since the callee may simply not have been
# reachable yet. A hard rejection/error is not retried.
RETRYABLE_OUTCOMES = {"no_answer", "busy"}


def _scheme_name(scheme_id_or_name: str) -> str:
    """Resolve a scheme id or partial name to its full display name."""
    query = scheme_id_or_name.strip().lower()
    for scheme in SCHEMES:
        if query == scheme["id"] or query in scheme["name"].lower():
            return scheme["name"]
    return scheme_id_or_name


def _classify_failure(exc: api.TwirpError) -> str:
    """Map a SIP dial failure to a coarse outcome: no_answer / busy / voicemail / error.

    LiveKit's SIP integration surfaces the callee's disposition (unanswered,
    busy, rejected, etc.) in the Twirp error message when
    ``wait_until_answered`` times out or the call can't be completed. This
    is a best-effort keyword match over that message, not a stable API
    contract — treat outcome classification as advisory.
    """
    reason = (exc.message or "").lower()
    if "voicemail" in reason or "answering machine" in reason:
        return "voicemail"
    if "busy" in reason:
        return "busy"
    if "no-answer" in reason or "unanswered" in reason or "timeout" in reason or "ringing" in reason:
        return "no_answer"
    return "error"


async def _place_call(
    lk: api.LiveKitAPI,
    *,
    phone_number: str,
    name: str,
    scheme_name: str,
    deadline: str,
    trunk_id: str,
) -> str:
    """Dispatch the agent and dial the callee into a fresh room.

    Returns one of: "answered", "no_answer", "busy", "voicemail", "error".
    """
    room_name = f"outbound-{uuid.uuid4().hex[:10]}"
    metadata = json.dumps(
        {
            "call_type": "outbound_reminder",
            "name": name,
            "scheme_name": scheme_name,
            "deadline": deadline,
            "phone_number": phone_number,
        }
    )

    # Explicitly dispatch the agent into this room before dialing, so it's
    # already there listening when the callee picks up.
    await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=AGENT_NAME, room=room_name, metadata=metadata
        )
    )

    try:
        participant = await lk.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=f"caller-{phone_number}",
                participant_name=name,
                wait_until_answered=True,
                ringing_timeout=timedelta(seconds=25),
                max_call_duration=timedelta(seconds=600),
            )
        )
        logger.info(
            "Call answered: room=%s participant=%s",
            room_name,
            participant.participant_identity,
        )
        return "answered"
    except api.TwirpError as exc:
        outcome = _classify_failure(exc)
        logger.warning(
            "Call to %s did not connect (outcome=%s): %s",
            phone_number,
            outcome,
            exc.message,
        )
        return outcome


async def place_reminder_call(
    *, name: str, phone: str, scheme: str, deadline: str
) -> str:
    """Run the full outbound flow: do-not-call check, dial, retry. Returns the final outcome."""
    init_db()
    if is_do_not_call(phone):
        logger.info("%s is on the do-not-call list; skipping.", phone)
        return "skipped_do_not_call"

    trunk_id = os.environ["SIP_OUTBOUND_TRUNK_ID"]
    scheme_name = _scheme_name(scheme)

    outcome = "error"
    async with api.LiveKitAPI() as lk:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            logger.info("Attempt %d/%d: calling %s", attempt, MAX_ATTEMPTS, phone)
            outcome = await _place_call(
                lk,
                phone_number=phone,
                name=name,
                scheme_name=scheme_name,
                deadline=deadline,
                trunk_id=trunk_id,
            )
            if outcome not in RETRYABLE_OUTCOMES or attempt == MAX_ATTEMPTS:
                break
            logger.info("Retrying in %ds...", RETRY_DELAY_SECONDS)
            await asyncio.sleep(RETRY_DELAY_SECONDS)

    logger.info("Final outcome for %s: %s", phone, outcome)
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser(description="Place a Pooja outbound scheme-deadline reminder call.")
    parser.add_argument("--name", required=True, help="Caller's name")
    parser.add_argument("--phone", required=True, help="E.164 phone number, e.g. +919876543210")
    parser.add_argument("--scheme", required=True, help="Scheme id or name, e.g. pmjdy")
    parser.add_argument("--deadline", required=True, help="Deadline to mention, e.g. '31 August'")
    args = parser.parse_args()

    asyncio.run(
        place_reminder_call(
            name=args.name, phone=args.phone, scheme=args.scheme, deadline=args.deadline
        )
    )


if __name__ == "__main__":
    main()
