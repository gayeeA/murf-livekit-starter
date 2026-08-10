"""Government financial-inclusion scheme data for the Pooja voice agent.

Day 5 tool: "scheme eligibility check from collected answers + document
checklist" (the Financial Services track's suggested lookup tool).

DATA SOURCE (read this before trusting the numbers):
    This is a hand-built LOCAL dataset, not a live API call. There is no
    free, public, machine-readable eligibility API for these schemes — the
    real sources are static PDFs/pages published by the Department of
    Financial Services, PFRDA, and NSI. The criteria below were curated by
    hand from those official rules and are believed correct as of
    ``DATA_AS_OF``, but scheme rules do change (e.g. Sukanya Samriddhi
    interest rates are revised quarterly by the government). Pooja always
    tells the caller the data's as-of date and directs them to the bank /
    official portal to confirm before they act, per the system prompt's
    KNOWLEDGE guardrail.

    Official references used to compile this dataset:
    - https://www.pmjdy.gov.in
    - https://www.jansuraksha.gov.in (PMSBY / PMJJBY / APY)
    - https://www.nsiindia.gov.in (Sukanya Samriddhi Yojana)
    - https://www.pmvishwakarma.gov.in
    - https://www.standupmitra.in
    - https://www.mudra.org.in
"""

from __future__ import annotations

from typing import Any

DATA_AS_OF = "2026-04-01"

# Each scheme's eligibility rule is intentionally simple (min/max age, income
# ceiling, gender, occupation) because that is what a caller can answer over
# the phone in one or two short questions.
SCHEMES: list[dict[str, Any]] = [
    {
        "id": "pmjdy",
        "name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "name_te": "ప్రధాన్ మంత్రి జన్ ధన్ యోజన",
        "category": "bank account",
        "summary": "A zero-balance savings bank account for anyone without one, with a RuPay debit card and accident cover.",
        "eligibility": {
            "age_min": 10,
            "age_max": None,
            "gender": "any",
            "income_max_annual": None,
            "requires_no_bank_account": True,
        },
        "documents": [
            "Aadhaar card (or any officially valid ID)",
            "One recent passport-size photo",
            "Address proof if your Aadhaar address is outdated",
        ],
    },
    {
        "id": "pmsby",
        "name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "name_te": "ప్రధాన్ మంత్రి సురక్ష బీమా యోజన",
        "category": "accident insurance",
        "summary": "Accidental death and disability insurance cover for a very small yearly premium (about 20 rupees).",
        "eligibility": {
            "age_min": 18,
            "age_max": 70,
            "gender": "any",
            "income_max_annual": None,
            "requires_bank_account": True,
        },
        "documents": [
            "Existing savings bank account",
            "Aadhaar card",
            "A filled auto-debit consent form (your bank branch has this)",
        ],
    },
    {
        "id": "pmjjby",
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "name_te": "ప్రధాన్ మంత్రి జీవన్ జ్యోతి బీమా యోజన",
        "category": "life insurance",
        "summary": "Life insurance cover of 2 lakh rupees for a low yearly premium (about 436 rupees), renewed every year.",
        "eligibility": {
            "age_min": 18,
            "age_max": 50,
            "gender": "any",
            "income_max_annual": None,
            "requires_bank_account": True,
        },
        "documents": [
            "Existing savings bank account",
            "Aadhaar card",
            "A filled auto-debit consent form (your bank branch has this)",
        ],
    },
    {
        "id": "apy",
        "name": "Atal Pension Yojana (APY)",
        "name_te": "అటల్ పెన్షన్ యోజన",
        "category": "pension",
        "summary": "A guaranteed monthly pension after age 60, funded by small monthly contributions now.",
        "eligibility": {
            "age_min": 18,
            "age_max": 40,
            "gender": "any",
            "income_max_annual": None,
            "requires_bank_account": True,
            "notes": "You should not already be an income-tax payer to join.",
        },
        "documents": [
            "Existing savings bank account",
            "Aadhaar card",
            "Mobile number linked to your bank account",
        ],
    },
    {
        "id": "ssy",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "name_te": "సుకన్య సమృద్ధి యోజన",
        "category": "girl child savings",
        "summary": "A high-interest savings account a parent or guardian opens for a girl child, for her education or marriage expenses later.",
        "eligibility": {
            "age_min": 0,
            "age_max": 10,
            "gender": "female",
            "income_max_annual": None,
            "notes": "Account is for the girl child; opened and operated by a parent or legal guardian.",
        },
        "documents": [
            "Girl child's birth certificate",
            "Aadhaar card of the girl child and the parent/guardian",
            "Address proof of the parent/guardian",
        ],
    },
    {
        "id": "pm_vishwakarma",
        "name": "PM Vishwakarma Yojana",
        "name_te": "పీఎం విశ్వకర్మ యోజన",
        "category": "artisan support",
        "summary": "Skill training, a toolkit allowance, and collateral-free loans for traditional artisans and craftspeople (carpenters, tailors, potters, and similar trades).",
        "eligibility": {
            "age_min": 18,
            "age_max": None,
            "gender": "any",
            "income_max_annual": None,
            "occupation_any_of": [
                "artisan",
                "craftsperson",
                "carpenter",
                "tailor",
                "potter",
                "blacksmith",
                "weaver",
                "cobbler",
                "barber",
            ],
        },
        "documents": [
            "Aadhaar card",
            "Proof of your trade (e.g. a trade certificate or local body reference letter, if you have one)",
            "Bank account details",
        ],
    },
    {
        "id": "stand_up_india",
        "name": "Stand-Up India",
        "name_te": "స్టాండ్-అప్ ఇండియా",
        "category": "business loan",
        "summary": "Bank loans between 10 lakh and 1 crore rupees to set up a new business, reserved for SC/ST and women entrepreneurs.",
        "eligibility": {
            "age_min": 18,
            "age_max": None,
            "gender": "female_or_sc_st",
            "income_max_annual": None,
            "notes": "At least 51% ownership/controlling stake must be with an SC/ST person or a woman, for a new (greenfield) enterprise.",
        },
        "documents": [
            "Identity and address proof (Aadhaar, PAN)",
            "Caste certificate, if applying under the SC/ST category",
            "A basic project report or business plan",
        ],
    },
    {
        "id": "mudra",
        "name": "Pradhan Mantri Mudra Yojana (PMMY)",
        "name_te": "ప్రధాన్ మంత్రి ముద్రా యోజన",
        "category": "business loan",
        "summary": "Collateral-free loans up to 20 lakh rupees for small businesses and micro-enterprises, in three tiers: Shishu, Kishor, and Tarun.",
        "eligibility": {
            "age_min": 18,
            "age_max": None,
            "gender": "any",
            "income_max_annual": None,
            "occupation_any_of": [
                "small business",
                "shopkeeper",
                "vendor",
                "self-employed",
                "micro-enterprise",
                "trader",
            ],
        },
        "documents": [
            "Identity and address proof (Aadhaar, PAN)",
            "Business proof (shop registration, GST if any, or a simple business plan for a new business)",
            "Passport-size photo",
        ],
    },
]


def _matches(scheme: dict[str, Any], age: int | None, occupation: str | None,
             annual_income: int | None, gender: str | None,
             has_bank_account: bool | None) -> tuple[bool, list[str]]:
    """Check one scheme's eligibility rules. Returns (eligible, reasons_if_not)."""
    rule = scheme["eligibility"]
    reasons: list[str] = []

    if age is not None:
        if rule.get("age_min") is not None and age < rule["age_min"]:
            reasons.append(f"minimum age is {rule['age_min']}")
        if rule.get("age_max") is not None and age > rule["age_max"]:
            reasons.append(f"maximum age is {rule['age_max']}")

    if rule.get("income_max_annual") is not None and annual_income is not None:
        if annual_income > rule["income_max_annual"]:
            reasons.append(f"annual income must be under {rule['income_max_annual']}")

    gender_rule = rule.get("gender", "any")
    if gender_rule not in ("any", None) and gender:
        g = gender.strip().lower()
        if gender_rule == "female" and g != "female":
            reasons.append("this scheme is for girl children / women")
        if gender_rule == "female_or_sc_st" and g != "female":
            # Can't verify SC/ST over a quick call, so only flag the gender gap;
            # SC/ST applicants of any gender remain eligible in principle.
            pass

    occ_rule = rule.get("occupation_any_of")
    if occ_rule and occupation:
        occ = occupation.strip().lower()
        if not any(o in occ or occ in o for o in occ_rule):
            reasons.append("this scheme targets specific occupations: " + ", ".join(occ_rule))

    if rule.get("requires_bank_account") and has_bank_account is False:
        reasons.append("requires an existing savings bank account first")

    return (len(reasons) == 0, reasons)


def check_eligibility(
    age: int | None = None,
    occupation: str | None = None,
    annual_income: int | None = None,
    gender: str | None = None,
    has_bank_account: bool | None = None,
) -> dict[str, Any]:
    """Check which schemes the given answers make someone likely eligible for.

    Any answer the caller hasn't given yet should be passed as None — that
    criterion is simply skipped rather than treated as a fail.
    """
    eligible: list[dict[str, str]] = []
    maybe: list[dict[str, str]] = []

    for scheme in SCHEMES:
        ok, reasons = _matches(scheme, age, occupation, annual_income, gender, has_bank_account)
        entry = {
            "id": scheme["id"],
            "name": scheme["name"],
            "category": scheme["category"],
            "summary": scheme["summary"],
        }
        if ok:
            eligible.append(entry)
        elif len(reasons) <= 1:
            # Close match (fails on just one criterion) - worth mentioning.
            entry["reason_not_eligible"] = reasons[0] if reasons else ""
            maybe.append(entry)

    return {
        "data_as_of": DATA_AS_OF,
        "eligible": eligible,
        "close_but_not_eligible": maybe,
    }


def get_documents(scheme_name_or_id: str) -> dict[str, Any] | None:
    """Look up the document checklist for one scheme by name or id (fuzzy match)."""
    query = scheme_name_or_id.strip().lower()
    for scheme in SCHEMES:
        if query == scheme["id"] or query in scheme["name"].lower() or scheme["name"].lower() in query:
            return {
                "id": scheme["id"],
                "name": scheme["name"],
                "documents": scheme["documents"],
                "data_as_of": DATA_AS_OF,
            }
    return None
