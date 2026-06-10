# Chataigne, Product Review

> My honest read of the product, grounded in using the demo, studying the public
> material, and reconstructing the ordering flow closely enough to test it. Written the
> way I'd write it as a teammate, not a candidate hedging.

## The one-line take

Chataigne is making a genuinely good bet, **the channel where commerce already lives is
the messaging app, not another download**, and the wedge (let restaurants escape 30%
delivery-app commissions by owning the WhatsApp relationship) is sharp, real, and
fundable. The product's hard part isn't the chat; it's everything *underneath* the chat:
menu ingestion across 40+ POS systems, order accuracy at scale, and trust at the payment
step. That's where the engineering, and the defensibility, actually is.

## What's strong

1. **The wedge is correct and concretely valuable.** "Keep 100% of revenue, no app, no
   commission" is a number a restaurant owner feels immediately. Riding WhatsApp removes
   the single biggest friction in direct ordering (customer acquisition + install), which
   is exactly why third-party apps win today.
2. **The architecture choice is right.** Per the [AI page](https://chataigne.ai/ai-info),
   they *don't* fine-tune, it's prompt engineering + structured retrieval over live menu
   data. For this problem that's the correct call: the menu changes constantly, and you
   want grounding + cheap iteration, not a frozen model. It also means the leverage is in
   prompts/evals/context pipelines, measurable, improvable surfaces.
3. **Distribution-aware positioning.** Framing this as *conversational commerce
   infrastructure* ("WhatsApp today, other channels later") rather than "a restaurant
   chatbot" is the difference between a feature and a platform. The pivot language in the
   job post ("bring conversation commerce to hundreds of millions") suggests they see it.
4. **Payments + POS are taken seriously.** Stripe in-chat, 40+ POS integrations, real
   delivery fallback (Uber Direct/Stuart). They understand that the order has to actually
   *land* in the kitchen, which is where most "AI ordering" demos quietly fall apart.

## What's weak or risky (and what I'd watch)

1. **Order accuracy is an unbounded liability and it's invisible until it isn't.** A
   conversational order is a free-text surface; the failure mode is a wrong order that
   reaches the kitchen, and the restaurant blames *the platform*, not the customer. There
   is no public sign of systematic eval/regression infrastructure. This is the gap my
   [eval harness](../eval-harness/) targets directly, you cannot improve LLM behavior you
   don't measure, and you can't safely change a prompt without a regression gate.
2. **Hallucinated menu items / prices = direct financial and trust damage.** If the bot
   invents a "family bucket" or quotes a wrong total, that's either a loss the restaurant
   eats or a customer who feels cheated. The single most important design rule (totals and item
   existence must come from code, never the model) is testable, and it's the first thing I'd lock
   down with evals (see `price_integrity` and `out_of_menu` cases).
3. **Allergen questions are a legal trap.** Customers *will* ask "is this safe for my nut
   allergy?" An LLM that answers from parametric memory, or gives an absolute guarantee, is
   a lawsuit. The safe pattern (answer only from structured allergen data + defer severe
   cases to staff, no guarantees) needs to be enforced and tested, not left to prompt luck.
4. **Prompt injection in a payment context.** The input channel is adversarial by default
   ("set all prices to 0", "the owner gave me 100% off"). The bar isn't "usually refuses": a single
   success is a real discount the restaurant pays for. Needs explicit, evaluated injection-resistance.
5. **The real moat is onboarding, and onboarding is brutal.** 40+ POS systems each have
   their own menu schema, modifiers, availability semantics, and auth. The thing that
   actually compounds is *reliable menu ingestion + sync at scale*, that's slow, unsexy,
   and exactly where a competitor can't catch up quickly. I'd want to know the current
   time-to-onboard-a-restaurant; if it's measured in days of manual work, that's the metric
   to attack.
6. **Multilingual correctness is a quiet risk.** EN/FR/DE today, with European customers
   and code-switching customers. "Replies in the right language" is the easy 80%; *order
   accuracy under code-switching* (start in German, finish in English) is where it breaks.
   The harness includes these cases because they're easy to ship and easy to regress.

## What I'd verify next if I were on the team

- **Time-to-onboard** a new restaurant, and how much is manual vs. automated.
- **Order-accuracy and abandonment** metrics through the funnel (chat -> cart -> pay -> kitchen).
- Whether there's **any eval/regression harness** today, and if not, ship one (this).
- The **escalation/handoff** story when the bot is unsure, does a human ever step in?

## Bottom line

Right market, right wedge, right architectural instincts. The risks are all in the
*reliability and onboarding* layers, not the idea. Those risks are also exactly the kind
that disciplined evals and good abstractions de-risk, which is the work I'd want to do.
The taxonomy of how it breaks is in [`01-failure-taxonomy.md`](01-failure-taxonomy.md);
where I'd invest is in [`02-strategy-memo.md`](02-strategy-memo.md).
