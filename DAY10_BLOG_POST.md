# Meet Pooja: A Telugu-Speaking Financial Helpline That Never Judges You

*10 Days of Voice Agents — VoiceForBharat Edition, Financial Services track*

## The problem, and who it's for

In a lot of India — gig workers, daily-wage earners, first-time UPI users, rural households — the nearest bank branch is a bus ride away, and the questions people actually have ("is this WhatsApp message a scam?", "what's a Jan Dhan account?", "which government scheme am I even eligible for?") feel too basic to ask a bank officer in person. English-only banking apps and IVR menus don't help either, especially for someone more comfortable in Telugu than English.

So for the Financial Services track of #VoiceForBharat, I built **Pooja** — "డబ్బు స్నేహితుడు," the money friend. A voice agent, not a chatbot, because the people this is for are used to *talking* to get help, not typing into a form. She speaks Telugu, Hindi, English, or whatever code-mixed blend the caller uses, explains money basics in plain language, and — critically — knows the difference between "I can explain this" and "you need a human for this."

## What Pooja actually does

Ten days, one agent, growing one capability at a time:

- Understands savings/budgeting, UPI and scam patterns, EMIs and interest, and KYC — in plain language, mirroring the caller's language
- Remembers returning callers (SQLite-backed memory) so they don't repeat their story every call
- Looks up real government scheme eligibility (Jan Dhan, PMSBY/PMJJBY, Atal Pension Yojana, Sukanya Samriddhi, PM Vishwakarma, Stand-Up India, Mudra) against a hand-curated dataset, and reads back the document checklist
- Makes **outbound** calls to remind eligible callers of scheme deadlines, respecting opt-out and a do-not-call list
- Knows when *not* to solve something herself — fraud, disputed transactions, and other sensitive cases get escalated to a human, with the caller's consent, and a ticket + Discord notification
- Tracks call outcomes on a live analytics dashboard (success rate, failure types, channel split) — without ever storing a name, phone number, or transcript
- As of Day 9, hands off scheme-eligibility questions mid-call to a **specialist agent** built just for that job, then hands the conversation back

## How the system works

```mermaid
flowchart LR
    A[🎙️ Caller speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM — Gemini]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit real-time transport]
    E -->|stream| F[🔊 Caller hears]
```

Four moving parts, same as any voice agent:
- **STT** (Deepgram Nova-3) turns the caller's speech into text
- **LLM** (Google Gemini) decides what to say and which tools to call
- **TTS** ([Murf Falcon](https://murf.ai/api/docs/text-to-speech/streaming)) turns the response back into speech — this is the part I'd call out specifically: 55ms model latency and ~130ms time-to-first-audio is the difference between a call that feels like a real conversation and one with an awkward "is it thinking?" pause after every turn
- **LiveKit Agents** wires all of it together and handles the real-time audio transport, both for browser calls and real SIP phone calls

On top of that pipeline: a Next.js frontend that shows the agent's state (listening / thinking / speaking) so callers using the browser demo aren't staring at silence, and a Python backend (`agent.py`) where the actual behavior — prompt, guardrails, tools — lives.

## The features that tell the story

**Guardrails first, features second.** Before I added a single tool, Pooja's prompt had hard rules: never ask for or repeat back an OTP/PIN/CVV/account number, never promise loan or scheme approval, never give investment/legal/tax advice, always say "I don't know, here's where to check" instead of guessing. Every feature added after that had to respect those rules — the scheme-lookup tool, for instance, returns `LOOKUP_FAILED` rather than letting the LLM invent a plausible-sounding scheme name.

**Human escalation, with consent.** Fraud and disputed-decision calls don't get "solved" by an LLM — Pooja asks permission, then creates an escalation ticket and pings Discord. Deciding *when* to hand off to a human is as much a design decision as anything else in the build.

**Handoff to a specialist agent (Day 9).** This was the last big piece: government scheme eligibility involves real rules (age, income, occupation, gender) that deserved a narrower, focused agent instead of one more section in an ever-growing prompt. Pooja now hands the call mid-conversation to a **Scheme Specialist** agent — full conversation context carries over, the handoff is spoken out loud on both ends, and the specialist hands back once the caller's question moves elsewhere. Here's the shape of it:

```python
@function_tool
async def transfer_to_scheme_specialist(self, context: RunContext):
    """Hand off to the government scheme specialist for eligibility
    checks and document checklists."""
    try:
        specialist = SchemeSpecialistAgent(
            chat_ctx=self.chat_ctx,          # caller never repeats themselves
            call_state=self._call_state,      # shared analytics state
            outbound_context=self._outbound_context,
        )
    except Exception:
        logger.exception("Failed to start the scheme specialist")
        return "HANDOFF_FAILED"
    return "Connecting the caller to the scheme specialist now.", specialist
```

Returning a `(text, Agent)` tuple is all LiveKit Agents needs to swap the active agent mid-call — the framework does the rest.

## The hard parts

**Silent failure is the enemy of voice UX.** The first version of the handoff, if something went wrong constructing the specialist, would have just... not handed off, with no explanation. In a voice call, silence reads as "the app is broken," not "the app is being careful." The fix was making failure a first-class, spoken outcome: `transfer_to_scheme_specialist` catches the exception, returns a plain `"HANDOFF_FAILED"` string, and the prompt tells Pooja to apologize and suggest the caller try again or visit their bank branch. It actually fired once during testing — Pooja caught it, said so out loud, and kept the call alive instead of going dead. That's the fallback path proving itself, not a demo failing.

**Storing "enough to be useful" without storing "too much."** Day 4's memory and Day 8's call-analytics log both needed to persist *something* across calls, but this is a financial helpline — an OTP, PIN, or full account number landing in a SQLite row is a real liability, not a hypothetical. The rule I settled on: memory stores facts the caller volunteers about their situation, never credentials; the call log stores outcome/duration/channel, never a name, phone number, or transcript. Every new persistent field got run through "would I be comfortable if this table leaked?" before it got added.

**A dev server that looks alive but isn't.** More mundane, but real: partway through testing, the frontend's `next dev` process died silently mid-session, and the browser kept trying to talk to it — producing a confusing `Failed to fetch` / `publishing rejected as engine not connected` error pair that looked like a LiveKit problem but was actually "nothing is listening on port 3000 anymore." Lesson: when a browser-side WebRTC/LiveKit error shows up, check that both halves of the stack (frontend *and* backend agent process) are actually still running before debugging the protocol.

## Build it yourself

**The starter this is built on:** [murf-ai/murf-livekit-starter](https://github.com/murf-ai/murf-livekit-starter) — Next.js frontend + Python/LiveKit Agents backend, Murf Falcon TTS wired in by default.

**My build:** [github.com/gayeeA/murf-livekit-starter](https://github.com/gayeeA/murf-livekit-starter)

1. **Clone and install**
   ```bash
   git clone https://github.com/gayeeA/murf-livekit-starter.git
   cd murf-livekit-starter
   cd backend && uv sync
   cd ../frontend && pnpm install
   ```

2. **Add your API keys — never commit these.** Copy `.env.example` → `.env.local` in *both* `backend/` and `frontend/` (both are already git-ignored). You'll need:
   - A free [LiveKit Cloud](https://cloud.livekit.io/) project → `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (same three values in both `.env.local` files)
   - A [Murf API key](https://murf.ai/api/dashboard) → `MURF_API_KEY`
   - A [Deepgram key](https://deepgram.com) → `DEEPGRAM_API_KEY`
   - A [Google AI Studio key](https://aistudio.google.com/apikey) → `GOOGLE_API_KEY` (or swap in OpenAI)

3. **Run both halves**
   ```bash
   # terminal 1
   cd backend && uv run src/agent.py dev
   # terminal 2
   cd frontend && pnpm dev
   ```

4. **Talk to it** — open `http://localhost:3000` in a browser, or run `uv run src/agent.py console` for a terminal-only conversation with no frontend at all. Either way, the agent joins a LiveKit room and you can just start talking.

Swap the `SYSTEM_PROMPT` in `backend/src/agent.py` and you have a completely different agent — a receptionist, a language tutor, an interview coach. The pipeline underneath doesn't change.

## What I'd improve next

- A proper "confidence" signal on scheme eligibility results, so Pooja can say "likely eligible" vs "borderline, please confirm at your branch" instead of a flat yes/no
- More specialist agents (e.g., a fraud/scam specialist) using the same handoff pattern now that it's proven out
- Real load-tested latency numbers from the Day 8 dashboard, not just anecdotal "it felt fast"

## Thanks to Murf AI

None of this would sound like a real conversation without the TTS layer, and that's the piece I'd single out. **Murf Falcon** is the fastest production TTS I've used — 55ms model latency, ~130ms time-to-first-audio across 10+ global regions — which is what let Pooja respond without the awkward dead-air pause that makes a voice bot feel like a voice bot. On top of that, 150+ voices across 35+ languages meant an Indian-English/Telugu-appropriate voice was available out of the box, not something I had to fine-tune myself.

Thanks to **Murf AI** for running 10 Days of Voice Agents — VoiceForBharat Edition, and for building an API fast enough that a 10-day challenge could actually ship something that feels production-grade rather than a proof-of-concept demo.

## Links

- Repo: [github.com/gayeeA/murf-livekit-starter](https://github.com/gayeeA/murf-livekit-starter)
- Starter template: [github.com/murf-ai/murf-livekit-starter](https://github.com/murf-ai/murf-livekit-starter)
- Built with [Murf Falcon TTS](https://murf.ai/api/docs/text-to-speech/streaming) and [LiveKit Agents](https://docs.livekit.io/agents/)

*Built as part of 10 Days of Voice Agents — VoiceForBharat Edition. #VoiceForBharat*
