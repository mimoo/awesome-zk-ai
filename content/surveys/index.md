---
title: The prior surveys, and where we disagree with them
section: surveys
order: 10
lede: >-
  Four prior attempts to map this field. We take most of our older numbers from one of
  them, and we disagree with all of them about three things: what quantization is, what
  counts as an objective, and how much a comparison table is worth.
papers: [zkml-survey, zkp-decentralized-ml-survey, icme-definitive-guide, modulus-cost-of-intelligence, safetynets, jolt-atlas, zktorch, fairproof, fairzk, oath, zkaudit, zkprov]
status: draft
---

An SoK that does not say where it departs from its predecessors is a literature review.
This page says.

{{ table:surveys }}

## What each one is

**[[zkml-survey]]** — the ZKP-VML survey (Peng et al.) is the backbone of the historical
half of this site, and we are in its debt. Its Table VII is a timeline of representative
systems from [[safetynets]] onward, and its Tables IV, V and VI give proving time,
verification time and proof size — *with hardware attached* — for training, testing and
inference systems respectively. Most of the pre-2024 entries here are sourced from it, and
every one of them is tagged `numbers_source: survey` and renders with a hollow provenance
dot.

It is a survey, not a system: it reports no original benchmarks, so it is excluded from
every plot on this site. That is not a criticism. It is the correct way to use it.

**[[zkp-decentralized-ml-survey]]** — complementary, and older. Its centre of gravity is
decentralized and federated settings rather than the single-prover MLaaS model, which makes
it the better entry point for [the federated cell](/federated/) and a weaker one for
inference.

**[[icme-definitive-guide]]** — a landscape blog, not a peer-reviewed source, and written
by a [[jolt-atlas]] co-author. We flag it `partisan: true` in `papers.yml` and we mean it:
its head-to-head claims favour Jolt Atlas and are recorded here as *attributed claims*, not
as facts. It is genuinely useful for two things — its framing of the overhead progression
across proof-system generations, and as one of two secondhand sources for [[zktorch]]'s LLM
numbers (the two sources disagree; both values are recorded in `papers.yml`).

**[[modulus-cost-of-intelligence]]** — the odd one out, and the one that has aged best. It
is not a survey of ML-proving *frameworks*; it is a benchmark of proof *backends* (Groth16,
Gemini, Winterfell, Halo2, Plonky2, zkCNN) run against MLPs. No transformers, no tokens, so
it is deliberately excluded from the LLM throughput graph. What makes it worth reading in
2026 is that it called the shot:

:::quote{src="The Cost of Intelligence" sec="Abstract"}
With respect to both proving time and memory, the GKR-based zkCNN prover appears best suited to tackle large models – even without an optimized implementation.
:::

That was written in January 2023. Every system on [the LLM inference page](/zk-inference/)
that reaches GPT-2 scale or beyond is a sum-check/GKR system. The Plonkish and Groth16
approaches did not get there. Modulus benchmarked the backends and read the trend correctly
three years before the papers proved it, and that is a better track record than any of the
taxonomies have.

---

## Where we disagree

### 1. Quantization is a confounder, not a footnote

The surveys tabulate proving time, verification time and proof size. They do not tabulate
**bit width** — and bit width is a free parameter that trades model accuracy for proving
speed. A system reporting excellent throughput on an aggressively quantized model is not
doing the same job as one reporting worse throughput on a faithful one, and nothing in a
three-column comparison table makes that visible.

This is not a nitpick, and it is not hypothetical. The largest headline throughput gap in
the LLM inference literature is between two systems at *different bit widths*, on
*different context lengths*, proving *different claims* (a full sequence versus a single
forward pass). Three confounds, all pushing the same direction. The protocol contribution
to that gap is smaller than the headline, and **nobody has isolated it.** See
[Quantization](/zk-inference/quantization/) — it is the largest single methodological
difference between this SoK and its predecessors.

Our rule follows from it: `quantization.bits: null` is a **finding**, not a hole. Several
of the fastest systems here do not state their bit width. We record the absence rather than
guessing, and a throughput figure with no accuracy claim attached to it is flagged, because
any system can go arbitrarily fast by quantizing to garbage.

### 2. There is a fourth objective

The ZKP-VML survey divides verifiable ML into **training, testing, inference** — one bucket
per pipeline stage, each proving that a *computation* ran as declared. The taxonomy is
sound and it exhausts its axis.

It has no slot for a claim about the *model itself*: that it is fair, that it was trained on
licensed data, that it is not censoring outputs, that it complies with a regulation.
[[fairproof]], [[fairzk]], [[oath]], [[zkaudit]] and the provenance systems are not proving
that a computation was performed correctly, and you cannot reach what they prove by proving
harder that one was. We call that a **fourth objective** and give it
[its own section](/properties/) — along with the argument that it is the objective with the
weakest security semantics, because a proof of fairness is only as good as the definition of
fairness it encodes, and that definition is contestable in a way arithmetic is not.

### 3. Provenance is first-class, not adjacent

Related to the above but worth separating. The surveys treat dataset provenance — if they
treat it at all — as a curiosity next to the "real" work of proving computations. We think
it is close to inverted.

Provenance is the claim with an actual customer. Copyright litigation, licensing compliance
and the EU AI Act's data-governance provisions turn on *which data went into this model*,
not on whether the softmax was computed to twelve bits. It is also the **cheaper** claim —
[[zkprov]] proves which dataset a model was trained on without proving the training
computation at all — and, unlike fairness, it has a fact of the matter behind it. A field
optimising for the hardest technical problem has spent a decade walking past the easiest
valuable one.

### 4. We do not trust comparison tables, including our own

The methodological disagreement, and the one that produced the most work.

Three of the four sources above contain a table comparing systems the authors did not run.
We reproduced those tables, then opened the primary papers, and found four discrepancies —
including one proof-size figure that differs by an order of magnitude between a paper and a
survey, and one that is smaller than a single pair of group elements. Every one of them was
invisible from the survey alone.

They are all documented, with both values, in `papers.yml` — which is load-bearing for this
site's credibility: it is the evidence that the numbers here were checked rather than copied,
recording both figures and the disagreement wherever two sources conflict. It is also the reason every figure on this site
renders with a provenance dot, and the reason a number never appears in prose — a number in
a paragraph cannot carry its provenance, and six months later nobody remembers where it
came from.

:::debate  Is a partisan blog a citable source?
We cite [[icme-definitive-guide]] and we flag it as partisan, which some readers will find
either too generous or too harsh. Our position: a comparison written by a competitor's
author is evidence, and excluding it would leave [[zktorch]]'s LLM performance with *no*
source at all rather than two conflicting ones. The failure would be to launder it — to
quote its numbers without the flag, at which point a marketing claim has become a survey
figure has become a fact. That laundering pipeline is exactly what a provenance tag exists
to break.
:::

:::gap  We are a survey too
Everything above is a criticism we are also exposed to. Many of this site's older rows are
secondhand from [[zkml-survey]] and we have not opened those PDFs. Several entries carry
`authors_verified: false`. The honest position is not that this SoK checked everything — it
is that it **marks what it did not check**, which is a lower bar than it sounds and one the
prior surveys did not clear.
:::
