---
title: How to read this
section: start
order: 10
lede: >-
  A SoK is only worth as much as its worst-sourced number. This one tags every figure with
  where it came from, and tells you what it has not read.
status: reviewed
---

## What this is claiming

The field is usually presented as a list of systems, each with a headline number, sorted by
that number. That presentation is close to useless, because **the numbers are not measuring
the same thing.** One system proves a single forward pass. Another proves one token. Another
proves a whole multi-token generation and calls the result a throughput. Reported side by
side, the fastest-looking system is often the one making the weakest claim.

So the organising question here is not *how fast* but *what is actually being proven*, and
underneath that, *what is being assumed rather than proven*. The quantization scheme, the
calibration set, the tokenizer, and the commitment to the model weights are all load-bearing,
and all routinely left outside the proof.

## The three rules

**Numbers live in `papers.yml`, never in prose.** Every figure on this site is rendered from
that file at build time. If you see a benchmark, it came from the data, and it carries a dot
telling you where the data came from. Prose that hardcodes a figure is rejected by the build,
because a number typed into a sentence is a number that will silently contradict the dataset
the first time the dataset is corrected.

**`null` is an answer.** When a paper does not state its bit width, we record `bits: null` and
say so. We do not fill it in with a plausible value. A missing number is a finding about the
literature, and in this literature, it is a very common one.

**Provenance is not a footnote.** A figure we read in the paper, a figure we took from someone
else's survey, and a figure from a vendor blog post are three different kinds of object. They
are marked differently everywhere they appear, and where a survey disagrees with the primary
paper, both numbers are recorded in `papers.yml` and the conflict is written up there
rather than quietly resolved in favour of one.

:::gap What this site does not do
It does not rank the systems. Given how differently they define their claims, a single ranking
would be a lie with a number attached. The [throughput chart](zk-inference/index.html) plots
them together because that comparison is the one everybody wants, and then tells you, per
point, why it does not mean what it looks like.
:::

## Quantization is the confounder

Proving cost depends on the bit width of the quantized model, and the papers do not agree on a
bit width, or, very often, state one at all. A system reporting excellent throughput at 8 bits
is not comparable to one reporting throughput at 16, and a throughput number with no accuracy
claim attached is not a meaningful data point at all. This is the single most common way to
draw a wrong conclusion from this literature, so it gets
[its own page](zk-inference/quantization.html).

## What we have and have not read

The [papers index](papers/index.html) marks, per entry, whether we hold the PDF and whether
anyone has actually read it and written down what to distrust about it. Most entries are
indexed but not deeply read; the [backlog](backlog/index.html) lists papers we know exist and
have not touched. Both are shown on purpose. A SoK that hides its own coverage gaps is telling
you it is complete, which it never is.

## Two literatures that do not talk

The clearest structural finding so far is in the [citation graph](graph/index.html). The
verifiability papers and the privacy papers are fighting the *same operators*, GELU, Softmax,
LayerNorm are the expensive, awkward ones in both worlds, with entirely different tools. And
they do not cite each other. Not rarely: **not at all.** Two research communities working the
two columns of the same table, in separate rooms.
