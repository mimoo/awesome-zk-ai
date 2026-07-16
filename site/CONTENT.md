# How to write content for the zkAI SoK

Read this before adding a page. It is the contract the build enforces.

## Where things live

```
papers.yml                  structured data. SOURCE OF TRUTH for every number.
operators.yml               the LLM forward-pass operators, and how each scheme proves each one.
references/<cell>/*.pdf     the PDFs we have actually read.
references/citation-graph.yml   edge A -> B means "A's text cites/mentions B".
content/<section>/*.md      prose. THIS is what you write.
content/papers/<id>.md      optional deep-dive appended to an auto-generated paper page.
site/sections.yml           the left-menu sections (cell axis) and top-menu paradigms.
site/vendor/                KaTeX. Source, not output -- copied into docs/ on each build.
site/build.py               joins them all -> docs/
site/validate.py            fails the build when they drift apart.
AGENTS.md                   how to add a paper end-to-end (find repo, clone, run a Workflow).
docs/                       GENERATED, and GITIGNORED. Never hand-edit; it is not even in
                            the repo. CI builds it and publishes it to GitHub Pages.
```

The hard rule: **a number lives in `papers.yml`, never in prose.** If you want to say
"DeepProve hits 174 tok/min", you do not type `174` into a markdown file. You write
`{{ perf:deepprove }}` or link the paper and let the generated table carry the figure.
Prose that hardcodes a benchmark number is how a SoK starts lying six months later.
`validate.py` greps content for bare `tok/min`, `tokens/min`, `x faster` and similar
figures and will fail you.

The rule is about *asserting*, not *mentioning*. Quoting a paper's own claim — its
"20–60× faster than the state of the art" — in order to dispute it is exactly the work
this SoK exists to do. So figures inside quotation marks, and inside `:::quote` and
`:::audit` callouts, are exempt. Everywhere else, use a shortcode.

## Voice: dry, direct, one claim per sentence

Less text, more clarity. The reader is skimming for the finding; give it to them and let the
generated table prove it. The rules are enforceable — a reviewer should be able to point at a
line, not argue taste:

- **Lead each section with its conclusion,** not its setup.
- **One claim per sentence.** Two independent claims joined by "and" → split them.
- **Present tense, active voice.** "Iron needs 280 GB", not "it was found that Iron would require".
- **Cut hedges and throat-clearing:** "it is worth noting", "interestingly", "arguably", "as we
  saw above", "in order to".
- **Paragraphs of four sentences or fewer.**

The one mechanism behind all of it — **the body/callout contract:** the body is a spine of
claims a hurried reader follows top to bottom. The moment a paragraph stops asserting the page's
claim and starts *teaching, warning, quoting, or hedging*, it leaves the body and becomes a
callout. A 40-line block explaining one system, or a four-point lecture on quantization sitting
inline, is the same failure: educative material left in the spine.

## Frontmatter

Every `content/**/*.md` starts with:

```yaml
---
title: What is actually being proven
section: zk-inference        # must match a key in site/sections.yml
order: 20                    # sidebar order within the section; gaps of 10 are conventional
lede: >-
  Three systems report a throughput number. They are measuring three different
  things, and only one of them is an end-to-end claim.
papers: [deepprove, zkgpt, zkllm]   # ids from papers.yml. Validated. Renders a "papers on this page" rail.
status: draft                # draft | reviewed. draft renders a banner.
# paradigm: tee              # OPTIONAL. Overrides the section's default top-menu bucket for
#                            # this page only -- used when one section spans two paradigms
#                            # (see content/alternatives/tees.md). Almost never needed.
---
```

`papers:` is not decoration. It builds the reverse index — each paper page lists every
essay that discusses it — so a paper can never be silently orphaned.

## Body

Standard markdown, plus:

**Math** — `$x = s(\bar{x}-z)$` inline, `$$ ... $$` display. KaTeX, vendored, renders
client-side. Display math gets the cyan left-rule automatically.

**Paper links** — `[[deepprove]]` renders the paper's name, linked to its page, and
registers a cross-reference. Use it constantly. An unknown id fails the build.

**Callouts** — these map onto the CSS already in the design system:

```
:::gap  Nobody has done this
Not one of the five LLM systems states a bit width *and* an accuracy delta.
:::

:::debate  Is 12 bits honest?
DeepProve reports 174 tok/min at 12 bits; zkGPT reports 2.75 at 16. The 63x gap
is not bit-width-normalised, and the two are not proving the same claim.
:::

:::audit  Audit surface
The lookup-table range is fixed at preprocessing. An activation outside the
calibrated range is not merely inaccurate -- it is unprovable.
:::

:::quote{src="DeepProve" sec="§5, Experiments"}
We run inference on the GPT-2 and Gemma 3 models using DeepProve using 12-bit
quantization level.
:::

:::intuition  Why a lookup is cheap
A range check asks "is x in [0, 2^b)?". Instead of proving it arithmetically, commit a
table of every legal value and prove x is one row of it. The prover cost is the table
size, not the bit width -- which is why lookups win exactly where bit-decomposition loses.
:::

:::note
Cheetah and SIRNN are the two OT-based building blocks nearly every 2PC paper here reuses.
:::
```

Quotes must be **verbatim from the PDF in `references/`**. If you cannot copy-paste it
out of `pdftotext`, you do not get to use `:::quote`. Paraphrase in your own prose instead.

Pick the callout by its **trigger**, not by vibe. The four adversarial ones are the point of
the SoK; `:::intuition` is the one non-adversarial slot, so teaching lands there instead of
bloating the body; `:::note` is a quiet true aside.

| Callout | Colour | Use it when… | Not for |
|---|---|---|---|
| `:::gap` | rose, dashed | a **boundary of knowledge**: nobody has done X, no paper reports Y, a claim is scoped narrower than it sounds | a thing to distrust (audit); a disagreement (debate) |
| `:::debate` | violet | **two sources or two readings genuinely disagree** and this SoK does not resolve it | one-sided criticism (audit) |
| `:::audit` | amber | **what to distrust**: a bug's hiding place, a security surface, an unverified vendor claim, a soundness question | general teaching (intuition); a scope limit (gap) |
| `:::intuition` | cyan | **educative expansion**: the mental model, why a mechanism works, background a reader can skip | anything adversarial |
| `:::note` | grey | a **true tangential aside** — a definition, a pointer | anything load-bearing; if it matters, it belongs in the body |
| `:::quote` | rule | **verbatim from a PDF** in `references/`, to hold a paper to its own words | paraphrase; your own summary |

Rule of thumb: **gap** = "here be dragons", **debate** = "we don't know which", **audit** =
"don't trust this", **intuition** = "here's the picture", **note** = "by the way", **quote** =
"in their words". (`:::warning` does not exist on purpose — "watch out" is what `:::audit`
already means.)

**Shortcodes** — the generator injects live data from `papers.yml`, so it can never go stale:

| Shortcode | Renders |
|---|---|
| `{{ table:inference }}` | the benchmark table for a `papers.yml` key |
| `{{ table:inference cols=model,params,tokens_per_minute,quantization.bits }}` | a chosen projection |
| `{{ chart:throughput }}` | throughput vs. params scatter, coloured by proof system |
| `{{ chart:timeline }}` | proving time for GPT-2 over time |
| `{{ chart:citations }}` | the citation graph, filtered to this page's `papers:` |
| `{{ perf:deepprove }}` | inline headline figure for one system, with provenance dot |
| `{{ papers:inference }}` | card grid of every paper under a `papers.yml` key |
| `{{ coverage }}` | the operator x scheme coverage matrix from `operators.yml` |

## Provenance is a first-class citizen

Every figure the generator renders carries its `numbers_source` as a coloured dot:
filled = `primary` (we read it in the paper), hollow = `survey` (secondhand), dashed =
`blog`/vendor claim. Do not launder a survey number into prose as if it were primary.

When two sources disagree, do not pick one. Record both in `papers.yml` and write the
conflict up in `content/soundness/conflicts.md`.

`null` in `papers.yml` means *the paper does not report this*. That is a finding, not a
hole to fill. Never guess a null.

## The contract for adding a paper

An agent that reads a new PDF touches **four** files. All four, or the build fails:

1. `references/<cell>/<id>.pdf` — the PDF itself.
2. `papers.yml` — the entry, with `numbers_source`, `authors_verified`, and
   `quantization.bits` (use `null` + a note if unstated — that is the honest answer).
3. `references/citation-graph.yml` — which of our other papers it cites. Run
   `python3 site/citegraph.py` to extract candidates, then confirm by eye.
4. `content/papers/<id>.md` — the deep-dive: **what is new**, **what it actually proves**
   (single pass? one token? a whole sequence?), and **what to distrust**. If you have
   nothing to say under "what to distrust", you have not read the paper carefully enough.

Then `make site && make check`. For the full paper↔repo procedure (find the code, clone it,
run a Workflow to learn how it really works before you write the entry), see
[`../AGENTS.md`](../AGENTS.md).

## Checklist before `make check`

Read your page top to bottom and confirm:

```
[ ] Every section's FIRST sentence states its conclusion, not its setup.
[ ] One claim per sentence. Two independent claims joined by "and" -> split them.
[ ] No number in body prose. Use {{ perf }} / {{ table }} / a [[paper]] link, or move the
    number into a :::quote or :::audit (those are rule-exempt).
[ ] Body = the claim; callout = the expansion. Any paragraph that teaches, warns, quotes,
    or hedges belongs in a callout, not the spine.
[ ] Each callout matches its trigger: gap=scope limit, debate=unresolved conflict,
    audit=distrust-this, intuition=mental model, note=aside, quote=verbatim-from-PDF.
[ ] Every paper is a [[wikilink]] on first mention.
[ ] Cut hedges: "it is worth noting", "interestingly", "arguably", "as we saw above".
[ ] Paragraphs are four sentences or fewer.
[ ] Your paper page says what to DISTRUST. If it can't, you haven't read it closely enough.
```
