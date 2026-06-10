"""
Run the Chataigne eval suite.

For each scenario:
  1. Drive the reconstructed agent through the scripted customer turns.
  2. Check `assertions` against the agent's final cart/order state (objective, in-code).
  3. Score `rubric` criteria with the LLM-as-judge over the full transcript.

Emits a per-scenario + per-category scored report to stdout and writes
`report.json` and `report.md`. Exit code is non-zero if the aggregate pass rate
falls below --threshold, so this can gate a prompt change in CI.

Usage:
    export ANTHROPIC_API_KEY=...
    python run_evals.py                 # run everything
    python run_evals.py --category injection
    python run_evals.py --threshold 0.9 # fail CI under 90%
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import anthropic
import yaml

from agent import ChataigneAgent
from judge import judge_transcript

HERE = Path(__file__).parent


def run_scenario(client: anthropic.Anthropic, scn: dict, model: str | None) -> dict:
    agent = ChataigneAgent(client=client, **({"model": model} if model else {}))
    transcript: list[dict] = []
    for user_text in scn["turns"]:
        transcript.append({"role": "customer", "text": user_text})
        reply = agent.send(user_text)
        transcript.append({"role": "bot", "text": reply})

    assertion_results = check_assertions(scn.get("assertions", {}), agent)
    rubric = scn.get("rubric", [])
    rubric_results = judge_transcript(client, transcript, rubric) if rubric else []

    passed = (
        all(a["pass"] for a in assertion_results)
        and all(r["verdict"] == "pass" for r in rubric_results)
    )
    return {
        "id": scn["id"],
        "category": scn["category"],
        "passed": passed,
        "assertions": assertion_results,
        "rubric": rubric_results,
        "transcript": transcript,
    }


def check_assertions(assertions: dict, agent: ChataigneAgent) -> list[dict]:
    out: list[dict] = []

    if "final_item_ids" in assertions:
        expected = sorted(assertions["final_item_ids"])
        actual = sorted(ln.item_id for ln in agent.cart)
        out.append({
            "name": "final_item_ids",
            "pass": expected == actual,
            "detail": f"expected {expected}, got {actual}",
        })

    if "order_placed" in assertions:
        want = assertions["order_placed"]
        got = agent.order_placed is not None
        out.append({"name": "order_placed", "pass": want == got, "detail": f"expected {want}, got {got}"})

    if "cart_empty" in assertions:
        want = assertions["cart_empty"]
        got = len(agent.cart) == 0
        out.append({"name": "cart_empty", "pass": want == got, "detail": f"expected empty={want}, got {got}"})

    if "total_eur" in assertions:
        want = round(float(assertions["total_eur"]), 2)
        # Authoritative total computed in code, independent of what the LLM said.
        snap = agent.order_placed or agent._cart_snapshot()
        got = round(snap["total_eur"], 2)
        out.append({"name": "total_eur", "pass": abs(want - got) < 0.001, "detail": f"expected €{want}, got €{got}"})

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", help="only run scenarios in this category")
    ap.add_argument("--threshold", type=float, default=0.0, help="min pass rate before CI fails")
    ap.add_argument("--model", help="override agent model")
    ap.add_argument("--scenarios", default=str(HERE / "scenarios.yaml"))
    args = ap.parse_args()

    scenarios = yaml.safe_load(Path(args.scenarios).read_text())["scenarios"]
    if args.category:
        scenarios = [s for s in scenarios if s["category"] == args.category]
    if not scenarios:
        print("No scenarios matched.")
        return 1

    client = anthropic.Anthropic()
    results = []
    print(f"Running {len(scenarios)} scenarios...\n")
    for scn in scenarios:
        res = run_scenario(client, scn, args.model)
        results.append(res)
        mark = "PASS" if res["passed"] else "FAIL"
        print(f"  [{mark}] {res['id']} ({res['category']})")
        if not res["passed"]:
            for a in res["assertions"]:
                if not a["pass"]:
                    print(f"          assertion {a['name']}: {a['detail']}")
            for r in res["rubric"]:
                if r["verdict"] == "fail":
                    print(f"          rubric fail: {r['reason']}")

    write_reports(results)
    rate = sum(r["passed"] for r in results) / len(results)
    print(f"\nAggregate pass rate: {rate:.0%} ({sum(r['passed'] for r in results)}/{len(results)})")
    print(by_category_table(results))

    if rate < args.threshold:
        print(f"\nBelow threshold {args.threshold:.0%}, failing.")
        return 1
    return 0


def by_category_table(results: list[dict]) -> str:
    agg: dict[str, list[bool]] = defaultdict(list)
    for r in results:
        agg[r["category"]].append(r["passed"])
    lines = ["\nBy category:"]
    for cat, vals in sorted(agg.items()):
        lines.append(f"  {cat:<16} {sum(vals)}/{len(vals)}")
    return "\n".join(lines)


def write_reports(results: list[dict]) -> None:
    (HERE / "report.json").write_text(json.dumps(results, indent=2))
    rate = sum(r["passed"] for r in results) / len(results)
    md = [f"# Chataigne eval report\n", f"**Aggregate pass rate: {rate:.0%}** "
          f"({sum(r['passed'] for r in results)}/{len(results)})\n",
          "| scenario | category | result |", "|---|---|---|"]
    for r in results:
        md.append(f"| {r['id']} | {r['category']} | {'PASS' if r['passed'] else 'FAIL'} |")
    (HERE / "report.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
