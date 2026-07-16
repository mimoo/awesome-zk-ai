---
title: Iron
paper: iron
status: reviewed
---

## What is new

Iron is the paper that started private transformer inference, and its contribution is one packing
trick plus a lot of careful protocol plumbing.

**The packing trick.** Cheetah had shown that polynomial multiplication computes an inner product if
you arrange the coefficients in opposite orders. Iron extends that from matrix-*vector* to
matrix-*matrix*: define two encodings `π_L` and `π_R` such that a single polynomial product places
every entry of the output matrix in a distinct coefficient of the result. Where Cheetah must encrypt
each *row* of the left matrix into its own ciphertext, Iron packs the **whole matrix into one**, as
long as `mnk ≤ N`. Transformers are full of high-dimensional matrix-matrix products, so this is
exactly the operation the prior generation had no good protocol for. That is the paper.

The non-linear protocols (Softmax, GELU, LayerNorm) are optimizations *on top of* SIRNN's OT
primitives rather than new constructions: normalize before exponentiating so you only ever need the
negative-exponential protocol; compute `x²` from the cross-term of the shares so you pay half a
multiplication instead of a whole one; fold LayerNorm's scale γ into the *next* layer's weights so
it costs nothing. Each is a factor under 2×. They are craft, not invention, and the paper does not
pretend otherwise.

## What it actually proves

Nothing. That is the point, and it is the axis on which this whole cluster is orthogonal to the
zkML column: **Iron produces no proof.** It computes BERT inference under 2-out-of-2 additive secret
sharing so the server never sees the prompt and the client never sees the weights. A *malicious*
server can compute the wrong function and nobody will ever know, the threat model is explicitly
honest-but-curious.

What it buys, precisely:
- **Privacy against a semi-honest counterparty**, on BERT-Tiny through BERT-Large, on four GLUE
  tasks, over a LAN.
- **Every layer's intermediates are hidden**, including the inputs to the non-linear layers, which
  the contemporaneous THE-X leaks to the client. Iron is right to press this point; it is the
  difference between a privacy claim and a privacy-flavoured one.
- **Nothing about the output.** The paper is explicit that it does not defend against what can be
  inferred from the inference result itself; model extraction is out of scope.

## What to distrust

**The paper contains no absolute performance numbers.** None. Every end-to-end result is a *ratio*
against SIRNN or MP-SPDZ, plotted on a log-scale bar chart. The famous anchor figure that the rest
of this literature (and this repo) quotes for Iron, hundreds of gigabytes of communication and
hours of wall clock for one BERT-base inference, **does not appear in Iron's paper.** It is
[[bolt]]'s reimplementation of Iron, benchmarked on a WAN setting BOLT chose. Iron itself measured
on a LAN. That provenance should travel with the number every time it is used, and the runtime half
of it is a function of BOLT's chosen bandwidth, not of Iron's protocol.

**The bit width is never stated.** Iron's Discussion says: "Iron works with a uniform bitwidth, which
is required to be large enough to accommodate all intermediate values", and then never says what it
is. The accuracy figure sweeps the *fractional scale* from 4 to 16 and shows that scale 12 is needed
to match plaintext exactly, but the ring width ℓ, which is what actually determines the cost of every
OT-based non-linear protocol, is nowhere. This is the same unreported-bit-width problem the
[[zkml-survey]] side of this repo complains about, in a literature that otherwise reports its
parameters well ([[bolt]] and [[ciphergpt]] both state ring width and scale explicitly).

**The accuracy claim is validated on the smallest model only.** "Numerically precise, which preserve
the model accuracy of plaintext" is asserted for the framework; the accuracy figure is measured on
**BERT-Tiny**. Runtime and communication are measured on all four BERT sizes; accuracy is measured on
one, the one where fixed-point error has the fewest layers to accumulate through.

:::audit The accuracy result beats its own baseline, unexplained
From §5.3, verbatim:

> Specifically, the accuracy loss does not exceed 0.3% over all datasets, and surprisingly, Iron
> exceeds the plaintext baseline on MNLI by 0.85%.

"Surprisingly" is doing a lot of work, and the follow-up, "similar results also appear in private
CNN inference", is a citation, not an explanation.

This is the same pattern as [[deepprove]]'s Gemma 3 perplexity beating its own fp32 baseline, and
[[bolt]]'s word-eliminated model beating plaintext on SST-2. **Three papers in this repo now report a
degraded computation outperforming its own reference, and all three wave at it.** Either these
baselines are noisy enough that sub-1% accuracy deltas are meaningless, in which case "preserves
plaintext accuracy" is unfalsifiable and no paper in this cluster has the statistical power to claim
it, or something is wrong. It cannot be a selling point.
:::

**The improvement is concentrated where the cost is not.** Iron's breakdown shows non-linear layers
consuming the overwhelming majority of communication after its optimizations, and Iron's non-linear
protocols improve on SIRNN by less than 2×, while its matmul improves by an order of magnitude. The
paper says this itself and calls it an open problem: "the main bottleneck of our work is the
communication overhead of non-linear layers." It is the same shape as the zkML side, where
[[deepprove]]'s own breakdown puts most of the prover cost in activations, softmax and
requantization. **In both paradigms, matmul is solved and the non-linears are not.** That cross-column
parallel is the most useful thing to take from this paper.
