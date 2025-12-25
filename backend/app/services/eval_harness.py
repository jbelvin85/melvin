from __future__ import annotations

"""
Lightweight evaluation harness for Melvin.

Usage:
    poetry run python -m backend.app.services.eval_harness

The harness calls MelvinService directly (no HTTP round-trip) so it can run in CI
or on dev machines without bringing up the full stack. Add representative judge
scenarios to SAMPLE_CASES to grow coverage over time.
"""

from typing import List

from .melvin import get_melvin_service


SAMPLE_CASES = [
    {
        "question": "How does [Hullbreacher] interact with [Wheel of Fortune] in Commander?",
        "expect_sources": ["Hullbreacher", "Wheel of Fortune"],
    },
    {
        "question": "If my commander dies twice, how much commander tax is applied?",
        "expect_sources": ["Comprehensive Rules"],
    },
]


def run_case(question: str, expect_sources: List[str]) -> bool:
    service = get_melvin_service()
    answer, thinking, context = service.answer_question_with_details(question)
    ok = True
    if "Sources:" not in answer:
        print(f"[WARN] Missing citations for question: {question!r}")
        ok = False
    for marker in expect_sources:
        if marker not in answer:
            print(f"[WARN] Expected citation fragment {marker!r} not present in answer for: {question!r}")
            ok = False
    if not context.get("rules") and not context.get("cards") and not context.get("knowledge"):
        print(f"[WARN] No grounded context stored for: {question!r}")
        ok = False
    if ok:
        print(f"[OK] {question}")
    return ok


def main() -> None:
    results = [run_case(case["question"], case.get("expect_sources", [])) for case in SAMPLE_CASES]
    passed = sum(1 for result in results if result)
    print(f"Completed {len(results)} cases ({passed} passed, {len(results) - passed} warnings).")


if __name__ == "__main__":
    main()
