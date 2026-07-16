---
title: The prior surveys, and where we disagree with them
section: surveys
order: 10
lede: >-
  Four prior attempts to map this field. A number of our older rows are secondhand from one
  of them, and we disagree with all of them about four things: what quantization is, what
  counts as an objective, whether provenance is a curiosity, and how much a comparison table
  is worth.
papers: [zkml-survey, zkp-decentralized-ml-survey, icme-definitive-guide, modulus-cost-of-intelligence, safetynets, jolt-atlas, zktorch, zkgpt, deepprove, zkml-kang, artemis, lu-et-al, zkllm, zen, fairproof, fairzk, oath, zkaudit, zkprov]
status: reviewed
---

An SoK that does not say where it departs from its predecessors is a literature review.
This page says.

{{ papers:surveys }}

## What each one is

**[[zkml-survey]]**, the ZKP-VML survey (Peng et al.) is the backbone of the historical
half of this site, and we are in its debt. Its Table VII is a timeline of representative
systems from [[safetynets]] onward, and its Tables IV, V and VI give proving time,
verification time and proof size, *with hardware attached*, for training, testing and
inference systems respectively. A number of our older rows are still sourced from it, and each
of those is tagged `numbers_source: survey` and renders with a hollow provenance dot. Several
that started there, [[zen]], [[zkml-kang]], [[zktorch]], have since been promoted to
`primary`, because we obtained the PDF and re-read the table.

It is a survey, not a system: it reports no original benchmarks, so it is excluded from
every plot on this site. That is not a criticism. It is the correct way to use it.

**[[zkp-decentralized-ml-survey]]**, complementary, and older. Its centre of gravity is
decentralized and federated settings rather than the single-prover MLaaS model, which makes
it the better entry point for [the federated cell](/federated/) and a weaker one for
inference.

**[[icme-definitive-guide]]**, a landscape blog, not a peer-reviewed source, and written
by a [[jolt-atlas]] co-author. We flag it `partisan: true` in `papers.yml` and we mean it:
its head-to-head claims favour Jolt Atlas and are recorded here as *attributed claims*, not
as facts. It is genuinely useful for two things, its framing of the overhead progression
across proof-system generations, and as the secondhand source we leaned on for [[zktorch]]'s
LLM numbers until we obtained the paper, its figure and DeepProve's derived one disagreed,
and [[zktorch]]'s own Table 4 has since retired both.

**[[modulus-cost-of-intelligence]]**, the odd one out, and the one that has aged best. It
is not a survey of ML-proving *frameworks*; it is a benchmark of proof *backends* (Groth16,
Gemini, Winterfell, Halo2, Plonky2, zkCNN) run against MLPs. No transformers, no tokens, so
it is deliberately excluded from the LLM throughput graph. What makes it worth reading in
2026 is that it called the shot:

:::quote{src="The Cost of Intelligence" sec="§1.1, Paper Motivation and High Level Summary"}
With respect to both proving time and memory, the GKR-based zkCNN prover appears best suited to tackle large models – even without an optimized implementation.
:::

That was written in January 2023. Three years on, the fastest GPT-2 proving on
[the LLM inference page](/zk-inference/) belongs to sum-check/GKR systems either way you
measure it, [[zkgpt]] and [[jolt-atlas]] on time per forward pass, [[deepprove]] on
throughput. Meanwhile the Plonkish baseline they measure themselves against,
[[zkml-kang]], says in its own Limitations section that a *distilled* GPT-2 is the largest
model it can prove inside its memory budget, and no Groth16 system in this corpus gets near a
transformer at all. Other arithmetizations do reach GPT-2 and past it, [[artemis]] via
commit-and-prove, [[lu-et-al]] via VOLE, [[zktorch]] all the way to LLaMA-2-7B via proof
accumulation, so what Modulus called was the scaling behaviour, not a hard ceiling; the
spread is in the table below. Reading that trend three years before the papers proved it is
still a better track record than any of the taxonomies have.

{{ table:inference }}

---

## Where we disagree

### 1. Quantization is a confounder, not a footnote

The surveys tabulate proving time, verification time and proof size. They do not tabulate
**bit width**, and bit width is a free parameter that trades model accuracy for proving
speed. A system reporting excellent throughput on an aggressively quantized model is not
doing the same job as one reporting worse throughput on a faithful one, and nothing in a
three-column comparison table makes that visible.

This is not a nitpick, and it is not hypothetical. The largest headline throughput gap in
the LLM inference literature is between two systems at *different bit widths*, on
*different context lengths*, proving *different claims* (a full sequence versus a single
forward pass). Three confounds, all pushing the same direction. The protocol contribution
to that gap is smaller than the headline, and **nobody has isolated it.** See
[Quantization](/zk-inference/quantization/), it is the largest single methodological
difference between this SoK and its predecessors.

Our rule follows from it: `quantization.bits: null` is a **finding**, not a hole. Several
of the fastest systems here do not state their bit width. We record the absence rather than
guessing, and a throughput figure with no accuracy claim attached to it is flagged, because
any system can go arbitrarily fast by quantizing to garbage.

### 2. There is a fourth objective

The ZKP-VML survey divides verifiable ML into **training, testing, inference**, one bucket
per pipeline stage, each proving that a *computation* ran as declared. The taxonomy is
sound and it exhausts its axis.

It has no slot for a claim about the *model itself*: that it is fair, that it was trained on
licensed data, that it is not censoring outputs, that it complies with a regulation.
[[fairproof]], [[fairzk]], [[oath]], [[zkaudit]] and the provenance systems are not proving
that a computation was performed correctly, and you cannot reach what they prove by proving
harder that one was. We call that a **fourth objective** and give it
[its own section](/properties/), along with the argument that it is the objective with the
weakest security semantics, because a proof of fairness is only as good as the definition of
fairness it encodes, and that definition is contestable in a way arithmetic is not.

### 3. Provenance is first-class, not adjacent

Related to the above but worth separating. The ZKP-VML survey does name dataset provenance, 
it gives it a future-work subsection, and says the provenance and integrity of training data
"can be just as important as the correctness of the model computation itself", and then
leaves it there: no taxonomy slot, no comparison table, not one system reviewed. We think that
ordering is close to inverted.

Provenance is the claim with an actual customer. Copyright litigation, licensing compliance
and the EU AI Act's data-governance provisions turn on *which data went into this model*,
not on whether the softmax was computed to twelve bits. It is also the **cheaper** claim, 
[[zkprov]] proves which dataset a model was trained on without proving the training
computation at all, and, unlike fairness, it has a fact of the matter behind it. A field
optimising for the hardest technical problem has spent a decade walking past the easiest
valuable one.

### 4. We do not trust comparison tables, including our own

The methodological disagreement, and the one that produced the most work.

Three of the four sources above contain a table comparing systems the authors did not run.
We reproduced those tables, then went to the primary papers, and found discrepancies. One
proof-size figure differs by an order of magnitude between the paper and the survey
([[zkllm]]). Another survey figure is smaller than a single pair of group elements, and that
paper we have not obtained, so it stands in `papers.yml` flagged implausible and unverified
rather than corrected. The difference between those two rows is the point: one we checked, one
we could only mark. Both were invisible from the survey alone.

Where two sources give two numbers, `papers.yml` records both and the disagreement. Where we
could not obtain the primary paper, it records the survey's figure and says so. That file is
load-bearing for this site's credibility: it is the evidence that the numbers here were checked
rather than copied. It is also the reason every figure on this site renders with a provenance
dot, and the reason a number never appears in prose, a number in a paragraph cannot carry its
provenance, and six months later nobody remembers where it came from.

:::debate  Is a partisan blog a citable source?
We cite [[icme-definitive-guide]] and we flag it as partisan, which some readers will find
either too generous or too harsh. Our position: a comparison written by a competitor's
author is evidence, and for a while it was the only cross-check we had on [[zktorch]]'s LLM
performance, until we obtained the paper and read Table 4 ourselves, at which point the
primary figures superseded it (and showed that the secondhand throughput number everyone was
passing around was a category error, not a measurement). That is what a flagged partisan
source is for: it holds a row open until a primary source can close it. The failure would be
to launder it, to quote its numbers without the flag, at which point a marketing claim has
become a survey figure has become a fact. That laundering pipeline is exactly what a
provenance tag exists to break.
:::

:::gap  We are a survey too
Everything above is a criticism we are also exposed to. Many of this site's older rows are
secondhand from [[zkml-survey]] and we have not opened those PDFs. Several entries carry
`authors_verified: false`. The honest position is not that this SoK checked everything, it
is that it **marks what it did not check**, which is a lower bar than it sounds and one the
prior surveys did not clear.
:::
