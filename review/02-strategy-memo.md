# Strategy memo, where the moat is, and what I'd build first

> Short, opinionated. The product review covers strengths/risks; this is about
> defensibility and sequencing.

## 1. The moat is not the chat. It's ingestion + reliability.

The conversational UX is the *demo*, and it's commoditizing fast (every chatbot vendor in
the search results does "order on WhatsApp"). It is not where durable advantage lives.
Two things actually compound:

- **Menu ingestion + sync across 40+ POS systems.** Each POS (Toast, Square, Lightspeed,
  Zelty, iiko, Clover, Revel, Micros…) has its own schema for items, modifiers, combos,
  availability, and pricing. Turning all of that into a clean, queryable menu the agent can
  ground on, and keeping it in sync as the restaurant changes prices at 5pm, is slow,
  unglamorous integration work that a competitor cannot shortcut. **Every integration you
  finish is a moat brick.** This is the real "infrastructure" in "conversational commerce
  infrastructure."
- **Measured reliability.** A restaurant will tolerate a slightly clunky bot; it will *not*
  tolerate wrong orders hitting the kitchen. The company that can *prove* (and hold) order
  accuracy as it ships changes wins retention. That proof is an eval/regression system, which is why
  I built one as the centerpiece rather than writing more opinions.

## 2. "WhatsApp today, other channels later" implies a real abstraction to design

The job post and homepage both gesture at multi-channel. The clean version of this is a
**channel-agnostic ordering core** with thin channel adapters:

```
            ┌─────────────── Ordering Core ───────────────┐
 WhatsApp ──┤  • conversation / intent                    │
 Instagram ─┤  • menu grounding (per-restaurant context)  ├── POS adapters (Toast, Square, …)
 SMS ───────┤  • cart + pricing + business rules (CODE)   │── Payments (Stripe)
 Voice ─────┤  • order state machine                      │── Delivery (Uber Direct, Stuart)
            └──────────────────────────────────────────────┘
             channel adapters: message in/out, media, auth
```

Designing the channel boundary well now (so adding Instagram DMs or voice is an adapter,
not a rewrite) is exactly the "design clear abstractions for commerce and communication
channels" line in the role. The non-negotiable invariant: **pricing, item existence, and
business rules live in the core, in code, never re-implemented per channel, never left to
the model.**

## 3. What I'd build first (in order)

1. **The eval harness, on real traffic.** Ship [the harness](../eval-harness/) against a
   reconstruction first (done), then point the same golden set at the production agent and
   wire `--threshold` into CI. Now every prompt/context change is gated on order accuracy,
   hallucination, injection resistance, and language correctness. This is force-multiplying:
   it makes every subsequent change safe and fast.
2. **Lock the code-owned invariants.** Audit that totals, item existence, and business
   rules (F1/F2/F8) are computed in code, not the model. Add the failing cases to the gate.
3. **Allergen safe-pattern + test (F4).** Structured allergen answers, no guarantees,
   staff-escalation on severe, enforced and evaluated. Cheap insurance against the worst case.
4. **Onboarding instrumentation.** Measure time-to-onboard and where the manual hours go in
   menu ingestion. Attack the biggest manual step. This is the metric that gates growth.
5. **Failure-driven golden-set growth.** Pipe real production failures + adversarial
   generation back into the golden set weekly. The eval suite should grow faster than the
   bug list.

## 4. One contrarian note

The temptation will be to make the conversation *more* capable (recommendations, upsells,
chit-chat, memory of past orders). Resist front-loading that. Every added capability is new
surface for F1-F8 to hurt a paying restaurant. The winning sequence is **boringly reliable
ordering first, delight second**, because in commerce, a wrong order costs more trust than
a great one earns. Reliability *is* the growth strategy here.
