# 📅 10 Days of Voice Agents — Progress Tracker

A daily log of what was changed, built, and learned while building **Pooja** — a Telugu-fluent, plain-language financial helpline voice agent for #VoiceForBharat, powered by **Murf Falcon TTS** + **LiveKit Agents**.

---

## Day 1 — Financial Helpline Persona: "Vitta Mitra"

**Commit:** `52a608d` — `first day of the murfai challenge`

**What changed / what was added:**
- 🎭 Replaced the default customer-support prompt with a **financial helpline persona** — "Vitta Mitra" (Hindi for *money friend*), aimed at gig workers, daily-wage earners, first-time UPI users, and rural households.
- 🧠 Added `ENABLE_TURN_DETECTION` env flag + `build_turn_detection()` helper that gracefully falls back to VAD-only mode when the multilingual turn-detector model isn't available.
- 🗣️ Switched Murf TTS voice from `Anisha` → **`Samar`** (Indian English, male) for a steady, grounded helpline tone.
- ✅ Added a test (`test_agent.py` +10) covering the turn-detection fallback path.

**Files touched:**
- `backend/src/agent.py` (+59)
- `backend/tests/test_agent.py` (+10)

---

## Day 2 — Personality, Job, & Limits: "Pooja" (Telugu Money Friend)

**Commit:** `ead8fe0` — `Day 2: Added financial safety guardrails`

**What changed / what was added:**
- 🏷️ **Rebranded persona** "Vitta Mitra" → **"Pooja"** (డబ్బు స్నేహితుడు — *money friend*), now **fluent in Telugu** and able to code-switch between Telugu, Hindi, and English.
- 📜 **Restructured `SYSTEM_PROMPT`** into the Day-2 template:
  **IDENTITY · OBJECTIVES · KNOWLEDGE · LANGUAGE · GUARDRAILS · STYLE**
- 🛡️ **Financial safety guardrails** — the agent never asks for or repeats OTPs, PINs, passwords, CVVs, or full account/card numbers; never promises/implies loan or scheme approval; never gives investment advice or claims access to personal data.
- 🚨 **Escalation script** — directs callers to their bank branch, the RBI **Sachet** portal (`sachet.rbi.org.in`), and the national cyber-crime helpline **1930**.
- 🎙️ **Multilingual STT** — Deepgram set to `language="multi"` so Telugu/Hindi/English speech is transcribed.
- 🗣️ **Voice updated** `Samar` → **`Pooja`** (Indian English, female), matching the new persona name.
- 👋 **First-turn greeting** — added `Assistant.on_enter()` with a warm bilingual (Telugu + English) self-introduction.
- 🤫 **Silent-user handling** — `user_away_timeout=10s`; one gentle re-prompt on silence, then a graceful goodbye + `session.shutdown()` after a second silent period.
- 🧪 **Added 3 new LLM-judged eval tests** — OTP refusal, loan-approval refusal, and Telugu code-mixed response.
- 🧨 **Created `RED_TEAM.md`** — 10 adversarial guardrail-break prompts (OTP/PIN fishing, authority pressure, jailbreak, guaranteed returns, silence, repetitive loops) with expected safe behavior.
- 🎨 **Frontend branding updated** — `companyName: 'Pooja'`, page title *"Pooja — Voice Financial Helpline"*, "Talk to Pooja" start button.
- 🐛 **Frontend polish** — fixed `useAgentErrors` hook (deduplicated failure toast via `useRef`, added fallback message, removed auto-`end()`); added `suppressHydrationWarning` to layout; dependency updates.

**Files touched:**
- `backend/src/RED_TEAM.md` (new, +57)
- `backend/src/agent.py` (+129/-… )
- `backend/tests/test_agent.py` (+112)
- `frontend/app-config.ts` (±8)
- `frontend/app/layout.tsx` (+1)
- `frontend/hooks/useAgentErrors.tsx` (±79)
- `frontend/package.json`, `frontend/pnpm-lock.yaml` (deps)

---

## Day 3 — Personalise the Frontend: Premium Fintech UI for "Pooja"

**Commit:** `a4d3e98` — `day 3 : updated the UI for the user friendly`

**What changed / what was added:**
- 🎨 **New premium color palette** — cool blue/violet fintech theme (`#34aeda` primary, `#7864e3` accent) applied consistently across `globals.css` (light + dark tokens, contrast-checked), `app-config.ts` accents, and the audio visualizer bars. Added a subtle radial-gradient background wash.
- 🪙 **New brand mark** — gradient rupee-style logo (`pooja-logo.svg` / `pooja-logo-dark.svg`) replacing the missing default LiveKit logo, used in the header and OG image.
- 🖼️ **Rebuilt Welcome ("Ready") screen** — card layout with gradient icon badge, "Savings / Loans / Insurance / Cards" topic pills, single "Talk to Pooja" CTA, and a privacy note ("Your call is private. No financial details are stored.").
- ⏳ **New Connecting state** (`connecting-view.tsx`) — spinner + "Connecting you to Pooja… please wait" copy; previously this state had no dedicated UI.
- 🎧 **Live Listening/Speaking indicator** (`agent-status-label.tsx`) — a pill badge pinned above the call screen that reads "Listening to you" / "Pooja is speaking" / "Pooja is thinking…", driven by the real `useAgent()` state, alongside the existing bar visualizer.
- 🔚 **New Call Ended screen** (`call-ended-view.tsx`) — explicit confirmation + "Talk to Pooja" restart button, instead of silently reverting to the welcome screen.
- 🎙️ **Microphone permission handling** (`mic-permission-notice.tsx`) — clear, plain-language messages for denied / no-device / unknown mic errors, checked proactively before connecting and reactively via `onDeviceError` during the call.
- 🔁 **New view state machine** (`view-controller.tsx`) — derives `ready / connecting / active / ended` from LiveKit's `connectionState` instead of a binary `isConnected` flag, so all five required states render distinctly.
- 🪧 **Header polish** (`layout.tsx`) — brand pill (logo + "Pooja" + "Financial Helpline") and a "Voice powered by Murf Falcon" badge.
- ✅ Verified with `tsc --noEmit`, `next build`, `eslint`, and a live dev-server smoke test — all clean, no console errors.

**Files touched:**
- `frontend/app-config.ts` (colors, logo paths, visualizer config)
- `frontend/app/layout.tsx` (header)
- `frontend/styles/globals.css` (palette + background)
- `frontend/components/app/view-controller.tsx` (state machine)
- `frontend/components/app/welcome-view.tsx` (Ready state)
- `frontend/components/app/connecting-view.tsx` (new — Connecting state)
- `frontend/components/app/call-ended-view.tsx` (new — Call Ended state)
- `frontend/components/app/agent-status-label.tsx` (new — Listening/Speaking indicator)
- `frontend/components/app/mic-permission-notice.tsx` (new — mic error handling)
- `frontend/components/agents-ui/blocks/agent-session-view-01/components/agent-session-block.tsx` (wired status label + device error passthrough)
- `frontend/public/pooja-logo.svg`, `frontend/public/pooja-logo-dark.svg` (new)

---

## Day 4 — Persistent Caller Memory: "Pooja" Remembers You

**Commit:** `—` — `Day 4: Added persistent caller memory (SQLite)`

**What changed / what was added:**
- 🗄️ **New storage layer** (`backend/src/memory.py`) — a small SQLite-backed persistence engine with a storage-agnostic interface (`lookup_user`, `save_user`, `forget_user`, `forget_user_by_name`, `init_db`). Data survives a full agent restart because it lives in a `memory.db` file (path overridable via `MEMORY_DB_PATH`).
- 🛡️ **Financial Services privacy guard** — a `_sanitize()` layer strips anything sensitive (account/card numbers, full Aadhaar/PAN, OTPs, PINs, passwords, phone numbers, long numeric runs) at both key and value level, so the agent can never persist data it shouldn't. This enforces the Day-4 hard rule.
- 🧠 **New agent tools** (in `Assistant`) — `lookup_user` (find a caller by name), `save_user_facts` (persist agreed facts), and `forget_user` (bonus: wipe a caller's record on request). The agent calls these itself; memory is read/written **through functions, not the prompt**.
- 👋 **Returning-caller greeting flow** — `SYSTEM_PROMPT` gained a **MEMORY & PERSONALISATION** section: the agent asks for the caller's name, looks them up, greets returning callers by name ("Namaste Ramesh, last time we spoke about your savings…") and continues from last time; new callers are welcomed as normal.
- ✅ **Consent before saving** — the prompt makes it a hard rule to ask the caller's permission before saving anything, and to drop it if they say no (mandatory for Financial Services).
- 🎙️ **Greeting updated** — `on_enter()` now also asks for the caller's name so the lookup can happen early in the call.
- 🧪 **New test suite** (`tests/test_memory.py`, 8 tests) — save/lookup round-trip, case-insensitive lookup, fact merging, forget by name and by id, and sensitive-data stripping (keys, values, long numbers). All pass.

**Files touched:**
- `backend/src/memory.py` (new — SQLite persistence + sanitizer)
- `backend/src/agent.py` (imports, MEMORY prompt section, 3 function tools, greeting, `init_db()` call)
- `backend/tests/test_memory.py` (new — 8 unit tests)
- `10_DAYS_TRACKER.md`

---

## Day 5 — Scheme Eligibility Tool: "Pooja" Learns to Look Things Up

**Commit:** `—` — `Day 5: Added government scheme eligibility + document checklist tool`

**What changed / what was added:**
- 🗂️ **New local dataset** (`backend/src/schemes.py`) — hand-curated eligibility rules and document checklists for 8 common government financial-inclusion schemes (Jan Dhan bank accounts, PMSBY, PMJJBY, Atal Pension Yojana, Sukanya Samriddhi Yojana, PM Vishwakarma, Stand-Up India, Mudra loans), compiled from official DFS/PFRDA/NSI sources and stamped with a `DATA_AS_OF` date. **This is local data, not a live API** — no free machine-readable eligibility API exists for these schemes; the README says so explicitly.
- 🧠 **Two new agent tools** — `check_scheme_eligibility` (matches age/occupation/income/gender/bank-account answers against scheme rules, returns eligible + "close but not eligible" schemes) and `get_scheme_documents` (document checklist by scheme name, fuzzy-matched).
- 📜 **New GOVERNMENT SCHEME LOOKUP prompt section** — tells the agent to gather only what's needed conversationally (not interrogate), speak results as a short natural list (not a data dump), always mention the data's as-of date, and point callers to their bank branch to confirm.
- 🛑 **Graceful failure path** — both tools catch exceptions and return `"LOOKUP_FAILED"`/`"SCHEME_NOT_FOUND"` instead of raising; the prompt instructs the agent to say so plainly and suggest retrying or contacting the bank, never to invent scheme details.
- 🧪 **New test suite** (`tests/test_schemes.py`, 9 tests) — eligibility matching (bank-account-required, age windows, gender-gated, occupation-gated schemes), unspecified answers being skipped rather than failed, and document lookup by partial name/id/unknown scheme. All pass.

**Files touched:**
- `backend/src/schemes.py` (new — local scheme dataset + eligibility/document lookup)
- `backend/src/agent.py` (import, GOVERNMENT SCHEME LOOKUP prompt section, 2 function tools)
- `backend/tests/test_schemes.py` (new — 9 unit tests)
- `backend/README.md` (Tools section documenting the dataset and its data-freshness)
- `10_DAYS_TRACKER.md`

---

## Day 6 — Outbound Calls: "Pooja" Reminds Eligible Callers of Scheme Deadlines

**Commit:** `—` — `Day 6: Added outbound scheme-deadline reminder calls via LiveKit SIP`

**What changed / what was added:**
- 📞 **Outbound use case (Financial Services track)** — "scheme deadline approaching for someone already found eligible." Builds directly on Day 5's local scheme dataset: Pooja now calls people who were previously checked as eligible, before their scheme's enrollment window closes.
- 🗂️ **New CLI dialer** (`backend/src/outbound_caller.py`) — dispatches the `my-agent` job into a fresh LiveKit room with call context (name, scheme, deadline, phone) as job metadata, then dials the number into that room via a LiveKit SIP **outbound trunk** backed by Twilio (or Linphone as a free fallback).
- 👋 **Outbound-aware opening** — `agent.py` reads the job metadata (`_parse_outbound_metadata`) and, when present, has `on_enter()` say `build_outbound_opening()` instead of the inbound greeting: states **who's calling (Pooja), why (scheme deadline reminder), and how to opt out — within the first two sentences**, per the Day-6 hard rule that outbound calls need this up front.
- 🚫 **Opt-out handling** — a new `opt_out_of_calls` tool adds the caller's number to a `do_not_call` SQLite table (`memory.add_do_not_call` / `memory.is_do_not_call`), kept separate from caller "facts" so a raw phone number is never treated as persisted personal data. `outbound_caller.py` checks this table before dialing and skips anyone who opted out. The `OUTBOUND_PROMPT_ADDENDUM` instructs the agent to call this tool immediately on any "stop calling me" request, no arguing or re-pitching.
- 🔁 **Outcome handling (advanced)** — `outbound_caller.py` classifies a failed dial into `no_answer` / `busy` / `voicemail` / `error` from the SIP failure message, and retries once after a 45s delay for `no_answer`/`busy`; hard errors are not retried.
- 🧪 **New test suite** (`tests/test_outbound.py`, 12 tests) — opening framing (who/why/opt-out present), metadata parsing (valid + malformed/non-outbound payloads rejected), scheme name resolution, and outcome classification. Plus 2 new tests in `tests/test_memory.py` for the do-not-call registry.
- 📖 **README** — new "Outbound calling — scheme deadline reminders (Day 6)" section documenting the Twilio + LiveKit SIP outbound trunk setup and how to place a call.

**Real-world telephony setup saga (the actual Day 6 grind):**
- Twilio trial account hit a hard wall — **Elastic SIP Trunking is not available on trial accounts at all** (`Error 20003`), via Console or the Twilio CLI. No workaround; requires a paid top-up.
- Tried **Linphone's free SIP service** (`sip.linphone.org`) as a zero-cost alternative instead of upgrading Twilio: free account, LiveKit outbound trunk pointed at `sip.linphone.org`, dialing the Linphone username as the "phone number."
- Hit and fixed two real bugs along the way (now fixed in `outbound_caller.py`):
  - `ringing_timeout` / `max_call_duration` are protobuf `Duration` fields — passing plain ints crashed with `AttributeError: 'int' object has no attribute 'seconds'`. Fixed with `datetime.timedelta(seconds=...)`.
  - `lk sip outbound update --codecs` uses `<name>` or `<name>/<sample-rate>` (e.g. `opus/48000`), not the SDP-style `opus/48000/2` — `lk` rejected the latter outright.
- Still unresolved as of today: the actual call attempt fails with **`488 Not Acceptable Here`**, even after widening codecs and disabling forced encryption. Likely cause: `sip.linphone.org` doesn't treat LiveKit's SIP trunk as a legitimate peer the way it treats registered Linphone app users — this needs a real SIP trace to confirm, which wasn't available today. Full troubleshooting log (setup steps, every error hit, what was tried, what's next) is in [`backend/DAY6_LINPHONE_NOTES.md`](backend/DAY6_LINPHONE_NOTES.md).
- Fallback if Linphone stays unresolved: switch `SIP_OUTBOUND_TRUNK_ID` to a real paid trunk (Twilio top-up, or a cheaper provider like Telnyx/Plivo) — no code changes needed either way, since `outbound_caller.py`/`agent.py` are provider-agnostic.

**Files touched:**
- `backend/src/outbound_caller.py` (new — CLI dialer; later fixed the `timedelta` bug)
- `backend/src/agent.py` (outbound metadata parsing, opening builder, opt-out tool, `OUTBOUND_PROMPT_ADDENDUM`)
- `backend/src/memory.py` (do-not-call registry)
- `backend/tests/test_outbound.py` (new — 12 unit tests)
- `backend/tests/test_memory.py` (+2 tests)
- `backend/.env.example` (`SIP_OUTBOUND_TRUNK_ID`)
- `backend/README.md` (Day 6 setup section + Twilio-trial-blocker warning + Linphone pointer)
- `backend/DAY6_LINPHONE_NOTES.md` (new — Linphone free-SIP troubleshooting log)
- `10_DAYS_TRACKER.md`

---

## Day 7 — Know When to Ask for Human Help: "Pooja" Escalates Fraud & Disputed Decisions

**Commit:** `—` — `Day 7: Added human-escalation tool with consent gate and Discord notification`

**What changed / what was added:**
- 🙋 **Two escalation triggers (Financial Services track)** — (1) the caller reports possible fraud (money already lost, a suspicious transaction, an impersonation attempt acted on — distinct from a general "how do scams work" question, which Pooja still answers herself), and (2) the caller needs a decision Pooja can't make (a disputed eligibility result, a rejected application, or an explicit request for a real person).
- 🗂️ **New escalation-ticket layer** (`backend/src/escalations.py`) — a small SQLite queue (`escalations.db`) with a `create_or_update_escalation` function, short reference IDs (`ESC-XXXXXXXX`), urgency levels (`low`/`medium`/`high`/`emergency`), and status transitions (`open` → `in_progress` → `resolved`).
- 🛡️ **Redaction before storage** — `issue_summary` and `already_checked` are stripped of anything that looks like an OTP, PIN, CVV, password, or account/Aadhaar/PAN-like number (including spaced Aadhaar formatting) before the ticket is saved or sent anywhere, even if the caller said it out loud.
- 🔁 **Duplicate handling (advanced)** — a second report from the same caller with an open ticket updates that ticket (appends a note, bumps urgency) instead of creating a fragmenting duplicate.
- 🧠 **New `create_escalation` tool + HUMAN ESCALATION prompt section** in `agent.py` — the prompt makes the tool call conditional on the caller's explicit consent: Pooja states what she wants to send in plain words and asks permission first; a "no" means nothing gets created.
- 📣 **Discord webhook notification** — `escalations.notify_discord()` best-effort posts new/updated tickets to a Discord channel if `DISCORD_ESCALATION_WEBHOOK_URL` is configured; tickets are always saved locally regardless, so nothing is lost if the webhook isn't set up or fails.
- 🖥️ **Status dashboard (advanced)** — `backend/src/view_escalations.py`, a small CLI that lists open/all tickets and moves them between `in_progress`/`resolved`, satisfying the "local database with a page that shows open requests" option without a web frontend.
- 🧪 **New test suite** (`tests/test_escalations.py`, 9 tests) — ticket creation, dedup-and-update, resolved tickets not being reused, status-transition validation, urgency fallback, and sensitive-data redaction. Plus 2 new LLM-judged eval tests in `tests/test_agent.py` (`test_asks_permission_before_escalating_fraud`, `test_normal_question_does_not_escalate`) verifying the consent gate and that ordinary answerable questions never create a ticket.
- 📖 **README** — new "Human escalation (Day 7)" section documenting the two triggers, consent flow, redaction rules, Discord webhook setup, and the CLI dashboard.

**Files touched:**
- `backend/src/escalations.py` (new — ticket storage, redaction, Discord notify)
- `backend/src/view_escalations.py` (new — CLI status dashboard)
- `backend/src/agent.py` (`create_escalation` tool, HUMAN ESCALATION prompt section, DB init)
- `backend/tests/test_escalations.py` (new — 9 unit tests)
- `backend/tests/test_agent.py` (+2 eval tests)
- `backend/.env.example` (`DISCORD_ESCALATION_WEBHOOK_URL`)
- `backend/README.md` (Day 7 section)
- `10_DAYS_TRACKER.md`

---

## Day 8 — Call Analytics Dashboard: Tracking How "Pooja" Is Actually Doing

**Commit:** `—` — `Day 8: Added call outcome logging + call analytics dashboard`

**What changed / what was added:**
- 🎯 **Success definition (Financial Services track, from Day 2 objectives)** — a call is **successful** if the caller reached one of three concrete outcomes: completed a government-scheme **eligibility check**, received a scheme's **document checklist**, or had a **human-escalation ticket created** for fraud/dispute (the "appropriate escalation" outcome, since knowing when *not* to solve it herself is part of Pooja's job too). Anything else is a **failed** call — not necessarily something broke, just that the caller didn't reach one of those outcomes.
- 🗂️ **New call-outcome log** (`backend/src/calls.py`) — a small SQLite table (`calls.db`), one row written per call, exactly once, when the session closes. Only aggregate/non-identifying fields are stored: call id, channel, timestamps, duration, outcome, failure type, and which outcome type was reached. **No caller name, phone number, transcript, or financial detail ever lands in this table** (Day-8 Step-6 hard rule).
- 🧩 **Wired into `agent.py`** — a `call_state` dict is created per call and passed into `Assistant`; the three success-path tools (`check_scheme_eligibility`, `get_scheme_documents`, `create_escalation`) call `self._mark_success(...)` only on genuine success, never on `LOOKUP_FAILED`/`SCHEME_NOT_FOUND`/`ESCALATION_FAILED`. Channel (`browser` vs `sip`) is captured from the room's noise-cancellation callback — the earliest point the linked participant's kind is known. A `session.on("close", ...)` handler reads `call_state` and writes the final row.
- 🏷️ **Failure-type classification (advanced)** — failed calls are grouped into `user_hangup`, `user_declined` (explicit opt-out), `no_response` (silence timeout), `error` (unrecoverable STT/LLM/TTS failure), or `incomplete` (any other non-outcome ending).
- 🖥️ **New live dashboard** (`backend/src/dashboard_server.py` + `dashboard_static/index.html`) — a **zero-new-dependency**, Python-stdlib-only web server exposing `/api/summary` and `/api/calls`, serving a dark-themed page that shows Total/Successful/Failed calls, success rate, a failure-type breakdown, a browser-vs-SIP channel split, and a recent-calls table (advanced options: success rate, failure types, call history, channel filter data — all done). Auto-refreshes every 5s so counts visibly climb during a live demo. Run with `uv run python src/dashboard_server.py`, opens at `http://localhost:8787`.
- 🧪 **New test suite** (`tests/test_calls.py`, 11 tests) — summary counting/success-rate math, failure-type fallback, channel breakdown, ordering/limit of recent calls, duration computation, invalid-outcome rejection, and a table-shape assertion proving no sensitive column exists to leak into.
- 📖 **README** — new "Call analytics dashboard (Day 8)" section documenting the success definition, failure-type table, wiring, and how to run the dashboard.

**Files touched:**
- `backend/src/calls.py` (new — SQLite call-outcome log)
- `backend/src/dashboard_server.py` (new — stdlib web server)
- `backend/src/dashboard_static/index.html` (new — dashboard page)
- `backend/src/agent.py` (`call_state` tracking, 3 tools mark success signals, channel capture, `session.on("close", ...)` handler, `init_calls_db()`)
- `backend/tests/test_calls.py` (new — 11 unit tests)
- `backend/.env.example` (`DASHBOARD_PORT`, `CALLS_DB_PATH`)
- `backend/README.md` (Day 8 section + Project Structure update)
- `10_DAYS_TRACKER.md`

---

## Day 9 — Hand Off to a Specialist Agent: "Pooja" Calls in the Scheme Desk

**Commit:** `—` — `Day 9: Added Government Scheme Specialist agent with mid-call handoff`

**What changed / what was added:**
- 🧑‍💼 **One specialist, one job (Financial Services track)** — the **Government Scheme Specialist**, with a narrower job than the main agent: government scheme eligibility checks and document checklists only. Nothing else.
- 🗂️ **New specialist agent** (`backend/src/specialists.py`) — `SchemeSpecialistAgent`, its own IDENTITY/JOB/LIMITS/GUARDRAILS/STYLE prompt, and the `check_scheme_eligibility`/`get_scheme_documents` tools **moved off** the main `Assistant` (Day 5) onto the specialist, since one agent shouldn't try to be an expert at everything.
- 🔀 **Handoff mechanics** — a `function_tool` (`transfer_to_scheme_specialist` on the main agent) returns `(text, Agent)`; LiveKit Agents' multi-agent support detects the `Agent` in the return value and switches the session onto it automatically (`session.update_agent(...)`). The specialist is constructed with `chat_ctx=self.chat_ctx`, so **the caller never has to re-explain their question** — full conversation history carries over.
- 📢 **Handoff is audible, not silent** — the main agent's prompt requires a short spoken line ("Let me connect you to our scheme specialist...") before the handoff tool is called; the specialist's `on_enter()` introduces itself ("Hi, this is Pooja's scheme desk...") the moment it takes over.
- 🔁 **Hand-back (advanced)** — the specialist has its own `return_to_pooja` tool for when the caller's topic moves outside scheme eligibility/documents (savings, UPI, EMIs, scams, fraud escalation); same handoff pattern, reversed.
- 🧯 **Failed-handoff handling (advanced)** — `transfer_to_scheme_specialist` wraps specialist construction in `try/except`; on failure it returns the plain string `"HANDOFF_FAILED"` (no `Agent`, so no handoff occurs), and the prompt tells the main agent to apologise and suggest the bank branch rather than leaving the caller stuck.
- 🔗 **Shared state across the handoff (advanced)** — new `backend/src/call_signals.py` holds the `mark_success()` helper both agents call into the same shared `call_state` dict (Day 8), and `outbound_context` (Day 6) is threaded through both directions too, so a scheme lookup completed *after* a handoff still counts correctly on the Day 8 dashboard, and an outbound-reminder call keeps its framing if handed back.
- 🧪 **New test suite** (`tests/test_specialists.py`, 6 tests) — handoff returns a specialist sharing `call_state`/`outbound_context`, failed-handoff fallback, specialist tools marking success on the shared state, and hand-back constructing a proper `Assistant`. Plus 2 new LLM-judged eval tests in `tests/test_agent.py` verifying a scheme-eligibility question triggers exactly one handoff (with an announcement) and an ordinary UPI question does not.
- 📖 **README** — new "Specialist handoff — Government Scheme Desk (Day 9)" section; Day 5's tools section updated to point at the new location.

**Files touched:**
- `backend/src/specialists.py` (new — `SchemeSpecialistAgent`)
- `backend/src/call_signals.py` (new — shared `mark_success()` helper)
- `backend/src/agent.py` (removed 2 scheme tools + prompt section, added `transfer_to_scheme_specialist`, `chat_ctx` passthrough on `Assistant.__init__`)
- `backend/tests/test_specialists.py` (new — 6 unit tests)
- `backend/tests/test_agent.py` (+2 eval tests)
- `backend/README.md` (Day 9 section, Day 5 section update, Project Structure update)
- `10_DAYS_TRACKER.md`

---

## Day 10 — Share Your Voice Agent Journey

**Commit:** `—` — `Day 10: Blog post + LinkedIn recap of the 10-day build`

**What changed / what was added:**
- 📝 **Blog post** ([`DAY10_BLOG_POST.md`](DAY10_BLOG_POST.md)) — a public write-up of the whole build: the problem and who Pooja is for, how the STT→LLM→TTS→LiveKit pipeline works, the features that best tell the story (guardrails, memory, scheme lookup, outbound calls, human escalation, the analytics dashboard, the Day 9 specialist handoff), three real difficulties hit during the build and how they were resolved, and a practical "build it yourself" section (clone, add API keys, run both halves, talk to it).
- 🔗 **LinkedIn recap** — summarizes the 10-day build, credits Murf Falcon TTS by name, tags Murf AI, and uses #VoiceForBharat, per the Day 10 submission requirements.
- 🐛 **Two real bugs surfaced and diagnosed while preparing today's content** (folded into the blog's "hard parts" section): the frontend `next dev` process dying silently mid-session (diagnosed via `Get-NetTCPConnection` showing nothing on port 3000 — not a LiveKit/protocol issue as the browser error first suggested), and a one-time `HANDOFF_FAILED` on the Day 9 scheme-specialist handoff that turned out to be a symptom of that same dead frontend rather than a bug in the handoff code — confirmed by reproducing the full handoff → eligibility-check flow cleanly against a freshly restarted backend.

**Files touched:**
- `DAY10_BLOG_POST.md` (new — blog draft, ready to paste into DEV/Hashnode/Medium)
- `10_DAYS_TRACKER.md`

---


## How to update this tracker

After each day's work, add a section above and/or fill the Day-N row. Keep it short:

```markdown
## Day N — <focus>
**Commit:** `<short-sha>` — `<commit message>`
**What changed / added:**
- ... bullet points of each user-visible or code change
**Files touched:** `path` (+/-)
```

## Quick references
- System prompt / pipeline: `backend/src/agent.py`
- Guardrail tests: `backend/tests/test_agent.py`
- Red-team prompts: `backend/src/RED_TEAM.md`
- Frontend branding: `frontend/app-config.ts`
- This file: `10_DAYS_TRACKER.md`