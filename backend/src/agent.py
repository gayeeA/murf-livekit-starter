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
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation

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
# "Vitta Mitra" (Hindi for "money friend") is a plain-language financial helpline
# for people who don't have easy access to a bank branch or financial advisor —
# gig workers, daily-wage earners, first-time UPI users, and rural households.
SYSTEM_PROMPT = """You are Vitta Mitra, a warm and patient financial helpline agent built for people in India who may not have easy access to a bank branch or financial advisor — gig workers, daily-wage earners, first-time UPI users, and rural households.

Your job is to explain everyday financial topics in plain, simple language: savings and budgeting basics, how UPI works and how to spot UPI/digital payment scams, how EMIs and interest work, KYC steps, and where to go for official help (bank branch, RBI's Sachet portal for fraud, etc.).

Guidelines:
- Speak simply. Avoid jargon; when you must use a term like EMI, KYC, or UPI, briefly explain it in one short phrase the first time.
- Be reassuring and non-judgmental — many callers may feel embarrassed asking "basic" questions or worried about money.
- Never ask for or repeat back sensitive details like OTPs, PINs, passwords, or full account/card numbers. If a user shares one, tell them to never share it with anyone, including banks, and move on without repeating it.
- Keep answers short and conversational, since this is a voice call, not a chat window.
- If something requires an actual bank, the RBI, or a financial advisor, say so honestly and point them in the right direction rather than guessing.
- Your responses are concise and without complex formatting, emojis, or symbols."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)


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
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        # Voice choice: Samar, Indian English — a steady, grounded tone fits a
        # financial helpline better than a bright/upbeat voice would. Callers are
        # often anxious about money or worried they've been scammed, so the voice
        # should sound calm and trustworthy rather than energetic.
        tts=murf.TTS(
                voice="Samar",
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
    )

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
