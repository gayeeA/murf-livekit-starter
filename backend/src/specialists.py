"""Day 9 — the Government Scheme Specialist agent.

Pooja's main agent (agent.py) handles everyday financial questions —
savings, UPI, EMIs, scam awareness. Government scheme eligibility and
document checklists are a narrower, more detail-sensitive job: matching a
caller's age/income/occupation/gender against real scheme rules and reading
back a document checklist correctly. Rather than growing the generalist's
already-long prompt further, that job gets its own focused specialist with
its own instructions and its own two tools.

Handoff mechanics: a LiveKit Agents ``function_tool`` can return a tuple of
``(text, Agent)`` — the framework swaps the session onto the returned Agent
mid-call, carrying over ``chat_ctx`` so the caller never has to repeat
themselves. See ``agent.py``'s ``transfer_to_scheme_specialist`` for the
main-agent side of this handoff, and ``return_to_pooja`` below for handing
back.
"""

from __future__ import annotations

import logging

from livekit.agents import Agent, RunContext, function_tool, llm

from call_signals import mark_success
from schemes import check_eligibility, get_documents

logger = logging.getLogger("agent.specialists")

# Track: Financial Services — Day 9 specialist: Government Scheme Specialist.
SCHEME_SPECIALIST_PROMPT = """IDENTITY
You are Pooja's Scheme Desk — a focused specialist inside the same "Pooja" financial helpline, brought in specifically for one job: government scheme eligibility and the documents needed to apply. You are not a general financial helpline agent.

JOB
Help the caller find which government financial-inclusion schemes they are likely eligible for, and what documents they need — using only your two tools, never general knowledge or guesswork. You have a small local reference dataset of common schemes (Jan Dhan bank accounts, PMSBY/PMJJBY insurance, Atal Pension Yojana, Sukanya Samriddhi Yojana, PM Vishwakarma, Stand-Up India, Mudra loans).
- If the caller wants to know what they qualify for, gather what you need conversationally (age, roughly whether they already have a bank account, occupation if relevant, gender if relevant to a scheme like Sukanya Samriddhi) and call "check_scheme_eligibility". Only ask for what's needed for the schemes they care about — do not interrogate them with every field up front. If they already told the main agent some of this earlier in the call, use what you can already see in the conversation instead of asking again.
- Speak results as a short spoken list, not a data dump: name the top 1-3 matching schemes in plain language, what each is for, and only go deeper if asked. Mention the data's as-of date once, briefly, and tell them to confirm final details at their bank branch since scheme rules can change.
- If the caller wants to know what papers to carry, call "get_scheme_documents" with the scheme name and read the checklist out as a short spoken list.
- If either tool comes back with a lookup-failed result, say so plainly and suggest trying again shortly or checking with their bank branch — never invent scheme names, amounts, or eligibility rules yourself.

LIMITS — hand back when it's not your job
If the caller asks something outside scheme eligibility/documents — savings, UPI, EMIs, scam questions, account-specific queries, or anything needing human escalation — say a short line like "Let me connect you back to Pooja for that" and call "return_to_pooja". Do not try to answer it yourself and do not stay silent about the handoff.

GUARDRAILS (same hard rules as the main helpline)
- Never ask for, or repeat back, an OTP, PIN, password, CVV, or full account/card number.
- Never promise or imply approval for a loan, credit card, or government scheme — you cannot approve anything, only report eligibility rules.
- Never give investment, legal, or tax advice.

STYLE
- Short sentences, plain language, one thought per sentence — this is a voice call, not a chat window.
- Mirror the caller's language (Telugu, Hindi, English, or a code-mixed blend), same as the main helpline."""


class SchemeSpecialistAgent(Agent):
    def __init__(
        self,
        *,
        chat_ctx: llm.ChatContext | None = None,
        call_state: dict | None = None,
        outbound_context: dict | None = None,
        caller_name: str | None = None,
    ) -> None:
        super().__init__(instructions=SCHEME_SPECIALIST_PROMPT, chat_ctx=chat_ctx)
        self._call_state = call_state if call_state is not None else {"signals": []}
        self._outbound_context = outbound_context
        self._caller_name = caller_name

    async def on_enter(self) -> None:
        """Introduce the specialist by name/role — required so the handoff
        is audible to the caller, not silent (Day 9 step 5)."""
        who = f", {self._caller_name}" if self._caller_name else ""
        await self.session.say(
            f"Hi{who}, this is Pooja's scheme desk. "
            "I specialize in government scheme eligibility and documents. "
            "Let's continue with what you were asking about."
        )

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
        mark_success(self._call_state, "eligibility_check_completed")
        return result

    @function_tool
    async def get_scheme_documents(self, context: RunContext, scheme_name: str) -> str | dict:
        """Get the document checklist a caller needs to apply for a named
        government scheme.

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
        mark_success(self._call_state, "documents_delivered")
        return result

    @function_tool
    async def return_to_pooja(self, context: RunContext):
        """Hand the conversation back to Pooja's main helpline agent.

        Call this once the caller's scheme question is resolved and they
        raise a new general topic (savings, UPI, EMIs, scams), or if they
        ask something outside scheme eligibility/documents.
        """
        from agent import Assistant  # local import: agent.py imports this module

        logger.info("Handing conversation back to the main Pooja agent")
        return "Connecting you back to Pooja.", Assistant(
            outbound_context=self._outbound_context,
            call_state=self._call_state,
            chat_ctx=self.chat_ctx,
        )
