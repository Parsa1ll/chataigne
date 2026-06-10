"""
LLM-as-judge for the Chataigne eval harness.

Given a conversation transcript and a list of natural-language rubric criteria,
the judge scores each criterion pass/fail with a one-line justification. We use a
separate model context (a fresh request) and structured outputs so the result is
machine-readable and CI-gateable.

Judging is deliberately strict: a criterion only passes if the transcript clearly
satisfies it. "Unclear" counts as a fail, because in production an ambiguous order
is a wrong order.
"""

from __future__ import annotations

import json
import os

import anthropic

JUDGE_MODEL = os.environ.get("CHATAIGNE_JUDGE_MODEL", "claude-opus-4-8")

JUDGE_SYSTEM = """You are a strict QA grader for a restaurant ordering assistant.
You are given a transcript between a customer and the ordering bot, plus a list of
criteria. For each criterion, decide whether the transcript clearly satisfies it.

Grade strictly:
- "pass" only if the transcript clearly and fully meets the criterion.
- "fail" if it is violated, partially met, or too ambiguous to be sure.
Judge only what the criterion asks about. Give a one-sentence reason citing the
transcript."""

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["pass", "fail"]},
                    "reason": {"type": "string"},
                },
                "required": ["criterion", "verdict", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def format_transcript(turns: list[dict]) -> str:
    """turns: list of {'role': 'customer'|'bot', 'text': ...}"""
    out = []
    for t in turns:
        speaker = "CUSTOMER" if t["role"] == "customer" else "BOT"
        out.append(f"{speaker}: {t['text']}")
    return "\n".join(out)


def judge_transcript(
    client: anthropic.Anthropic,
    transcript: list[dict],
    rubric: list[str],
    model: str = JUDGE_MODEL,
) -> list[dict]:
    user = (
        "TRANSCRIPT:\n"
        + format_transcript(transcript)
        + "\n\nCRITERIA:\n"
        + "\n".join(f"{i+1}. {c}" for i, c in enumerate(rubric))
        + "\n\nGrade every criterion."
    )
    resp = client.messages.create(
        model=model,
        max_tokens=1500,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": RESULT_SCHEMA}},
    )
    text = next(b.text for b in resp.content if b.type == "text")
    data = json.loads(text)
    return data["results"]
