# Châtaigne teardown, redesign, and eval harness

**A take-home for VZ Labs, Member of Technical Staff (Co-op). By Parsa Ahmadnezhad.**

I spent a day with the live product (including Châtaigne's public demo bot) before writing
anything. I ran 9 red-team probes against the real agent, and it held on the dangerous
failure modes; the things worth fixing are in clarity, data, and flow. I turned that into a
failure taxonomy and a set of concrete fixes, redesigned the ordering flow, and built a
runnable eval harness so prompt changes can be measured instead of guessed.

It's a multi-format package on purpose: skim the site in 30 seconds, or go as deep as the code.

## Start here: the interactive site

**Open [`site/index.html`](site/index.html) in a browser.** It's the 30-second front door:
the verdict, a scorecard, the live-test results, the insights, an architecture teardown, and
an interactive before/after redesign of the WhatsApp ordering flow (toggle "Current" vs
"Redesigned"). It's styled to match chataigne.ai.

## The four artifacts

| Artifact | What it is | Open |
|---|---|---|
| **Interactive site** | The main thing. Teardown, scorecard, live findings, and the redesign mockup. | [`site/index.html`](site/index.html) |
| **LaTeX report** | The written write-up: insights, taxonomy, live results, architecture, strategy. | [`report/chataigne-teardown.pdf`](report/chataigne-teardown.pdf) ([`.tex`](report/chataigne-teardown.tex)) |
| **Eval harness** | Runnable: agent reconstruction, 19 scored scenarios, LLM-as-judge, CI gate. | [`eval-harness/`](eval-harness/) |
| **Live red-team** | The probes I ran against the live demo bot, with the full write-up. | [`redteam/findings.md`](redteam/findings.md) |

## The thesis, in a paragraph

I think the core bet is right. Putting ordering inside the app people already have open,
instead of asking them to download another one, is a smart wedge, and grounding an LLM in live
menu data beats fine-tuning. What I'd worry about isn't the idea, it's the reliability and
onboarding layers under the chat. Item existence, prices, and business rules belong in code,
never the model. The POS write path is where the real moat and the real risk both sit. And
because Châtaigne charges per order rather than a commission, order frequency and loyalty are
the revenue lever, which runs straight into WhatsApp's 24-hour messaging window. You de-risk
all of it with disciplined evals and a clean channel boundary. That's the work, and it's why I
built the harness.

## Live test, in one line

I tried to break the things that actually hurt a restaurant: hallucinated items, prompt
injection in a payment loop, social engineering, and allergen liability all held. The things
to fix are a summary whose lines don't visibly add up to the total, a pickup/delivery time
stuck on the restaurant's Paris timezone, replies that stay in French after you switch back to
English mid-conversation, and no way to cancel or change an order in chat once it's confirmed.
Full detail in [`redteam/findings.md`](redteam/findings.md).

## Repo map

```
site/            the interactive teardown + redesign (open index.html)
report/          LaTeX source + compiled PDF
eval-harness/    runnable eval suite (agent, scenarios, judge, runner)
redteam/         live-bot findings + probe plan
review/          product review, failure taxonomy, strategy memo
```

## Running things

- **Site and report:** just open them. The report PDF is prebuilt; recompile with `pdflatex`
  or Overleaf if you edit the `.tex`.
- **Eval harness:** see [`eval-harness/README.md`](eval-harness/README.md). Needs an
  `ANTHROPIC_API_KEY`.
- **Live red-team:** the run is done ([`redteam/findings.md`](redteam/findings.md)). To redo
  it, open the demo at [wa.me/41779276810](https://wa.me/41779276810) and work through
  [`redteam/redteam-plan.md`](redteam/redteam-plan.md).
