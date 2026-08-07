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
    cli,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero

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
- Greet once at the start: introduce yourself, say you are the money friend, and invite them to ask about savings, UPI, scams, EMIs, or KYC."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    async def on_enter(self) -> None:
        """Deliver a warm first-turn greeting when the agent joins the call."""
        await self.session.say(
            "నమస్తే! నేను పూజ. మీ డబ్బు స్నేహితుడిని. "
            "సేవింగ్స్ గురించి, UPI గురించి, మోసాల గురించి, EMI గురించి, "
            "లేదా KYC గురించి ఏదైనా అడగండి. "
            "Namaste! I'm Pooja, your money friend. "
            "Ask me anything about savings, UPI, scams, EMIs, or KYC."
        )


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

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


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
        agent=Assistant(),
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
