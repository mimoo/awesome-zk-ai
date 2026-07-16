---
title: Quantization, the hidden variable
section: zk-inference
order: 40
lede: >-
  Bit width is a free parameter that trades accuracy for proving speed. Most papers in this
  section do not state theirs. That makes the throughput column a comparison across an
  uncontrolled variable -- and it makes the range check an audit surface.
papers: [deepprove, zkgpt, zkpytorch, zkllm, jolt-atlas, spagkr, zen, zkcnn, zktorch, safetynets, nanozk, zip, bionetta]
status: draft
---

Finite fields have no floats. Every system in this section therefore quantizes the model to
integers before proving it, and quantization is not a preprocessing detail, it is a knob
that moves the headline number. Turn it down and the prover gets faster and the model gets
worse. Nothing in the [inference table](./) shows you where each system set the knob.

{{ table:inference cols=model,params,tokens_per_minute,quantization.bits }}

Read the last column first. The blanks are not missing data we failed to collect; `null` in
`papers.yml` means *the paper does not state it*. That is the finding.

## What the papers actually do

[[zkgpt]] gives the cleanest accounting of anyone: it states the bit width, states the
scheme (affine, `x = S(q - z)`, per-layer scale and zero-point, inherited from [[zkcnn]]),
and reports the perplexity cost on three named datasets. It is the reference point against
which the others should be normalized, and it sits at the *high* end of the bit-width range
which means it is doing a materially harder job on the lookup and range-check side than a
lower-precision system. That is not the same as saying its position in the throughput column is
a bit-width effect: zkGPT is a GKR system, and (see below) bit width barely touches the matmuls.
Its figure is a single forward pass, derived by us, and it is not commensurable with
DeepProve's for reasons that have nothing to do with bits.

[[deepprove]] states a bit width and an accuracy delta too, and it is the only paper here that
reports accuracy at *several* bit widths rather than one, which is the only reason the trade-off
is legible at all. It is worth reading closely because its quantization block is the most
sophisticated in the literature:

:::quote{src="DeepProve" sec="§5, Experiments"}
For various maximum sequence lengths, we run inference on the GPT-2 and Gemma 3 models
(with 124M and 270M parameters respectively) using DeepProve using 12-bit quantization
level.
:::

Underneath that sentence: symmetric affine post-training quantization with a calibration
pass, scale $s = a / (2^{b-1} - 1)$ where $a = \max(|x_{max}|, |x_{min}|)$ so the zero-point
vanishes; activations clamped to $[-a, a]$; mixed precision, with residual layers given a
larger bit length; and, the interesting one, **outlier smoothing by orthonormal rotation**,
$XW = (XM)(M^{\top}W)$, with $M$ absorbed into the previous layer's weights so the
hard-to-quantize activation tensor is never materialized. DeepProve further states that its scale
factors are *not* restricted to powers of two, unlike [[zktorch]]'s. It does **not** level that
charge at [[zkgpt]]; its complaint there is a fixed scaling factor used *without clamping*, which
forces a larger lookup table. **Our own reading is that zkGPT's scales are not powers of two
either**: it approximates the float scale ratio by the nearest fraction $C_1/C_2$, with the
integers found by search, an arbitrary rational. Both systems handle arbitrary float scales; they
differ in mechanism, not in generality. The two mechanisms are set side by side in
[the rescale seam](./numerics/), and the conflict is logged in
`papers.yml`.

Two things follow that most readers miss.

**Precision is nearly free for DeepProve, and that is a claim about lookup tables, not about
arithmetic.** Moving from its lowest to its highest tested bit width costs it almost nothing
in prover time, because the number of lookup tables barely changes. If your cost is
dominated by table *count* rather than table *size*, bit width is cheap. If it is dominated
by table size, as it is for a lookup-centric design like [[jolt-atlas]], bit width is
exponential. **These systems do not face the same trade-off, and neither of them says so.**

**Gemma 3 does not survive low precision, and the reason is architectural.** Below its
chosen bit width, Gemma 3's cosine similarity to the float model collapses, not degrades,
collapses. DeepProve attributes this to extremely large outlier activations plus extra
RMSNorm layers in the transformer blocks, which defeat exactly the rotation-smoothing trick
that works on GPT-2. This is the most important quantization result in the section and
nobody has followed up on it: **the smoothing technique that makes low-bit proving viable is
architecture-dependent, and modern architectures break it.** Every throughput projection
that assumes "and it will get cheaper as we quantize harder" is betting against this
finding.

:::gap  Two numbers in DeepProve's Table 4 are not explained
As printed: GPT-2's cosine similarity is *worse* at the highest bit width than at the middle
one, and Gemma 3's quantized perplexity is *better than its own floating-point baseline*.
Both are reproduced verbatim in `papers.yml`. Neither is addressed in the text. The second
is the more troubling, a quantized model beating its own fp32 reference on perplexity is
either a very small evaluation set talking, a baseline computed differently from the
quantized measurement, or a mistake. It is a small blemish on the most carefully quantized
paper here, which is exactly why it is worth flagging rather than ignoring.
:::

The rest of the field:

- [[zkpytorch]] runs the lowest *integer* precision of anyone, [[spagkr]]'s ternary weights are
  narrower still, but ternary is a structural change rather than a bit-width setting (see below)
with wider intermediates for matmul accumulation and a re-quantization back down
  after each table lookup. Its whole reason for doing so is *field size*, see below. Its
  LLM accuracy claim is a **cosine similarity**, which is a weaker guarantee than perplexity:
  a high cosine similarity can still flip an argmax and change a generated token.
- [[spagkr]] goes to ternary weights, $\{-1, 0, 1\}$, which eliminates multiplication
  altogether.
- [[zkllm]], [[zkcnn]] and [[nanozk]] state a scheme but no bit width.
  [[nanozk]] additionally claims its lookup approximations preserve perplexity *exactly*,
  which is an extraordinary claim in an unreviewed single-author preprint whose abstract
  contains an unsubstituted `METHOD` placeholder. Treat accordingly.
- [[zen]] never writes its width in a single sentence either, but it is pinned by its own
  encoding: its networks "work with low precision (e.g. 8-bit) unsigned integers", and packing
  those weights and activations into a BLS12-381 field element *is* its stranded encoding, so
  the width is structural rather than incidental.
- [[jolt-atlas]] states no bit width at all, and for its design that omission matters most.

## The Jolt Atlas problem

Lookup-table size is the dominant cost in [[jolt-atlas]], and table size grows exponentially
in the bit width of the lookup input. So bit width is *more* load-bearing there than in any
pure sum-check system, and it is the one paper that never gives it. The only precision
mentions in the paper are incidental and both concern the activation table rather than the
model.

Worse, its headline optimization is admittedly lossy:

:::quote{src="Jolt Atlas" sec="§4.2, Neural teleportation"}
the original computation y = σ(x) is replaced by y′ = σ(x/τ ), which is a lossy
approximation (i.e., y′ ̸= y in general) but it is not significant in practice.
:::

The error is bounded, but bounded in *raw output units of a fixed-point representation*,
never in model accuracy. There is no perplexity number and no task-accuracy number for any
model in that paper. So the system with the most bit-width-sensitive design is also the one
that reports neither the bit width nor what its approximation costs the model. Its results
are not therefore wrong; they are un-normalizable, and they cannot be placed on the same
axis as [[zkgpt]]'s or [[deepprove]]'s.

## Does lower precision actually mean faster proving?

Directionally yes, but the evidence is thinner than it looks, one measurement, and one that is
usually mistaken for one. [[spagkr]] is *reported by the ZKP-VML survey* to buy a further
multiplicative proof-time reduction from going ternary, on top of what its sparsity-aware
linear layers already buy; we have not read SpaGKR, and that figure reaches us secondhand. And
[[zen]] reports a large reduction in R1CS constraint count from its proof-friendly *encoding*, 
but read that one carefully: ZEN's baseline is a vanilla encoding of the *same* uint8 network, so
it measures ZEN's circuit tricks, not bit width, and its headline ratio excludes the in-circuit
commitment that dominates its smaller models (see [ZEN](../papers/zen/)). It is suggestive, not a
bit-width curve.

But the effect is **not uniform across the circuit**, and this is the part to internalize
before treating bit width as a single throughput knob.

1. **Lookups and range checks: exponential in bits.** A table indexed by a value has size
   $O(2^b)$. This is where the entire quantization saving lands in a lookup-centric system,
   and it is the cliff [[zkgpt]] documents when it declines to merge its rounding
   constraints too aggressively.
2. **The matmuls: essentially flat in bits.** In a sum-check/GKR system the prover's cost
   for a matrix multiplication is field operations proportional to the *number of gates*,
   which depends on parameter count, not on $b$, as long as the values still fit the field.
   Dropping precision barely touches the matmuls, and the matmuls are where a transformer's
   FLOPs live.
3. **Except when it changes the field, which is the real prize.** Low precision lets you pick
   a *small* field. [[zkpytorch]] quantizes hard specifically so it can work over M61 instead
   of a 254-bit curve field like [[zkgpt]]'s BN254. That is a large constant factor across
   the *whole* circuit, matmuls included, and it is a much bigger lever than the lookup
   tables.
4. **Ternary is a structural change, not just "very few bits".** [[spagkr]]'s win comes
   substantially from $\{-1, 0, 1\}$ weights *removing multiplications* and inducing
   sparsity. Do not extrapolate it to "narrow integers give this speedup" for an arbitrary
   system.

So the intuition holds, but the mechanism is *lookup tables, sparsity and field size*, not
the matmuls. A GKR system dominated by attention matmuls may see almost nothing from
quantizing harder; a lookup-heavy system should see a great deal. Which is one more reason
two systems' throughput figures at different bit widths are not two points on the same
curve.

## Quantization as an audit surface

This is the part that should worry an auditor, and it is not hypothetical arithmetic, it is
what these systems actually do.

Quantized zkML pushes correctness onto **range checks and lookup arguments**. [[zkgpt]]'s
*result-as-witness* paradigm has the prover supply the output of Softmax, LayerNorm and GeLU
as a witness and then prove it lies in the correct range. Soundness therefore rests
*entirely* on those range constraints being complete. An under-constrained range check in a
result-as-witness design lets a malicious prover assert an arbitrary non-linear output, and
under-constrained circuits are the class SNARK auditors report finding most often. We do not cite
a count here: no vulnerability taxonomy is in this SoK's corpus yet. Combine those two sentences
and you have where to look first.

The other half of the surface is the *range itself*. Lookup tables and quantization scales
are fixed at preprocessing, from a calibration dataset. An activation that falls outside the
calibrated range at inference time is not merely inaccurate, it may be **unprovable**.
[[deepprove]] says this outright about its competitors' design:

:::quote{src="DeepProve" sec="§6, Related work"}
The major downside is that since re-quantization and non-linear functions are usually proven
via lookup arguments, using a fixed scaling factor without clamping can lead to situations
where the values generated during inference are too large to be looked up, thus forcing a
larger lookup table to commit.
:::

DeepProve's answer is to clamp activations into the calibrated range. That is the right
engineering call and it has a consequence worth naming: **clamping is a silent modification
of the model.** The proof is now a faithful proof of the *clamped* computation. On an
adversarially chosen input designed to drive activations far out of the calibration range,
the certified output and the true model's output can diverge, and the proof will verify
anyway, because the clamp is inside the statement, not a violation of it.

:::audit  Audit surface
Three questions to ask any quantized zkML system. Only DeepProve answers the second; no paper
here answers the other two:

1. **Is the range check complete?** In a result-as-witness design, a missing constraint on
   the witnessed output of a non-linearity is a total soundness break, not a precision bug.
2. **What happens to an out-of-calibration activation?** Clamped (the computation silently
   changes), rejected (the prover can be DoS'd by a crafted input), or unprovable (same)?
   The choice is a security property. DeepProve names it, it clamps, and proves the
   out-of-range case explicitly. Everyone else leaves it undocumented.
3. **Who chose the calibration set?** In MLaaS the prover is the model owner, so the prover
   chose it. The scales, the tables and the clamps are all downstream of data the verifier
   never sees.

**No such bug is known in any system listed here.**
This is where we would look, not what we have found.
:::

## The system with no bit width at all

[[bionetta]] does not appear in the table above, and the reason is the most useful thing it has to
say about quantization: **it has no bit width in the sense this page has been using the term.**

It does not quantize activations down to 8 or 12 or 16 bits. Every value stays a full BN254 field
element carrying $\rho$ fractional bits, and the cost of a non-linearity is $b+1$ constraints where
$b$ is the width of the **field**, 254, not the width of the value. ReLU has to bit-decompose its
input to find the sign, and what it decomposes is the field element. It pays for 254 bits whether
the number in there is worth 15 of them or 60.

The consequence is the sharpest result on this page, and it cuts against the premise the page opens
with. **Raising the precision costs nothing.** Bionetta measures relative error against TensorFlow
over $10^5$ random inputs, worst case across five models, and it falls from $5.2\times10^{-3}$ at
$\rho = 15$ to $9.4\times10^{-7}$ at $\rho = 60$, four orders of magnitude, with **no change to
the constraint count**, because the decomposition was over the field element all along.

That is [[deepprove]]'s finding, four more bits costs well under one percent of prover time, 
reproduced in an unrelated proof system by a team that has never heard of it. Two systems now say
the same thing: *the knob the field has spent a decade turning is not the knob that costs money.*
What precision actually costs is **seams**, a larger $\rho$ overflows sooner and forces more
frequent rescales. See [the numerics page](/numerics/) for the argument, and for the open question
these two jointly sharpen.

The catch is real, and it is the same catch as everywhere else on this page. Bionetta can afford
to bit-decompose because its rescale rides for free on a ReLU it was already paying for, and it
can afford *that* only because it supports nothing but the ReLU family. No softmax, no attention,
no transformer. It is not a refutation of the field's quantization strategy so much as a
demonstration of what that strategy is buying, and of what it is paying with.

## The counter-thesis

[[zip]] does not quantize. It proves inference over native IEEE-754 double-precision
floating point, using piecewise-polynomial lookup approximations for activations with extra
arithmetic constraints hardening the lookups against a malicious prover. It is a small-model
system and it is not a competitor on throughput, but it is the standing proof that
quantization is a **design choice made to fit the prover**, not a law of nature.

With one caveat that changes how the paper should be cited, and that we have not seen stated
anywhere: **ZIP's proof does not bind the activation to its true IEEE-754 value.** The exact
double is a *witness*, constrained only to lie within a $\delta$-relative ball around a
certified polynomial approximation, and on GeLU, its flagship activation, that ball is wide
enough to swallow bfloat16's entire machine epsilon an order of magnitude over. The precision
is a property of *what the honest server computes*, not of *what the proof enforces*. The
argument, and why it is a research question rather than a bug, is in
[the rescale seam](./numerics/).

That reframes the whole section. Most of this literature *bends the model to fit the
prover*: [[safetynets]] restricted activations to quadratics, [[jolt-atlas]] teleports the
network, [[spagkr]] wants ternary weights. A smaller strand
*bends the prover to fit the model*: [[deepprove]]'s standard-ML quantization
pipeline (whose authors pointedly note that theirs is the only work to measure accuracy with
the exact codebase the prover consumes), and [[zip]]'s native floats. The second strand is
the one that scales to models you did not get to choose.
