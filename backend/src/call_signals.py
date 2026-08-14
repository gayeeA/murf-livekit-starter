"""Day 8 success-signal helper, shared across agents (Day 9: main + specialist).

A call's outcome (successful/failed, see calls.py) is decided from a shared
mutable ``call_state`` dict that every agent handling the call — the main
Assistant, or a specialist it hands off to — writes into via this one
function. Kept separate from agent.py so specialists.py can use it without
importing agent.py at module load time (agent.py imports specialists.py,
so the reverse import would be circular).
"""

from __future__ import annotations


def mark_success(call_state: dict, signal: str) -> None:
    """Record that this call reached a defined 'successful call' outcome.

    Idempotent — calling it twice with the same signal only records it once.
    """
    signals = call_state.setdefault("signals", [])
    if signal not in signals:
        signals.append(signal)
