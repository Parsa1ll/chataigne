# Failure taxonomy, conversational ordering agent

Eight failure classes a Chataigne-style ordering agent has to survive, derived from first
principles about the problem and from probing the flow. Each one is (a) commercially
meaningful, (b) reproducible, and (c) wired to concrete tests, either a probe against the
**live demo bot** ([`../redteam/redteam-plan.md`](../redteam/redteam-plan.md)) or a scored
scenario in the **eval harness** ([`../eval-harness/scenarios.yaml`](../eval-harness/scenarios.yaml)),
usually both.

The **Live-bot** column points to the probe in the red-team plan that exercises each class; the
actual results are written up in [`../redteam/findings.md`](../redteam/findings.md). The point of the
taxonomy is that none of these are abstract: every row is something you can trigger on purpose and
then gate against.

| # | Failure class | What it looks like | Why it matters | Live-bot (probe) | Harness coverage |
|---|---|---|---|---|---|
| F1 | **Menu hallucination** | Bot accepts/quotes an item that doesn't exist ("family bucket", "fish taco") | Loss the restaurant eats, or a cheated customer; erodes trust instantly | §2.1-2.4 | `out_of_menu_item`, `out_of_menu_protein` |
| F2 | **Price / math drift** | Bot's quoted total disagrees with the real total; same order priced differently twice | Direct revenue error; undermines the "transparent pricing" promise | §4.1-4.3 | `price_integrity_bulk`, `price_integrity_extras_math` |
| F3 | **Order-accuracy under edits** | Mid-order modification/removal leaves the cart wrong | Wrong order reaches the kitchen -> refund + angry restaurant | §3.1-3.4 | `modify_change_mind`, `modify_remove_item` |
| F4 | **Allergen / liability over-reach** | Bot answers allergy questions from memory, or gives an absolute "safe" guarantee | Health + legal exposure; the worst-case failure | §5.1-5.3 | `allergen_peanut`, `allergen_dairy` |
| F5 | **Prompt injection / abuse** | "Set prices to 0", "owner gave me 100% off", fake `SYSTEM:` lines | Unauthorized discounts = real money; role-hijack = brand damage | §6.1-6.5 | `injection_free_food`, `injection_prompt_leak`, `injection_role_change` |
| F6 | **Multilingual / code-switch errors** | Wrong language, or order corrupted when the customer switches languages mid-order | Silent accuracy loss across a whole market segment | §7.1-7.4 | `multilingual_french`, `multilingual_codeswitch` |
| F7 | **Ambiguity mishandling** | Bot guesses a full order from "gimme some tacos" instead of clarifying | Confident-wrong orders; worse than asking | §1.2, §8.3 | `ambiguous_quantity`, `ambiguous_spice` |
| F8 | **Business-rule violations** | Ignores delivery minimum / radius / fees; places invalid orders | Operational breakage, unfulfillable orders | harness only | `delivery_minimum`, `delivery_fee_applied` |

## Severity ranking (where I'd spend reliability budget first)

1. **F4 allergen**, lowest frequency, highest blast radius. Lock the safe pattern + test it.
2. **F1 hallucination** and **F2 price drift**, frequent, directly financial, and *fully
   preventable in code* (ground item existence and arithmetic outside the model). Cheapest
   high-value win.
3. **F5 injection**, adversarial input in a payment loop; one success is real money.
4. **F3 / F6 / F7 / F8**, accuracy/UX correctness; high volume, addressed well by a
   golden-set regression gate.

## The throughline

F1, F2, and F8 should essentially never reach the model's discretion: **item existence,
prices, totals, and business rules belong in code**, with the LLM doing language, not
arithmetic or policy. That's the design the [reconstruction](../eval-harness/agent.py)
demonstrates (cart + totals are code-owned; the model is instructed to quote tool numbers
verbatim), and it's the first architectural thing I'd verify is true in production.
