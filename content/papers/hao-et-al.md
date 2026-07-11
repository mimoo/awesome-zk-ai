---
title: Hao et al.
paper: hao-et-al
status: reviewed
---

## What is new

One substitution, applied systematically, on top of [[mystique]]'s substrate.

Hao et al. diagnose that in [[mystique]] the non-linear layers dominate — not because non-linearity
is inherently expensive, but because of *how* Mystique reaches it. Every non-linear function forces
an arithmetic→Boolean conversion (`zk-edaBits`) followed by evaluation in a Boolean circuit, where
exponentiation, division and reciprocal square root each cost thousands of multiplication gates.
Their fix is to delete both steps: **evaluate the non-linear function by table lookup, over
arithmetic values, never leaving 𝔽ₚ.**

The obvious objection is that a faithful table for `y = f(x)` over a 61-bit prime field has ≈2⁶¹
entries. The answer is **digit decomposition**: split the input into a constant number of small
digits (5–12 bits), look each digit up in its own small table, and rebuild the function from the
pieces with purpose-built comparison, truncation and most-significant-non-zero-bit protocols. From
those blocks they compose exponentiation, division and reciprocal square root, and from *those*,
ReLU, sigmoid, GELU, softmax, maxpooling and normalization.

Two details are worth the SoK's attention.

**The lookup is instantiated from ZK-ROM, not from a polynomial lookup argument.** For `N` lookups
into a size-`T` public table the cost is `T + 2N` multiplications, so:

:::quote{src="Hao et al." sec="§3.5, ZK proofs of table lookup from ZK-ROM"}
considering N ≫ T , the amortized computation complexity per lookup is 2 multiplications.
:::

They explicitly considered and rejected the lookup arguments the rest of this section is built on:
they re-ran Caulk and found it far slower per amortized access at the same table size, and they
argue Lasso's decomposability requirement does not fit their tables. This is one of very few places
in the literature where someone benchmarks a folklore choice instead of inheriting it.

**The convergent evolution is the real finding.** Strip the cryptography and Hao et al.'s recipe is
the same recipe as the sum-check lineage: decompose a wide value into narrow digits, put the digits
in small tables, and reassemble. That is DeepProve's chunked requantization, zkLLM's base-`b` digit
decomposition inside `zkAttn`, and Jolt Atlas's prefix-suffix decomposition — arrived at
independently, from a VOLE starting point, with ZK-ROM standing in for LogUp. Their softmax even
subtracts the row max before exponentiating, exactly as [[zkllm]]'s shift-invariance trick does, and
for the same reason: it bounds the input range so the table can be small. Four systems, four
cryptographic substrates, one idea.

## What it actually proves

**That a large batch of evaluations of a single non-linear function was computed correctly — in
isolation, with no model around it.**

This is a *component supplier*, not a competitor, and the distinction is the whole point of the
paper's evaluation and the whole risk in reading it.

**There is no model.** The evaluation tables are indexed by *function* — ReLU, sigmoid, GELU,
softmax, maxpooling, normalization — not by network. No CNN is proven end to end, no transformer is
proven end to end, and consequently **no accuracy number appears anywhere in the paper**, for any
model, at any precision.

**It inherits [[mystique]]'s proof object wholesale**, and therefore all of its limits:

:::quote{src="Hao et al." sec="§3.3, Zero-knowledge proofs"}
in our implementation, we use the recent VOLE-based interactive designated-verifier ZK proofs
[56–59] due to their fast prover time and small memory footprint.
:::

Interactive, designated-verifier, one verifier at a time, communication rather than a proof.
Everything the [[mystique]] note says about what that costs you applies here unchanged. A reader who
sees the headline speedup and files this under "fast zkML" has mis-filed it: it is fast
*designated-verifier* zkML, and it is not competing with [[deepprove]] or [[jolt-atlas]] for the same
job.

**The figures are amortized over a batch, and the batch size is load-bearing.** The default
configuration is 10⁵ instances of the function at fixed-point scale 12. The `O(1)`-multiplications
claim is explicitly an amortized claim requiring `N ≫ T` — with a 2¹²-entry table, the `T` term is
only negligible because `N` is large. This is a fair assumption for ML (they note a single ResNet-50
layer contains hundreds of thousands of ReLUs) but it is an assumption, and the per-operator rows in
`papers.yml` are batch figures, not the cost of one ReLU.

**So what does proving an operator in isolation tell you about proving a model?** Two of the three
things you need, and not the third.

- *It does tell you the seam is gone.* The cost Hao et al. removes — arithmetic↔Boolean conversion —
  is precisely the boundary between a model's linear and non-linear layers. That is the one component
  whose isolated speedup you would expect to survive composition, because the seam is exactly what a
  real model does over and over.
- *It does not tell you the composed cost.* No end-to-end run means the linear layers, the
  layer-to-layer plumbing, and the real shapes are unmeasured. The reported softmax is over a
  10-element vector and the normalization over 16 — CIFAR-class shapes. An LLM's softmax is over a
  sequence and its LayerNorm over the model dimension; the digit-decomposition cost model is
  sensitive to input range, and those ranges are not the ones tested.
- *It does not tell you the accuracy cost at all* — see below, because that is the one that matters.

## What to distrust

:::audit The paper undoes Mystique's accuracy mechanism and never measures the damage
This is the central thing to distrust, and it is a gap rather than an error.

[[mystique]] evaluates non-linearities as **IEEE-754 single-precision floating-point circuits**, and
says why — it was worried about error amplification through a deep network:

> This could particularly be a concern for deep neural networks with hundred of layers where the
> error could propagate and get amplified. *(Mystique, §7.2)*

It then backs the worry with the best accuracy evaluation in this cluster — the full CIFAR-10 test
set, a reported accuracy delta, and the ℓ₂ distribution of the error.

Hao et al. **replaces those float circuits with fixed-point digit tables at scale 12** — and reports
no accuracy evaluation whatsoever. Not on CIFAR-10, not on a language model, not even a numerical
error bound against the float reference.

It is worse than a missing table, because the approximations are *tunable and set to the cheapest
setting*: division runs with `I = 0` refinement iterations and reciprocal square root with `I = 1`,
with lookup bitlengths of 5 and 6 bits, "following prior work". Division with zero refinement
iterations is a table-initialised approximation and nothing more — and division and reciprocal square
root are exactly what softmax and normalization are built from.

So the speedup is real and the price is unmeasured. The correct summary of this paper is *"the same
functions, far cheaper, at an accuracy cost nobody has reported"* — and given that the baseline chose
its representation **specifically to protect accuracy at depth**, that is the first experiment
anybody should ask for.
:::

**The baseline is single, and in-lineage.** Every comparison in the paper is against [[mystique]].
The comparison itself is scrupulous — they re-ran Mystique's own EMP implementation under their own
network and hardware conditions, which is more than most papers in this repo do — but "the
state-of-the-art ZK proofs for ML" is doing a lot of work. By 2024, [[zkcnn]] and [[zkllm]] existed,
and both prove non-linearities via lookup arguments in a sum-check system. Hao et al. dismiss
[[zkcnn]] in a sentence — "specialized and may not be readily extended to more complex functions" —
and note it assumes a gap between the field size and the input size. That may well be right, but it
is an argument, not a measurement. The headline improvement is over the state of the art *within the
VOLE lineage*.

:::audit `papers.yml` says "not open-sourced". The paper says otherwise.
The `hao-et-al` entry carries the note *"Not open-sourced (per zkGPT)"* — a claim inherited
secondhand from [[zkgpt]]'s related-work section, with `numbers_source: survey`. The primary source
disagrees, in §7.1:

> The source code is available at https://github.com/CryptMatrix/ZKMath.

A secondhand "not open-sourced" is exactly the kind of claim that ages into a quiet slander. It
should be corrected, and the entry promoted to `primary` now that the PDF has been read.
:::

**Watch the `T + 2N` cost model when you leave the amortized regime.** The lookup cost is not `O(1)`;
it is `O(1)` *given* `N ≫ T`, and `T` grows exponentially in the digit width. The paper is completely
upfront about this — it is why they observe a jump in runtime when the scale crosses 12 and a second
lookup table is needed. It is not a criticism, but it is the number to recompute before assuming these
results transfer to an operator that is evaluated a few thousand times rather than a few hundred
thousand.
