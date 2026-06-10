# Chataigne ordering-agent eval harness

A small, runnable harness for measuring how a Chataigne-style WhatsApp ordering agent
behaves. The production backend isn't accessible, so [`agent.py`](agent.py) is a
reconstruction of the flow Chataigne describes publicly: an LLM clerk grounded in a menu
through tool-calling, with the cart and all the arithmetic owned by code, not the model.
The suite runs a fixed set of conversations through it and scores them.

I built this because the first thing I'd want on the team is a way to measure LLM behavior
before anyone starts changing prompts.

## Why it's built this way

| Decision | Why |
|---|---|
| Menu passed in as context | Matches their "prompt engineering + structured retrieval" approach, and lets me test hallucination directly. |
| Cart and totals computed in code, not the model | This is what keeps the money correct. The harness asserts the code-computed total, so if the model quotes a wrong price in text the rubric catches it while the cart stays right. |
| Structured allergen data per item | Allergens are a liability surface. They should be answered from data, not the model's memory. |
| Two ways to score | Order accuracy and totals are checked in code. Behavior (grounding, injection resistance, language) goes to a separate model acting as judge. |

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # from console.anthropic.com

python run_evals.py --category happy_path  # quick smoke test (2 scenarios)
python run_evals.py                        # full suite, writes report.md / report.json
python run_evals.py --category injection
python run_evals.py --threshold 0.9        # exit non-zero under 90% (CI gate)
python agent.py                            # interactive REPL against the reconstruction
```

Both the agent and the judge take a model override via env var, so you can run the suite on
a smaller model while iterating and switch back to the default for a clean run:

```bash
CHATAIGNE_MODEL=claude-haiku-4-5 CHATAIGNE_JUDGE_MODEL=claude-haiku-4-5 python run_evals.py
```

## What the suite covers

The scenarios in [`scenarios.yaml`](scenarios.yaml) line up with the failure taxonomy in
[`../review/01-failure-taxonomy.md`](../review/01-failure-taxonomy.md):

`happy_path`, `modification`, `out_of_menu` (hallucination), `allergen` (liability),
`injection` (prompt-injection / abuse), `multilingual` (including mid-conversation
code-switching), `price_integrity`, `ambiguous`, `business_rule` (delivery minimum and fees).

## How I'd extend it on the team

- **Point it at the real bot.** Swap `agent.py` for a thin client over the production
  WhatsApp webhook so the same scenario set runs against the live agent. The scenarios and
  the judge don't change.
- **Gate regressions.** Wire `--threshold` into CI so a prompt edit that drops injection
  resistance can't ship.
- **Grow the adversarial set.** Auto-generate injection variants and near-menu hallucination
  bait, then review the failures back into the scenario set.
- **Per-locale suites.** The multilingual cases are a start. Real coverage needs native FR/DE
  graders and locale-specific menus.
