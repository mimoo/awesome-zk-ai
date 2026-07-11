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
site/build.py               joins them all -> docs/
site/validate.py            fails the build when they drift apart.
docs/                       GENERATED. Never hand-edit. Your edit will be overwritten.
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
```

Quotes must be **verbatim from the PDF in `references/`**. If you cannot copy-paste it
out of `pdftotext`, you do not get to use `:::quote`. Paraphrase in your own prose instead.

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

Then `make site && make check`.
