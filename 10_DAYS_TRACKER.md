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

## Day 6+

| Day | Date | Focus | What changed / added | Status |
|-----|------|-------|----------------------|--------|
| Day 6 | — | TBD | TBD | ⏳ |
| Day 7 | — | TBD | TBD | ⏳ |
| Day 8 | — | TBD | TBD | ⏳ |
| Day 9 | — | TBD | TBD | ⏳ |
| Day 10 | — | TBD | TBD | ⏳ |

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

