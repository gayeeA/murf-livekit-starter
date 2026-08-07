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

## Day 3+

| Day | Date | Focus | What changed / added | Status |
|-----|------|-------|----------------------|--------|
| Day 3 | — | TBD | TBD | ⏳ |
| Day 4 | — | TBD | TBD | ⏳ |
| Day 5 | — | TBD | TBD | ⏳ |
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

