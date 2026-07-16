---
title: ZKML
paper: zkml-kang
status: reviewed
---

## What is new

ZKML is not a protocol. It is an **optimizing compiler from TensorFlow to halo2**, and its thesis
is that in a Plonkish system the *encoding* of an operation, not the choice of proof system,
dominates cost, a claim it backs with an ablation showing the same model varying by more than an
order of magnitude across gadget choices.

**The insight that carries the paper is that the right encoding is a global property, not a local
one.** A halo2 circuit is a grid whose rows must be a power of two, so rows and columns trade
against each other, and a gadget that is cheap in isolation can be ruinous in context. The paper's
worked example is a single ReLU: implement it as a lookup table (two cells, but three new columns
and a table with `2^b` rows), as a four-row bit decomposition (one column), or by reusing arithmetic
constraints already present in the grid (thirty-two rows, no new columns). In their toy circuit the
*third* is cheapest, but at `2^18` ReLUs the lookup table wins by a wide margin. There is no
locally correct answer, so ZKML builds a cost model over `nFFT`/MSM counts and searches the layout
space instead of picking an encoding a priori.

**The gadget set is what actually unlocks non-CNN models**, and it is the part worth reading. Prior
work optimized convolutions, fully-connected layers and ReLU, which is exactly the set of operations
a CNN needs and nothing else. ZKML adds variable (rounded) division, a maximum gadget, a scaled
exponential, and, composed from those three, a **numerically careful softmax**. The softmax is the
nice piece of engineering: shift by the max for stability (standard), but then note that naive
integer division of `e^{x_i}` by `Σ e^{x_j}` rounds every entry but one to zero, so they scale the
*numerator* by the scale factor rather than dividing the sum by it, preserving precision. Softmax,
`BatchMatMul` and general pointwise non-linearities are precisely the layers that ZEN, vCNN and
[[zkcnn]] do not have, and they are what a transformer or a recommender is made of.

**Linear layers use Freivalds' algorithm**: compute `B = WA` outside the circuit and verify it by
checking `Br = WAr` for a random `r`, turning an `O(n^3)` in-circuit multiplication into an `O(n^2)`
check. This is the single most soundness-critical design decision in the system, and it is discussed
below.

## What it actually proves

**One forward pass of one fixed-function model, with private weights and a public architecture.**
There is no autoregression, no generation, and no accuracy claim for the language model.

Three scoping facts that the downstream literature routinely drops:

**The "GPT-2" everyone benchmarks against is a *distilled* GPT-2.** ZKML's own model table lists it
at well under the 124M parameters that our inference table and the survey attribute to it, with a
FLOP count that is what a **single token** through that model costs. Every "faster than ZKML on
GPT-2" claim in this repo, [[zkgpt]]'s, [[zktorch]]'s, is a comparison against a distilled model,
proving one token, and none of them say so. This is a data-quality problem, not a criticism of ZKML,
which is perfectly clear about what it ran.

**Autoregression is out of scope by construction.** The paper states that ZKML supports no branching
and no variable-length loops, so NLP models require fixed-length inputs and loops are unrolled. A
generation of `n` tokens is `n` separate proofs, and the paper never claims otherwise.

**What is assumed rather than proven** is stated with unusual honesty, and the two admissions below
are load-bearing:

:::quote{src="ZKML" sec="§4.4, Limitations"}
ZKML requires that the model architecture (but not weights) is revealed.
:::

:::quote{src="ZKML" sec="§4.4, Limitations"}
Another major concern for all ZK-SNARKs is that the representation of the computation within the
ZK-SNARK is equivalent to the original computation (i.e., correctness of the circuit). A formal
proof of correctness is outside the scope of this work.
:::

The second is the compiler-correctness gap that every system in this cell has and only this one
names. ZKML's soundness is halo2's soundness *plus* the unproven assertion that the compiled circuit
computes the model.

**Nothing in the paper binds the private weights to a published model.** The motivating figure is a
user checking that their feed came from Twitter's *real* recommender `M` and not a substitute `M'`, 
but a halo2 proof with the weights in advice columns establishes only "the prover knows *some*
weights that, in this architecture, produce this output." Pinning them to a specific committed model
requires a weight commitment carried as a public input, and the paper specifies neither the contents
of its instance columns nor any commitment scheme over the weights. To its credit, §2 says up front
that all of its applications "must be combined with other techniques to be fully secure", but the
missing piece is not exotic, it is the entire premise of the use case, and it is exactly the cost
that [[artemis]] later measures and attacks.

## What to distrust

**The Freivalds randomness is where the soundness of every linear layer lives, and the paper does
not say where it comes from.** The requirement is stated exactly right:

:::quote{src="ZKML" sec="§6.1, Linear layers"}
The random vector 𝑟 must be generated after the matrix and results are committed.
:::

In an interactive protocol that is free. In a non-interactive halo2 circuit it is not: `r` has to be
derived from a challenge drawn *after* the commitments to `W`, `A` and `B`, which means a multi-phase
circuit with a real challenge API. The paper never mentions how this is done. If `r` is a compile-time
constant, or read from a fixed instance column, or otherwise available to the prover before it commits
to `B`, then a malicious prover chooses `B ≠ WA` in the kernel of the check and the matmul, the bulk
of the model, is unsound. We are **not** claiming that ZKML does this wrong; we are saying that the
paper does not contain the sentence that would tell you, and that this is the first thing to read the
code for. It is also the reason this system's linear layers have *statistical*, not perfect,
soundness, which no summary of ZKML we have seen mentions.

**Do not cite ZKML as a proof of training.** Its model-support table carries a checkmark for "CNN
training", but §4.4 says plainly that the authors do not focus on proofs of training, and no training
benchmark appears anywhere in the evaluation. The checkmark is a capability claim with no measurement
behind it.

**It inherits halo2 wholesale**, including the Halo2 query-collision bug, the query-collision bug class
was disclosed to ezkl and the halo2 forks, and ZKML sits on the same backend. Combined with the
authors' own admission that circuit correctness is unproven, ZKML's attack surface is "every
under-constrained gadget in a 43-layer compiler", which is exactly the class the SNARK-vulnerability SoK
identifies as the most common and most severe.

**The lookup-table range is bounded by the grid.** The paper notes that a table can be at most as
long as the circuit, so the range of inputs to a non-linearity *constrains the precision of the
fixed-point representation*. That is the quantization-as-audit-surface question in its sharpest form:
the admissible activation range is fixed at compile time by a layout decision, and the paper reports
accuracy only on MNIST and CIFAR classification. There is no perplexity number, and no accuracy
number of any kind, for the distilled GPT-2.

:::audit  The ZKML-on-GPT-2 "conflict" is probably not a conflict
`papers.yml` and the README record a disagreement: the survey reports 3652 s / 18.70 s / 28 KB for
ZKML on GPT-2, while [[zkgpt]]'s Table 3 measures 4026 s / 12.1 s / 7.8 KB. Having read the paper, the
survey's figures are exactly ZKML's Table 6, its **KZG** backend. ZKML also ships an **IPA** backend,
whose Table 7 row for GPT-2 (3949.60 s proving, 11.98 s verification) tracks zkGPT's proving and
verification times closely. The most economical explanation is that zkGPT benchmarked the IPA build
and the survey read the KZG table, i.e. the two sources measured two different backends of the same
system rather than contradicting each other. The proof sizes still do not line up, so this is a strong
hypothesis and not a resolution, but "KZG vs IPA" should be checked before anyone records a third
conflicting number.
:::

**Credit where due.** ZKML is the honest baseline of this whole cell: it states its limitations in a
section actually called Limitations, it names the compiler-correctness gap that its successors do not,
it reports accuracy on the models where accuracy is measurable, and its numbers reproduce. The
problems above are the problems of a compiler paper doing a compiler paper's job, the systems that
cite it as a punching bag have mostly not matched its candor.
