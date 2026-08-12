"""Day 7 — tiny local dashboard for escalation requests.

No web frontend needed: this just prints every escalation (or only the open
ones) as a readable table, and lets you move a ticket's status along for the
"human" side of the demo.

Usage:
    uv run python src/view_escalations.py                # open + in_progress
    uv run python src/view_escalations.py --all           # every ticket
    uv run python src/view_escalations.py --resolve ESC-AB12CD34
    uv run python src/view_escalations.py --start ESC-AB12CD34   # -> in_progress
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from escalations import (
    init_db,
    list_all_escalations,
    list_open_escalations,
    update_status,
)

load_dotenv(".env.local")


def _print_table(records: list[dict]) -> None:
    if not records:
        print("(no escalations)")
        return
    for r in records:
        print(f"[{r['status'].upper():^11}] {r['reference_id']}  urgency={r['urgency']}")
        print(f"    caller: {r['caller_name']}  language: {r['language'] or '—'}")
        print(f"    issue: {r['issue_summary']}")
        if r["already_checked"]:
            print(f"    already checked: {r['already_checked']}")
        print(f"    follow-up: {r['follow_up_method'] or 'unspecified'}")
        if r["notes"]:
            print(f"    {len(r['notes'])} follow-up note(s) from repeat calls")
        print(f"    created: {r['created_at']}  updated: {r['updated_at']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="View / update Pooja's escalation queue.")
    parser.add_argument("--all", action="store_true", help="Show resolved tickets too")
    parser.add_argument("--resolve", metavar="REFERENCE_ID", help="Mark a ticket resolved")
    parser.add_argument("--start", metavar="REFERENCE_ID", help="Mark a ticket in_progress")
    args = parser.parse_args()

    init_db()

    if args.resolve:
        ok = update_status(args.resolve, "resolved")
        print(f"{args.resolve}: {'resolved' if ok else 'not found'}")
        return
    if args.start:
        ok = update_status(args.start, "in_progress")
        print(f"{args.start}: {'in_progress' if ok else 'not found'}")
        return

    records = list_all_escalations() if args.all else list_open_escalations()
    _print_table(records)


if __name__ == "__main__":
    main()
