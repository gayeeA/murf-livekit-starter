# Backend — Voice Agent with Murf Falcon TTS

The Python backend for the Voice Agent Starter. It runs a real-time voice AI pipeline using [LiveKit Agents](https://docs.livekit.io/agents), connecting Murf Falcon TTS, Deepgram STT, and Google Gemini into a single conversational agent.

## How It Works

```
User speaks → [Deepgram STT] → text → [Gemini LLM] → response → [Murf Falcon TTS] → audio → User hears
```

LiveKit handles the real-time audio transport. The agent connects to LiveKit as a participant, listens for user speech, and responds with synthesized audio.

## Setup

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env.local
```

Fill in your keys in `.env.local`:

| Variable             | Where to get it                                           |
| -------------------- | --------------------------------------------------------- |
| `LIVEKIT_URL`        | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `LIVEKIT_API_KEY`    | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `LIVEKIT_API_SECRET` | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `MURF_API_KEY`       | [murf.ai/api/dashboard](https://murf.ai/api/dashboard)    |
| `DEEPGRAM_API_KEY`   | [deepgram.com](https://console.deepgram.com/)             |
| `GOOGLE_API_KEY`     | [aistudio.google.com](https://aistudio.google.com/apikey) |

For LiveKit Cloud users, you can auto-populate LiveKit credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### 3. Download models

```bash
uv run python src/agent.py download-files
```

This downloads Silero VAD and the LiveKit turn detector models.

### 4. Run the agent

```bash
# Development mode (auto-reload)
uv run python src/agent.py dev

# Or test directly in your terminal (no frontend needed)
uv run python src/agent.py console

# Production
uv run python src/agent.py start
```

## Configuration

All configuration lives in [`src/agent.py`](src/agent.py).

### System prompt

The `SYSTEM_PROMPT` constant at the top of `agent.py` controls what your agent does. Change it to build any voice-powered use case.

#### Example prompts

**Customer Support (default):**

```
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

**Interview Coach:**

```
You are an experienced interview coach. Conduct mock interviews with the user for software engineering roles. Ask one behavioral or technical question at a time, let the user answer fully, then give specific feedback on their response — what was strong, what could improve, and a suggested reframe. Keep the tone encouraging but honest.
```

**Sales Assistant:**

```
You are a knowledgeable sales assistant for an electronics store. Help customers find the right product by asking about their needs, budget, and preferences. Compare options clearly, highlight trade-offs, and make a recommendation. Never be pushy — focus on helping the customer make the best decision for them.
```

**Fitness Coach:**

```
You are an upbeat personal fitness coach. Help users plan workouts, suggest exercises for specific muscle groups, and answer questions about form and technique. Ask about their fitness level and any injuries before recommending exercises. Keep instructions clear and motivating.
```

**Storyteller / Bedtime Narrator:**

```
You are a creative storyteller who tells original bedtime stories for children aged 4–8. Ask the child (or parent) for a character name, a favorite animal, and a setting, then weave a short, calming story. Use vivid but simple language. End each story on a peaceful, sleepy note.
```

**Meeting Summarizer:**

```
You are a meeting assistant. The user will describe what happened in a meeting or read you their notes. Summarize the key decisions, action items (with owners if mentioned), and any open questions. Be concise and structured. Ask clarifying questions if something is ambiguous.
```

**Trivia Game Host:**

```
You are an enthusiastic trivia game host. Ask the user one trivia question at a time from a mix of categories — science, history, pop culture, geography, and sports. Wait for their answer, tell them if they're right or wrong, give a brief fun fact, then move to the next question. Keep score and announce it every 5 questions.
```

**Mental Health Check-in Companion:**

```
You are a gentle, non-clinical wellness companion. Help users talk through their day, reflect on how they're feeling, and practice simple grounding exercises like deep breathing or gratitude lists. You are not a therapist — if the user expresses serious distress or mentions self-harm, gently encourage them to reach out to a professional or crisis helpline.
```

### Voice

Set the `voice` argument in the `murf.TTS(...)` call:

```python
tts=murf.TTS(
    voice="en-US-matthew",    # Change this
    style="Conversation",
    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
    text_pacing=True
)
```

Some voice options:

| Voice ID | Description                      |
| -------- | -------------------------------- |
| `Anisha` | Indian English, female (default) |
| `Pooja`  | Indian English, female           |
| `Samar`  | Indian English, male             |
| `Amara`  | US English, female               |
| `Hazel`  | UK English, female               |
| `Bertie` | UK English, male                 |
| `Gordon` | US English, male                 |

Browse all 150+ voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT (Speech-to-Text)

Default is Deepgram Nova-3. Change in the `AgentSession(stt=...)` call:

```python
stt=deepgram.STT(model="nova-3")
```

### LLM

Default is Google Gemini. To switch:

- **Gemini (default):** Set `GOOGLE_API_KEY` in `.env.local`
- **OpenAI:** Set `OPENAI_API_KEY`, install `livekit-agents[openai]`, and change the `llm=` argument

## Tools — government scheme lookup (Day 5)

Pooja can look up common government financial-inclusion schemes (Jan Dhan bank accounts, PMSBY/PMJJBY insurance, Atal Pension Yojana, Sukanya Samriddhi Yojana, PM Vishwakarma, Stand-Up India, Mudra loans) via two `function_tool`s in [`src/agent.py`](src/agent.py):

- `check_scheme_eligibility(age, occupation, annual_income, gender, has_bank_account)` — checks the caller's answers against each scheme's rules and returns likely-eligible schemes plus near-misses.
- `get_scheme_documents(scheme_name)` — returns the document checklist for a named scheme.

**Data source: this is a local, hand-built dataset, not a live API.** There is no free, machine-readable eligibility API for these government schemes — the authoritative sources are static pages/PDFs published by the Department of Financial Services, PFRDA, and NSI (linked in [`src/schemes.py`](src/schemes.py)). The eligibility rules were curated by hand from those official sources and are marked with an `data_as_of` date (`schemes.DATA_AS_OF`). The agent always states that date when reading out results and tells the caller to confirm final details at their bank branch, since scheme terms do change over time.

**Failure handling:** both tools wrap the lookup in a `try/except` and return `"LOOKUP_FAILED"` (or `"SCHEME_NOT_FOUND"` for an unknown scheme name) instead of raising. The `SYSTEM_PROMPT`'s GOVERNMENT SCHEME LOOKUP section instructs the agent to say so plainly to the caller and suggest trying again or contacting their bank — never to invent scheme names, amounts, or rules.

Unit tests for the eligibility logic and document lookup live in [`tests/test_schemes.py`](tests/test_schemes.py).

## Outbound calling — scheme deadline reminders (Day 6)

Day 5 gave Pooja a tool to check scheme eligibility *when someone calls in*. Day 6 flips that: Pooja now *places* a call to remind someone who was **already found eligible** that a scheme's enrollment window is closing soon — the Financial Services track's outbound trigger.

### How it's wired

- [`src/outbound_caller.py`](src/outbound_caller.py) is a standalone CLI script — it dispatches the `my-agent` job into a fresh LiveKit room with the call's context (name, scheme, deadline, phone number) as job metadata, then dials the phone number into that room via a LiveKit SIP **outbound trunk**.
- `agent.py` reads that metadata (`_parse_outbound_metadata`) and, if present, has `Assistant.on_enter()` open with `build_outbound_opening()` instead of the normal inbound greeting. That opening states **who's calling, why, and how to opt out — in the first two sentences** (a hard requirement for outbound: the person didn't ask for this call and doesn't know who's calling).
- If the caller says anything like "stop calling me" during the call, the agent calls the `opt_out_of_calls` tool, which adds their number to a `do_not_call` table in the SQLite memory DB (`memory.add_do_not_call` / `memory.is_do_not_call`). `outbound_caller.py` checks that table before dialing and skips anyone on it.
- **Outcome handling (advanced):** `outbound_caller.py` classifies a failed dial (`no_answer` / `busy` / `voicemail` / `error`) from the SIP error LiveKit returns, and retries once after a short delay for `no_answer`/`busy` — a hard rejection or error is not retried.

### Setup: Twilio + LiveKit SIP outbound trunk

> ⚠️ **Twilio trial accounts cannot create Elastic SIP Trunks at all.** Trying to (via Console or the Twilio CLI) fails immediately with `Error 20003: This feature is not available on a Trial account`. There's no free-tier workaround on Twilio's side — you need to add a small balance to unlock it.

1. Buy a phone number in your [Twilio Console](https://console.twilio.com/) (or reuse your free trial number) and create an **Elastic SIP Trunk** pointed at your LiveKit project's SIP URI (Settings → SIP in [LiveKit Cloud](https://cloud.livekit.io/)). Twilio's [LiveKit SIP trunking guide](https://docs.livekit.io/sip/quickstarts/configuring-twilio-trunk/) walks through this end to end. The [Twilio CLI](https://www.twilio.com/docs/twilio-cli/quickstart) trunking plugin (`twilio plugins:install @twilio-labs/plugin-trunking`) is more reliable than hunting through the Console UI for this.
2. Create a LiveKit **outbound trunk** referencing your Twilio number/credentials, with the [LiveKit CLI](https://docs.livekit.io/sip/trunk-outbound/):
   ```bash
   lk sip outbound create outbound-trunk.json
   ```
3. Copy the returned trunk ID into `SIP_OUTBOUND_TRUNK_ID` in `.env.local`.
4. **Free alternative:** [Linphone](https://www.linphone.org/)'s free SIP service (`sip.linphone.org`) was tried as a no-cost substitute for Twilio — see [`DAY6_LINPHONE_NOTES.md`](DAY6_LINPHONE_NOTES.md) for the full setup, the bugs hit and fixed along the way (a `timedelta` vs. plain-int protobuf issue, `lk` CLI codec string format), and the unresolved `488 Not Acceptable Here` SIP error this path currently ends on. Treat it as experimental, not a drop-in Twilio replacement.

### Placing a call

With the agent worker running (`uv run python src/agent.py dev`) in one terminal:

```bash
uv run python src/outbound_caller.py \
  --name "Ramesh" --phone "+919876543210" \
  --scheme pmjdy --deadline "31 August"
```

`--scheme` accepts a scheme id or partial name from [`src/schemes.py`](src/schemes.py) (e.g. `pmjdy`, `sukanya samriddhi`).

Unit tests for the opening framing, metadata parsing, and outcome classification live in [`tests/test_outbound.py`](tests/test_outbound.py).

## Human escalation (Day 7)

Pooja doesn't try to resolve everything herself. Two situations always get handed to a human, per `SYSTEM_PROMPT`'s HUMAN ESCALATION section in [`src/agent.py`](src/agent.py):

1. **Possible fraud** — money already lost, a suspicious transaction, or an impersonation attempt the caller acted on. (A general "how do I spot a scam" question is different — Pooja answers that herself.)
2. **A decision Pooja cannot make** — a disputed scheme eligibility result, a rejected application, or the caller explicitly asking for a real person.

### How it's wired

- [`src/escalations.py`](src/escalations.py) is the storage + notification layer: a small SQLite ticket queue (`backend/escalations.db`) plus a best-effort post to a Discord webhook, if `DISCORD_ESCALATION_WEBHOOK_URL` is set. Every escalation gets a short reference ID (`ESC-XXXXXXXX`).
- The `create_escalation` `function_tool` on `Assistant` (in `agent.py`) is the only thing that calls it. The prompt makes calling this tool conditional on the caller's explicit consent — Pooja must say what she wants to send and ask permission first; if the caller says no, nothing is created.
- **Redaction:** the free-text summary fields (`issue_summary`, `already_checked`) are stripped of anything that looks like an OTP, PIN, CVV, password, or an account/Aadhaar/PAN-like number before they're stored or sent anywhere — even if the caller said one out loud on the call. `follow_up_value` (how to reach the caller back) is intentionally *not* redacted, since that's the whole point of the ticket, but the agent should only fill it in with what the caller just agreed to share.
- **No full transcripts** — the agent composes a short factual summary itself; it never dumps the whole conversation into a ticket.
- **Duplicate handling (advanced):** if the same caller already has an open (non-resolved) ticket, a new report on the same issue updates that ticket (appends a note, bumps urgency if higher) instead of creating a second one.
- **Urgency levels (advanced):** `low` / `medium` / `high` / `emergency`, chosen by the agent based on the situation.
- **Status view (advanced):** [`src/view_escalations.py`](src/view_escalations.py) is a tiny CLI "dashboard" — no web frontend needed:
  ```bash
  uv run python src/view_escalations.py            # open + in_progress tickets
  uv run python src/view_escalations.py --all       # every ticket
  uv run python src/view_escalations.py --start ESC-XXXXXXXX     # -> in_progress
  uv run python src/view_escalations.py --resolve ESC-XXXXXXXX   # -> resolved
  ```

### Setup

Escalations work with zero configuration — tickets always save locally. To also get a real-time notification:

1. In Discord: Server Settings → Integrations → Webhooks → New Webhook → Copy Webhook URL.
2. Set `DISCORD_ESCALATION_WEBHOOK_URL` in `.env.local`.

Unit tests for creation, dedup, status transitions, and redaction live in [`tests/test_escalations.py`](tests/test_escalations.py). Two LLM-judged eval tests in `tests/test_agent.py` (`test_asks_permission_before_escalating_fraud`, `test_normal_question_does_not_escalate`) verify the consent gate and that ordinary questions never trigger a ticket.

## Testing

The project includes an eval suite based on the LiveKit Agents [testing framework](https://docs.livekit.io/agents/build/testing/):

```bash
uv run pytest
```

Tests are in [`tests/test_agent.py`](tests/test_agent.py) and use LLM-as-judge evaluations to verify the agent behaves correctly (friendly greetings, grounding, refusing harmful requests).

To run tests in CI, you'll need to add `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` as repository secrets.

## Deployment

### Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY`
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

### Docker

A production-ready [Dockerfile](Dockerfile) is included:

```bash
docker build -t murf-voice-agent .
docker run --env-file .env.local murf-voice-agent
```

## Project Structure

```
backend/
├── src/
│   ├── agent.py          # Agent entrypoint — pipeline, prompt, config, tools
│   ├── memory.py          # SQLite-backed caller memory (Day 4)
│   └── schemes.py         # Local government-scheme dataset + lookup (Day 5)
├── tests/
│   ├── test_agent.py     # LLM-judged eval suite
│   ├── test_memory.py    # Caller memory unit tests
│   └── test_schemes.py   # Scheme eligibility/document unit tests
├── .env.example           # Environment variable template
├── pyproject.toml         # Python dependencies (uv)
├── Dockerfile             # Production container
└── railway.toml           # Railway deploy config
```

## Links

- [Murf Falcon TTS Docs](https://murf.ai/api/docs/text-to-speech/streaming)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Agents Docs](https://docs.livekit.io/agents)
- [Deepgram Nova-3 Docs](https://developers.deepgram.com)

## License

MIT — see [LICENSE](LICENSE).
