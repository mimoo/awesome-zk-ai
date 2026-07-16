# AGENTS.md

Guidance for agents (and humans) working in this repo. This is a SoK on **verifiable and
private AI**: zkML, MPC/2PC, FHE, TEE, and sampling-based verification. Read this before you
touch anything. For the fuller contributor contract read [`site/CONTENT.md`](./site/CONTENT.md)
too — this file points at it rather than repeating it.

## What this repo is

- `papers.yml` — structured data on every paper. **The source of truth for every number.**
- `operators.yml` — the 26 LLM forward-pass operators × how each scheme proves each one.
- `references/<cell>/*.pdf` — the PDFs we have actually read. Cells: `proving-inference`,
  `proving-training`, `privacy-inference`, `federated`, `numerics`, `alternatives`, `surveys`.
- `references/citation-graph.yml` — edge `A -> B` means "A's text cites/mentions B".
- `content/<section>/*.md` — prose. **This is what you write.**
- `content/papers/<id>.md` — optional deep-dive appended to an auto-generated paper page.
- `site/build.py` — joins all of the above into `docs/`.
- `site/validate.py` — fails the build when data and prose drift apart.
- `site/sections.yml` — declares sections; maps each `papers.yml` category to a section.
- `docs/` — **GENERATED and GITIGNORED. Never hand-edit.** CI rebuilds and publishes it.
- `README.md` — a summary of the site. It should shrink, not grow; new prose belongs on the
  website, not here.

## 1. Data-first philosophy

The point of this repo is that claims are checkable, so the **data carries the claims** and the
prose interprets them.

- **Numbers live in `papers.yml`, never in prose.** To say "DeepProve hits 174 tok/min" you do
  not type `174` into markdown — you write `{{ perf:deepprove }}` or `{{ table:inference }}` and
  let the generator carry the figure. `validate.py` greps content for bare `tok/min`,
  `x faster`, and similar figures and fails you. The one exception: a figure inside quotation
  marks or inside `:::quote`/`:::audit` — quoting a paper's own claim in order to dispute it is
  the work this SoK exists to do.
- **`null` is an answer, not a hole.** `quantization.bits: null` means the paper does not state
  the bit width. That is a finding. Never guess a null to make a table look complete.
- **Provenance is mandatory.** Every benchmark row needs `numbers_source` (`primary` = we read
  it in the paper; `survey` = secondhand from the ZKP-VML survey; a third-party measurement
  stays `primary` but must carry a `_note` naming who measured it). Never launder a survey
  number into prose as primary. When two sources disagree, record both and write the conflict
  up — do not pick one.
- **`claim_kind` is the most important field.** Two papers both reporting "tokens/minute" may
  prove completely different things: one forward pass, one generated token, or a full generation
  certified end-to-end. A throughput number without a `claim_kind` beside it is not comparable
  to anything.
- **`quantization` is a confounder, not a footnote.** Throughput at 8 bits is not comparable to
  throughput at 16 bits. Always record `quantization.bits` and, where the paper gives it,
  `accuracy_retention`.

## 2. Adding new content: the workflow

The goal is never to trust the abstract. It is to understand what a system *actually* does, so
the entry records what it *proves*, not what it *claims*.

### Step A — pair the paper with its code (both directions)

- **Given a paper**, find its code repo: check the paper for a repo link, the authors' org on
  GitHub, and any artifact/badge link.
- **Given a repo**, find its paper: check the README, `CITATION.cff`, a `/paper` or `/docs`
  dir, and the linked arXiv/ePrint.
- If a paper genuinely has no code, record that — it is also a finding.

### Step B — clone it and RUN A WORKFLOW inside the clone

Clone the repo locally (outside this repo tree — e.g. under your scratchpad). Then **run a
multi-agent Workflow inside that clone** to understand how the system really works — do not skim
the README and move on. The Workflow should establish, from the actual code and configs:

- the real proving / inference pipeline (what circuit or protocol, what gets committed);
- the quantization scheme and **bit width actually used in the benchmarks** (grep configs, not
  the abstract);
- the **threat model** — who is the adversary, what is hidden from whom, what is assumed honest;
- **what it really proves vs. what it claims** — single pass? one token? a full sequence? Is a
  "verifiable inference" number actually simulated or extrapolated?
- who took the reported numbers, on what hardware.

### Step C — record findings across the FOUR files (all four, or the build fails)

1. **`references/<cell>/<id>.pdf`** — the PDF, in the cell dir matching its category.
2. **`papers.yml`** — the entry, with at minimum `numbers_source`, `authors_verified`,
   `quantization.bits` (use `null` + a note if unstated), and `claim_kind`. Numbers you could
   not verify are `null`, not optimistic guesses.
3. **`references/citation-graph.yml`** — the edges this paper adds. Run `python3
   site/citegraph.py` to extract candidates from the PDF, then confirm each edge by eye.
4. **`content/papers/<id>.md`** — the deep-dive note: **what is new**, **what it actually
   proves**, and **what to distrust**. If you have nothing under "what to distrust", you have
   not read the paper carefully enough.

Then wire up the website surface so it is never orphaned: the owning `papers.yml` category must
be claimed by a section in `site/sections.yml`, and a `content/<section>/*.md` page should
reference the paper (via `[[id]]`, `papers:` frontmatter, or a `{{ table:cat }}` /
`{{ chart:… }}` shortcode).

## 3. House prose style

Dry, direct, minimal. Less text, more clarity. State the finding, then let the generated table
prove it. Do not narrate; do not hedge with filler ("it is worth noting", "interestingly",
"arguably", "as we saw above"). One claim per sentence. Lead each section with its conclusion.

Move educative or expanding material **out of the body and into an admonition**, so the main
line stays a clean spine of claims:

- `:::gap` — a boundary of knowledge: nobody has done X, no paper reports Y, a claim is scoped
  narrower than it sounds.
- `:::debate` — two sources or two readings genuinely disagree and this SoK deliberately does
  not resolve it.
- `:::audit` — what to distrust: where a bug hides, a security surface, an unverified vendor
  claim, a soundness question.
- `:::quote{src="…" sec="…"}` — **verbatim** from a PDF in `references/`. If you cannot
  copy-paste it out of `pdftotext`, paraphrase instead — do not use `:::quote`.

Use `[[wikilinks]]` to paper ids on first mention, and shortcodes (`{{ table:… }}`,
`{{ perf:… }}`, `{{ chart:… }}`, `{{ papers:… }}`, `{{ coverage }}`) instead of copied figures.

## 4. Verify before committing

- `make site` — rebuild `docs/`. Must succeed.
- `make check` — the integrity gate. Must pass. It enforces: every `papers.yml` category is
  owned by a section; citation-graph endpoints are real ids; content frontmatter sections and
  `papers:`/`[[…]]` ids exist; **no hardcoded numbers in prose**; provenance discipline on
  `papers.yml`; and it warns about PDFs held but not written up.
- **Never hand-edit `docs/`** — it is generated and gitignored; your edit is not even tracked.
- Commit or push only when asked. `make check` green is the bar for "done".

## Checklist for adding a paper

1. Paired the paper with its code repo (or recorded that there is none).
2. Cloned the repo and ran a Workflow inside it to learn how it actually works.
3. Established the real pipeline, quantization bit width, threat model, and proves-vs-claims.
4. `references/<cell>/<id>.pdf` added.
5. `papers.yml` entry with `numbers_source`, `authors_verified`, `quantization.bits`,
   `claim_kind` — `null` where the paper is silent, never a guess.
6. `references/citation-graph.yml` edges added via `citegraph.py` and confirmed by eye.
7. `content/papers/<id>.md`: what's new, what it proves, what to distrust.
8. Website wiring: section owns the category, a page references the paper, no orphan.
9. `make site && make check` both pass; `docs/` left untouched.
