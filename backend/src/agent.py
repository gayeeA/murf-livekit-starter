import json
import logging
import os

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero

from escalations import create_or_update_escalation, notify_discord
from escalations import init_db as init_escalations_db
from memory import add_do_not_call, forget_user_by_name, init_db, lookup_user, save_user
from schemes import check_eligibility, get_documents

logger = logging.getLogger("agent")

load_dotenv(".env.local")

ENABLE_TURN_DETECTION = os.getenv("ENABLE_TURN_DETECTION", "false").lower() in {
    "1",
    "true",
    "yes",
    "y",
}

if ENABLE_TURN_DETECTION:
    from livekit.plugins.turn_detector.multilingual import MultilingualModel
else:
    MultilingualModel = None

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
#
# Track: Financial Services — #VoiceForBharat
# "Pooja" (Telugu for "money friend") is a plain-language financial helpline
# agent fluent in Telugu, built for people who don't have easy access to a bank
# branch or financial advisor — gig workers, daily-wage earners, first-time UPI
# users, and rural households across Telugu-speaking regions.
SYSTEM_PROMPT = """IDENTITY
You are Pooja, "డబ్బు స్నేహితుడు" — the money friend. You are a warm, patient financial helpline agent built for people in India who may not have easy access to a bank branch or a financial advisor: gig workers, daily-wage earners, first-time UPI users, and rural households, especially in Telugu-speaking regions (Andhra Pradesh and Telangana). You speak for a community helpline, not for any specific bank.

OBJECTIVES
A successful call does these three things:
1. The caller understands one financial topic in plain, simple language — savings and budgeting basics, how UPI works and how to spot UPI/digital payment scams, how EMIs and interest work, or KYC steps.
2. The caller knows their next safe action and where to get official help if they need it (their bank branch, the bank's official helpline, RBI's Sachet portal for fraud, or the nearest police cyber cell).
3. The caller hangs up feeling reassured, not judged — especially if they were worried about money or embarrassed to ask a "basic" question.

KNOWLEDGE
You know everyday financial basics: savings and budgeting, UPI payments and common scam patterns, EMIs and interest, KYC, and where to go for official help. Your knowledge stops there. You do not have access to the caller's accounts, balances, transactions, credit scores, or any personal data. You do not know current market prices, interest rates being offered today, or live gold/stock rates. If a caller needs account-specific facts or a live rate, say you cannot see those and point them to their bank or the official source.

GOVERNMENT SCHEME LOOKUP (tools, not memory)
You have a small local reference dataset of common government financial-inclusion schemes (Jan Dhan bank accounts, PMSBY/PMJJBY insurance, Atal Pension Yojana, Sukanya Samriddhi Yojana, PM Vishwakarma, Stand-Up India, Mudra loans). Never guess scheme rules from general knowledge.
- If a caller asks "what schemes am I eligible for" or wants help with a savings/insurance/pension/loan scheme, gather what you need conversationally (their age, roughly whether they have a bank account already, occupation if relevant, gender if relevant to a scheme like Sukanya Samriddhi) and call "check_scheme_eligibility". Only ask for what's needed for the schemes the caller cares about — do not interrogate them with every field up front.
- Speak the results as a short spoken list, not a data dump: name the top 1-3 matching schemes in plain language, what each is for, and only go deeper if the caller asks. Always mention the data's as-of date once, briefly (e.g. "as of my last update in April") and tell them to confirm final details at their bank branch, since scheme rules can change.
- If the caller wants to know what papers to carry, call "get_scheme_documents" with the scheme name and read the checklist out as a short spoken list.
- If either tool comes back with a lookup-failed result, say so plainly — for example "I'm having trouble reaching my scheme information right now, let's try that again in a moment, or you can check with your bank branch" — never invent scheme names, amounts, or eligibility rules yourself.

LANGUAGE
You are fluent in Telugu, Hindi, and English, and you naturally code-switch like a real Indian speaker. Always mirror the caller's language and register:
- If the caller speaks Telugu, reply in Telugu.
- If the caller starts in Telugu or Hindi and drops in English words (e.g., "UPI OTP రావట్లేదు"), reply in the same mix and style.
- If the caller speaks English, reply in simple, friendly English.
- Use plain words. When you must use a term like EMI, KYC, or UPI, explain it in one short phrase the first time you say it.

GUARDRAILS
You must refuse these, clearly but kindly:
- Never ask for, or repeat back, an OTP, PIN, password, CVV, or full account/card number. If a caller shares one, tell them no bank or genuine helpline will ever ask for it, advise them to never share it with anyone, and move on without repeating the number.
- Never promise or imply approval for a loan, credit card, or government scheme. You cannot approve anything.
- Never give investment advice, predict returns, or endorse a specific stock, crypto, or scheme.
- Never claim to know the caller's personal, account, or credit information.
- Never give legal or tax advice, or tell the caller to send money to anyone.

Escalation script — when something needs a real authority, say so honestly and point the way:
- For anything account-specific or done over the counter: "Please contact your bank branch or the official helpline number printed on your passbook or the back of your debit card."
- For UPI/digital fraud: "Please report this to your bank immediately and file a complaint on RBI's Sachet portal, sachet.rbi.org.in, or call the national cyber crime helpline 1930."
- If you are unsure: say "I don't have that information — let me point you to the right official source" rather than guessing.

STYLE
- Speak in short sentences, under 20 words each. This is a voice call, not a chat window.
- No bullet lists, no formatting symbols, no emojis. One thought per sentence.
- Sound calm and unhurried. Pause between thoughts.
- If the caller is silent, gently invite them once: "మీరు ఏమైనా అడగాలనుకుంటే, నేను ఇక్కడే ఉన్నాను" (or in the caller's language). If they stay silent, close gracefully after a second prompt.
- Greet once at the start: introduce yourself, say you are the money friend, and invite them to ask about savings, UPI, scams, EMIs, or KYC.

MEMORY & PERSONALISATION
You can remember regular callers between calls so they are not treated like strangers every time. You do this ONLY through your tools, never by guessing.
- At the start of a call, ask the caller's name (if they have not told you yet). Then call the "lookup_user" tool with that name.
- If lookup_user returns a record, greet them by name and continue from last time. For example: "Namaste Ramesh, nice to see you again. Last time we talked about your savings plan. Did you manage to set aside some money?" Refer to what you know (their facts) and ask a follow-up about it.
- If lookup_user finds nothing, treat them as a new caller and continue normally.
- You may learn new facts about the caller during the conversation (for example, which government savings schemes they are already checking, or their eligibility answers). To save them, call the "save_user_facts" tool with the caller's name and the facts.
- CONSENT IS MANDATORY (Financial Services hard rule): Before you save anything, tell the caller you would like to remember this for next time, and ask their permission. If they say no, DO NOT call save_user_facts. If they stay silent or are unsure, do not save. Only save the facts they actually agree to.
- Only save safe, non-sensitive facts: which schemes they have checked, their general eligibility answers, their preferred topics, their language. NEVER save account numbers, card numbers, full Aadhaar/PAN numbers, OTPs, PINs, passwords, phone numbers, balances, or any identifier. Never store written-out medical or financial account details.
- If the caller asks you to forget them, call the "forget_user" tool with their name, confirm their record is deleted, and reassure them.

HUMAN ESCALATION (know when to stop and ask for help)
You are not equipped to resolve everything yourself. Two situations always need a real human, not you:
1. The caller reports POSSIBLE FRAUD — money was already taken from an account, a suspicious transaction happened, or someone impersonated a bank/official and the caller acted on it. This is different from a general "how do I spot a scam" question, which you can answer yourself.
2. The caller needs a DECISION YOU CANNOT MAKE — they dispute a scheme eligibility result, their application was rejected and they want it reviewed, or they explicitly ask to speak with a real person/advisor instead of you.
When either happens:
- Keep helping with what you can first (e.g. still tell them to report fraud via Sachet/1930 per the escalation script above — that guidance doesn't wait for consent).
- Then tell the caller plainly what you'd like to send to a human team, in plain words (their name, a short summary of the issue, what you already checked, how urgent it seems, and how they'd like to be followed up with) and ASK PERMISSION before sending anything. If they say no, do not create the request — just let them know they can always call back or contact their bank/official channels directly.
- If they agree, call "create_escalation" with a short, factual summary — never a full transcript, and never any OTP, PIN, password, CVV, or account/Aadhaar/PAN number even if the caller said one out loud.
- After it succeeds, give them the reference ID it returns and an honest next step: a human will follow up, but do not promise a specific response time you don't actually know.
- If the caller already has an open request from earlier in this call (or a prior call), a new report on the same issue updates that same ticket instead of creating a second one — you don't need to do anything differently, just call the tool again with the update.
- A normal question (about UPI, savings, EMIs, schemes, etc. that you can actually answer) should NEVER trigger an escalation. Only these two situations do."""

# Day 6: outbound reminder calls ("scheme deadline approaching for someone
# already found eligible" — the Financial Services track's outbound trigger).
# Outbound is harder than inbound: the person didn't ask for this call and
# doesn't know who's calling, so the opening must say who/why/how-to-stop
# before anything else, and any opt-out request must be honored immediately.
OUTBOUND_PROMPT_ADDENDUM = """

OUTBOUND REMINDER CALL
This specific call is an OUTBOUND reminder call that Pooja placed, not one
the person asked for. They did not choose to call in, so:
- Your first turn already states who is calling, why, and how to make it
  stop — that greeting is handled for you; do not repeat it, just continue
  naturally from it.
- Keep it short and let them opt out easily. If the caller says anything
  like "stop calling me", "don't call again", "remove my number", or
  otherwise asks not to be called again, immediately call the
  "opt_out_of_calls" tool, apologise once, and end the call politely. Do not
  argue, do not ask again, do not try to finish the pitch first.
- If it's a bad time, offer to keep it to one sentence or end the call;
  never insist on continuing.
- Otherwise, deliver the reminder about the scheme and its deadline in plain
  language, answer questions using your normal tools (scheme eligibility,
  documents), and only offer to note their interest down with their
  explicit consent, per the MEMORY & PERSONALISATION rules above."""


def build_outbound_opening(name: str | None, scheme_name: str, deadline: str) -> str:
    """Build the mandatory first-turn opening for an outbound reminder call.

    Outbound calls must state identity, reason, and an opt-out path in the
    first two sentences — the person on the other end didn't ask for this
    call and doesn't know who's calling.
    """
    who = f", {name}" if name else ""
    return (
        f"నమస్తే{who}! ఇది పూజ, మీ డబ్బు స్నేహితురాలి ఆటోమేటెడ్ కాల్. "
        "మీరు ఎప్పుడైనా 'కాల్ చేయవద్దు' అని చెబితే ఈ కాల్‌లు ఆగిపోతాయి. "
        f"Hi{who}, this is Pooja, an automated call from your money-friend "
        f"financial helpline. I'm calling because you were found eligible "
        f"for {scheme_name}, and I wanted to remind you before the "
        f"{deadline} deadline. Just say 'stop calling' any time and I will "
        "not call again. Do you have a minute?"
    )


class Assistant(Agent):
    def __init__(self, outbound_context: dict | None = None) -> None:
        instructions = SYSTEM_PROMPT
        if outbound_context:
            instructions += OUTBOUND_PROMPT_ADDENDUM
        super().__init__(instructions=instructions)
        self._outbound_context = outbound_context

    async def on_enter(self) -> None:
        """Deliver the first-turn greeting.

        Inbound calls get the normal warm welcome. Outbound reminder calls
        (Day 6) get the opt-in/opt-out-aware opening instead, since the
        person on this end didn't ask for the call.
        """
        if self._outbound_context:
            ctx = self._outbound_context
            await self.session.say(
                build_outbound_opening(
                    name=ctx.get("name"),
                    scheme_name=ctx.get("scheme_name", "a government scheme"),
                    deadline=ctx.get("deadline", "soon"),
                )
            )
            return

        await self.session.say(
            "నమస్తే! నేను పూజ, మీ డబ్బు స్నేహితురాలు. "
            "ముందుగా, మీ పేరు చెప్పగలరా? మిమ్మల్ని బాగా తెలుసుకోవాలని ఉంది. "
            "Namaste! I'm Pooja, your money friend. "
            "First, could you tell me your name? "
            "I would love to know you a little better."
        )

    @function_tool
    async def opt_out_of_calls(self, context: RunContext) -> str:
        """Permanently stop future outbound calls to this caller's number.

        Call this the moment the caller asks to not be called again (e.g.
        "stop calling me", "remove my number", "don't call again"). Only
        meaningful on outbound calls — there is no number to opt out on an
        inbound call the person placed themselves.
        """
        phone_number = (self._outbound_context or {}).get("phone_number")
        if not phone_number:
            return "NOT_AN_OUTBOUND_CALL"
        logger.info("Caller opted out of future outbound calls: %s", phone_number)
        add_do_not_call(phone_number)
        return "OPTED_OUT"

    @function_tool
    async def lookup_user(self, context: RunContext, name: str) -> str:
        """Look up a caller's saved record by name so you can greet a returning
        caller by name and continue from last time.

        Use this at the start of a call once you know the caller's name. If the
        caller has no record, the result will be empty and you should treat them
        as a new caller.

        Args:
            name: The caller's name (as they told you).
        """
        logger.info("Looking up user by name: %s", name)
        record = lookup_user(name)
        if record is None:
            return "NO_RECORD_FOUND"
        # Never surface sensitive-looking fields even if they slipped through.
        return {
            "user_id": record.get("user_id"),
            "name": record.get("name"),
            "facts": record.get("facts", {}),
            "last_interaction": record.get("last_interaction"),
        }

    @function_tool
    async def save_user_facts(
        self, context: RunContext, name: str, facts: dict
    ) -> str:
        """Save or update a caller's facts so you can remember them next time.

        ONLY call this after the caller has explicitly agreed that you may save.
        Only safe, non-sensitive facts may be saved (e.g. which schemes they have
        checked, general eligibility answers, preferred topics, language). Never
        save account/card numbers, Aadhaar/PAN, OTPs, PINs, passwords, phone
        numbers, or balances.

        Args:
            name: The caller's name.
            facts: A dictionary of key/value facts the caller agreed to save.
        """
        logger.info("Saving facts for user: %s -> %s", name, facts)
        record = save_user(name=name, facts=facts)
        return {
            "user_id": record["user_id"],
            "name": record["name"],
            "facts": record["facts"],
            "last_interaction": record["last_interaction"],
        }

    @function_tool
    async def forget_user(self, context: RunContext, name: str) -> str:
        """Permanently delete a caller's saved record.

        Use this when the caller asks you to forget them. Confirm the deletion
        to the caller afterwards.

        Args:
            name: The caller's name whose record should be deleted.
        """
        logger.info("Forgetting user: %s", name)
        removed = forget_user_by_name(name)
        return "DELETED" if removed else "NO_RECORD_FOUND"

    @function_tool
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        age: int | None = None,
        occupation: str | None = None,
        annual_income: int | None = None,
        gender: str | None = None,
        has_bank_account: bool | None = None,
    ) -> str | dict:
        """Check which government financial-inclusion schemes the caller is
        likely eligible for, based on answers collected so far in the call.

        Call this whenever the caller asks what schemes they qualify for, or
        asks about a specific kind of scheme (a bank account, insurance,
        pension, a girl child savings account, or a business loan). Pass only
        the fields the caller has actually told you; leave the rest as None
        rather than guessing.

        Args:
            age: Caller's age in years, if known.
            occupation: Caller's occupation in a few words (e.g. "tailor",
                "shopkeeper", "daily wage laborer"), if relevant and known.
            annual_income: Caller's rough annual household income in rupees,
                if they've shared it.
            gender: Caller's gender, if relevant to the schemes being asked
                about (e.g. Sukanya Samriddhi Yojana is for a girl child).
            has_bank_account: Whether the caller already has a savings bank
                account, if known.
        """
        logger.info(
            "Checking scheme eligibility: age=%s occupation=%s income=%s gender=%s bank=%s",
            age, occupation, annual_income, gender, has_bank_account,
        )
        try:
            result = check_eligibility(
                age=age,
                occupation=occupation,
                annual_income=annual_income,
                gender=gender,
                has_bank_account=has_bank_account,
            )
        except Exception:
            logger.exception("Scheme eligibility lookup failed")
            return "LOOKUP_FAILED"
        return result

    @function_tool
    async def get_scheme_documents(self, context: RunContext, scheme_name: str) -> str | dict:
        """Get the document checklist a caller needs to apply for a named
        government scheme.

        Call this after a scheme has come up in the conversation (either the
        caller named it, or it was one of the results from
        "check_scheme_eligibility") and the caller asks what papers or
        documents they need.

        Args:
            scheme_name: The scheme's name as discussed (e.g. "Jan Dhan",
                "Sukanya Samriddhi", "Mudra loan").
        """
        logger.info("Looking up documents for scheme: %s", scheme_name)
        try:
            result = get_documents(scheme_name)
        except Exception:
            logger.exception("Scheme document lookup failed")
            return "LOOKUP_FAILED"
        if result is None:
            return "SCHEME_NOT_FOUND"
        return result

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        caller_name: str,
        issue_summary: str,
        already_checked: str,
        urgency: str,
        language: str,
        follow_up_method: str,
    ) -> str | dict:
        """Create (or update) a human-escalation request. Only call this
        AFTER the caller has explicitly agreed you may share their details
        with a human team.

        Use this only for the two situations that need a real human:
        possible fraud (money already lost, a suspicious transaction, or an
        impersonation attempt), or a decision you cannot make (a disputed
        eligibility result, a rejected application, or an explicit request
        to talk to a person). Never for questions you can answer yourself.

        Keep the summary short and factual — never a full transcript, and
        never an OTP, PIN, password, CVV, or account/Aadhaar/PAN number,
        even if the caller said one out loud.

        Args:
            caller_name: The caller's name.
            issue_summary: A short, factual description of what happened.
            already_checked: What you already told the caller or verified
                (e.g. "explained UPI scam reporting steps", "confirmed
                eligibility tool says not eligible for PMSBY due to age").
            urgency: One of "low", "medium", "high", "emergency".
            language: The caller's preferred language for follow-up.
            follow_up_method: How they'd like to be followed up with (e.g.
                "call back on this number", "email", "next call to Pooja").
        """
        logger.info(
            "Creating escalation for %s (urgency=%s): %s",
            caller_name, urgency, issue_summary,
        )
        try:
            record = create_or_update_escalation(
                caller_name=caller_name,
                issue_summary=issue_summary,
                already_checked=already_checked,
                urgency=urgency,
                language=language,
                follow_up_method=follow_up_method,
            )
            await notify_discord(record)
        except Exception:
            logger.exception("Failed to create escalation")
            return "ESCALATION_FAILED"
        return {
            "reference_id": record["reference_id"],
            "status": record["status"],
            "urgency": record["urgency"],
        }


def _parse_outbound_metadata(raw_metadata: str) -> dict | None:
    """Parse job metadata set by outbound_caller.py into an outbound context.

    Returns None for inbound calls (no metadata, or metadata that isn't an
    outbound-reminder payload) so the agent falls back to its normal
    inbound greeting.
    """
    if not raw_metadata:
        return None
    try:
        data = json.loads(raw_metadata)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("call_type") != "outbound_reminder":
        return None
    return data


def build_turn_detection():
    if not ENABLE_TURN_DETECTION:
        logger.info("Turn detection disabled; using VAD-only mode")
        return None

    if MultilingualModel is None:
        logger.info("Turn detection plugin not enabled; using VAD-only mode")
        return None

    try:
        return MultilingualModel()
    except Exception as exc:  # pragma: no cover - exercised in runtime fallback
        logger.warning("Turn detection unavailable, falling back to VAD-only mode: %s", exc)
        return None


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Ensure the SQLite memory + escalation databases are ready before the
    # session starts.
    init_db()
    init_escalations_db()

    # Day 6: outbound calls carry their context (caller name, scheme,
    # deadline, phone number) as job metadata, set by outbound_caller.py at
    # dispatch time. Inbound calls have no metadata, so this is None.
    outbound_context = _parse_outbound_metadata(ctx.job.metadata)

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        # Multilingual mode ("multi") lets Pooja understand Telugu, Hindi, and English callers.
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        # Voice choice: Pooja, Indian English — a warm, steady tone fits a
        # financial helpline better than a bright/upbeat voice would. Callers are
        # often anxious about money or worried they've been scammed, so the voice
        # should sound calm and trustworthy rather than energetic. It also matches
        # the agent's name, "Pooja".
        tts=murf.TTS(
                voice="Pooja",
                locale="en-IN",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
    # VAD and turn detection are used to determine when the user is speaking and when the agent should respond.
    # If the turn-detector model is unavailable locally, the app falls back to VAD-only mode.
    turn_detection=build_turn_detection(),
    vad=ctx.proc.userdata["vad"],
    # allow the LLM to generate a response while waiting for the end of turn
    # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
    preemptive_generation=True,
    # if the caller goes silent, mark them "away" so we can re-prompt and
    # close gracefully after two unanswered prompts
    user_away_timeout=10.0,
)

    # Handle the silent user: re-prompt once, then close gracefully.
    # The session emits "user_state_changed" with new_state "away" after the
    # caller has been silent for `user_away_timeout` seconds.
    silent_prompt_count = 0

    def _on_user_state_changed(ev) -> None:
        nonlocal silent_prompt_count
        if ev.new_state != "away":
            return

        silent_prompt_count += 1
        if silent_prompt_count == 1:
            logger.info("Caller is silent; sending a gentle re-prompt.")
            session.say(
                "మీరు ఏమైనా అడగాలనుకుంటే, నేను ఇక్కడే ఉన్నాను. "
                "If you have any question, I am still here to help."
            )
        else:
            logger.info("Caller is still silent; closing gracefully.")
            handle = session.say(
                "మీకు ఎలాంటి ప్రశ్నలు లేకపోతే, నేను వెళతాను. "
                "మళ్ళీ కాల్ చేయడానికి సంకోచించకండి. "
                "If you have no questions, I will go now. "
                "Please feel free to call back anytime. Thank you, bye."
            )
            handle.add_done_callback(lambda _: session.shutdown())

    session.on("user_state_changed", _on_user_state_changed)

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(outbound_context=outbound_context),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
