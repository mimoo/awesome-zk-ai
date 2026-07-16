---
title: Floats, fixed point, and the rescale seam
section: numerics
order: 10
lede: >-
  A neural network multiplies real numbers; a SNARK multiplies integers mod p, and an MPC
  protocol multiplies secret shares of them. Every system in this section is an answer to that
  disagreement. The cost of the answer is not in the matmuls, it is at the seams between them,
  where a wide accumulator must be squeezed back down. That squeeze is a division, and neither
  a field nor a secret share can divide.
papers: [deepprove, zkgpt, zkllm, zkpytorch, zktorch, jolt-atlas, safetynets, zip, hao-et-al, zkcnn, zkml-kang, zkpot-garg, garg-fp, zklp, archer-ieee, secfloat, prob-truncation, range-arithmetic, modulus-cost-of-intelligence, bionetta]
status: draft
---

**This section belongs to neither column of the 2x2, because it sits underneath both.**

Everywhere else in this SoK, a page belongs to a cell: you are either proving a computation or
hiding it. The papers here do neither. They answer a question that arrives *before* the
cryptography does, **how do you represent a real number at all, once you have left the reals?**, 
and both columns have to answer it before they can begin.

So the five papers in this section split down the middle, and the split is not the one the rest of
the atlas uses. [[garg-fp]] and [[zklp]] build floating-point arithmetic inside a *proof*.
[[archer-ieee]], [[secfloat]] and [[prob-truncation]] build it inside a *secure computation*, no
proving anywhere, no verifier, nothing to check. They are in the same section because they are
solving the same problem, and because, as the [bridge](./bridge/) page shows, they are the only
place where the two literatures of this repo demonstrably touch.

Read this page for the problem. Read [the bridge](./bridge/) for who has been quietly borrowing
from whom.

---

[Quantization](./quantization/) asks *where each system set the bit-width knob, and what it
cost them*. This page asks the question underneath: **why does the knob exist at all, and what
exactly are you paying for when you turn it?**

The short answer is that sum-check makes matrix multiplication nearly free, so the matmuls are
not where the money goes. The money goes to the **seams between** the matmuls, where the output
of one layer has to be rounded back down to the width the next layer expects. Rounding is
division. **Division is not an operation a finite field has.** Everything below is a consequence, 
and almost all of it restates, in ZK vocabulary, a constraint the MPC world hit first.

## Deep learning chose range over precision

Start with the format the industry actually runs on, because it is the opposite of what a
circuit wants.

| Format | Sign | Exp | Mantissa | Max finite | Machine $\epsilon$ | ~Decimal digits |
|---|---|---|---|---|---|---|
| FP32 | 1 | 8 | 23 | $\approx 3.4\times10^{38}$ | $2^{-23}$ | ~7.2 |
| FP16 | 1 | 5 | 10 | $65{,}504$ | $2^{-10}$ | ~3.3 |
| **BF16** | 1 | **8** | **7** | $\approx 3.4\times10^{38}$ | $2^{-7}$ | **~2.4** |
| FP8 (E4M3) | 1 | 4 | 3 | $448$ | $2^{-3}$ | ~1 |
| INT8 | — | — | — | $127$ | *(step 1)* | *uniform* |

**BF16 is the row that matters, because of what it gave up.** It keeps every bit of FP32's
exponent, the full $10^{-38}$ to $10^{38}$ dynamic range, and pays by cutting the mantissa from
23 bits to 7. It carries roughly *two decimal digits*. It is a wildly imprecise format, and it is
what modern models train and run in.

That was a deliberate trade, and it is the fact the whole numerics problem hangs on:

> **Deep learning needs dynamic range far more than it needs precision.**

Weights cluster near zero; activations occasionally spike enormously; gradients decay across
depth. What kills a network is a value that *overflows to infinity* or *underflows to zero*, not
a value wrong in its eighth significant digit. Networks are statistical objects with enormous
redundancy and they absorb per-element noise; they do not absorb a silently zeroed tensor. FP16,
with only 5 exponent bits, really does overflow in training and needs loss-scaling to survive.
BF16 exists to make that class of problem disappear. The industry chose range.

**A fixed-point number is precisely the opposite trade.** $Q_{m.f}$ is an integer with an implied
binary point: a uniform absolute step of $2^{-f}$ and a hard ceiling at $2^m$. Uniform precision
everywhere, *no dynamic range at all*. It is the format deep learning rejected, and it is the
only thing you can cheaply put in a circuit.

[[zkpytorch]] states the resulting bind more crisply than anyone:

:::quote{src="zkPyTorch" sec="§2.3, Machine Learning Quantization"}
directly handling floating-point numbers is infeasible due to the high computational overhead
required for native floating-point support in ZK circuits. To address this, previous ZKML schemes
employ fixed-point numbers to approximate floating-point values. However, due to the wide dynamic
range of floating-point numbers, fixed-point representations require a significantly larger bit
width for accurate representation. For instance, the standard float32 format can represent
positive numbers ranging from approximately $2^{-126}$ to $2^{127}$, whereas 32-bit fixed-point
numbers are limited to a range of $2^{-16}$ to $2^{16}$. This disparity forces fixed-point
representations to use additional bits to emulate floating-point numbers, thereby necessitating
ZKML to operate over large finite fields, such as the scalar field of the BN254 curve, which
considerably reduces efficiency in proof generation.
:::

Read that as a causal chain, because it organizes the entire section:

$$\text{float dynamic range} \Rightarrow \text{many fixed-point bits} \Rightarrow \text{big field} \Rightarrow \text{slow prover}$$

The field's response was to break the chain at the front: quantize to small integers, so you can
use a small field. [[zkpytorch]] picks **M61** for exactly this reason, its aggressive
quantization is not primarily about lookup tables, it is about *escaping BN254*. **Your numeric
format chooses your field, and your field is a constant factor on the entire circuit.**

But breaking the chain at the front adds a term at the back that the papers underplay:
*and now you must prove all the rounding.*

## What a field refuses to give you

A SNARK offers variables in $\mathbb{F}_p$ and two operations, $+$ and $\times$. What is *absent*
is what costs money:

**No order.** $\mathbb{F}_p$ is not ordered. "Is $a < b$?" is not a field question, the elements
are residue classes, they do not sit on a line. Every ReLU, max, clamp, and comparison must be
*manufactured*, usually by decomposing into bits.

**No magnitude.** There is no $|x|$. Negative numbers are a *convention*: we agree to read $p-5$
as $-5$, and that works only while everything stays inside a window we reserved by hand. Nothing
in the field enforces the window.

**No division.** You *can* divide in $\mathbb{F}_p$, $x/2^s$ means $x\cdot(2^s)^{-1} \bmod p$,
and that inverse exists. But it is **not truncation**. If $x$ is not an exact multiple of $2^s$,
field division returns a perfectly valid field element that is a huge, unrelated number bearing no
relation to $\lfloor x/2^s \rfloor$. Field division inverts field multiplication; **integer
division is a different function entirely**, and the field does not implement it.

That is the crux:

> The rescale after a matmul is a floor-division. Floor-division is not a field operation.
> You cannot compute it, you can only **guess it and check it**.

## The rescale seam

Take a dot product of $n$ values quantized to $q$ bits:

$$q\text{-bit} \times q\text{-bit} \rightarrow 2q \text{ bits}, \qquad \text{summed over } n \rightarrow 2q + \log_2 n \text{ bits}$$

At $q=8$ with hidden dimension $4096$, an 8-bit input becomes a 28-bit output. Every matmul
inflates its operands and must be deflated before the next one, or widths compound layer over
layer until they pass the modulus. [[deepprove]] puts it plainly:

:::quote{src="DeepProve" sec="§4, Requantization"}
the bit-length of the intermediate values in LLM inference would grow rapidly, leading to
computation slowdown and even potential field overflow.
:::

Deflating means computing $y = \text{round}\big((S_x S_w / S_y)\cdot \text{acc}\big)$, which needs
two things a field hates: multiplication by an **arbitrary float ratio**, and **rounding**.

### The universal trick: advise, then range-check

Nobody computes the division. **Everybody guesses it and checks it.** To prove
$y = \lfloor x/2^s \rfloor$, the prover supplies both $y$ and a remainder $r$ as
non-deterministic advice, and the circuit enforces:

$$x = y\cdot 2^s + r \qquad\text{and}\qquad 0 \le r < 2^s \qquad\text{and}\qquad y \text{ in range}$$

The first constraint is one multiplication and one addition, nearly free. It is also, **on its
own, worthless**: without the range check the prover can pick *any* $y$ and set
$r = x - y\cdot 2^s$ to match. The range check is not a detail. **The range check is the entire
proof.** The arithmetic is bookkeeping; the security is all in the bounds.

[[zkgpt]] names the pattern outright:

:::quote{src="zkGPT" sec="§4.3"}
division, square root, and exponentiation as advice and check the correctness of the computation.
This is much cheaper than simulating the computation in arithmetic relations.
:::

### How the range check is actually done, and why lookups changed everything

The pattern above is stable across a decade. What has changed, and what actually moved the cost
curve, is the *implementation of the range check*. Three generations, and you can watch them
happen:

**Generation 1, bit decomposition.** Decompose the value into bits, prove the bits recompose to
it, and simply *drop* the low $k$ bits. That is division by $2^k$, and it is what the
[[modulus-cost-of-intelligence]] report describes as the standard approach:

:::quote{src="Modulus, The Cost of Intelligence" sec="§3.2, Fixed-point division"}
we scale the model weights and inputs by a factor of $s$ each, and the bias values by a factor of
$s^2$ each, and after performing a typical linear layer computation $Wx + b$, we "un-scale" the
output by a factor of $s$, i.e. we divide by $s$. For the division operation we use bit
decomposition, truncating the $k$ least significant bits to effectively divide by $s = 2^k$.
:::

Cost: roughly one constraint per bit, per value, at every seam. Note also how it handles sign, 
by the raw field convention, *"the range $p/2 < x < p$ represents negative values"*, precisely the
hand-reserved window from the section above, with nothing but a comment enforcing it.

**Generation 2, wider chunks, checked by lookup.** The same report's Halo2 implementation already
decomposes in **base 1024 instead of base 2**, and range-checks each limb against $[0, 1023]$ *with
a lookup table*. One lookup replaces ten bit-constraints. The gadget did not change; the
*verification of the gadget* got cheaper.

**Generation 3, decomposable lookup tables.** Which is exactly where [[deepprove]] lands: $k$-bit
chunks, each range-checked against a small table, with the tables *decomposable* so they never have
to be materialized in full (the Lasso/LogUp line of work). Same seam, same advice, same three
constraints, but the expensive one is now a lookup argument instead of a bit-blast.

**This is the real reason lookup arguments transformed zkML**, and it is usually explained
backwards. They are not primarily a trick for evaluating non-linearities. They are a cheaper way to
do the *range checks*, and range checks are what rounding costs. Non-linearities were the visible
beneficiary; the rescale seam is where the tonnage was.

[[zkgpt]] then states the cost model that governs this entire field:

:::quote{src="zkGPT" sec="§5.1, Constraint level optimization"}
rounding introduces range relations to prove, which are more computationally expensive than
proving arithmetic relations.
:::

**Arithmetic is cheap; rounding is expensive; the game is to round as seldom as possible.** Once
you hold that sentence, every design decision in every paper here becomes legible.

### Two ways to kill the arbitrary float scale

The ratio $S_xS_w/S_y$ is a float, and you cannot put a float in a field. There are exactly two
moves, and the two leading LLM systems each took one.

**Move A, integer multiplier, power-of-two shift.** [[deepprove]] fixed-point-encodes the float
scale as an integer, multiplies by it, adds a half for round-to-nearest, then divides by a power
of two, which is a *shift*:

$$y = \left\lfloor \frac{\text{Quant}(2^f\epsilon)\cdot x + 2^{f+\delta-1}}{2^{f+\delta}} \right\rfloor - 2^{q-1}$$

:::quote{src="DeepProve" sec="§4.3.2, Case 1"}
At first glance, this formula seems "SNARK-unfriendly" as it requires one division per element.
Observe, however, that the divisor is a power of two number, and thus the division can be
considered as a right shift which is easier to prove.
:::

The shift is proven by a lookup argument over *decomposable tables*: decompose into $k$-bit
chunks, range-check every chunk, keep the most significant ones. Note what happened, **the range
check and the shift are the same operation.**

**Move B, rational approximation, inequality sandwich.** [[zkgpt]] never divides at all. It
approximates the float ratio by a rational $C_1/C_2$ of two $Q$-bit integers, then encodes "$q_z$
is the correctly rounded result" as a pair of integer inequalities:

$$C_2 q_y(2q_z - 1) \;\le\; 2C_1 q_x \;<\; C_2 q_y (2q_z+1)$$

Multiply through by the denominator and rounding becomes a *sandwich of two comparisons*. No
division survives. The trick generalizes beautifully, zkGPT proves square roots the same way:

$$q_y = \text{round}(\sqrt{q_x}) \iff (2q_y-1)^2 \le 4q_x \le (2q_y+1)^2 - 1$$

An irrational function reduced to two multiplications and a range check.

One caveat on provenance, since this page is arguing partly from it: zkGPT spells out the *search*
for $C_1/C_2$, "obtained by searching in an interval $[1, 2^Q]$ and finding the nearest fraction"
and spells out the double inequality, in §4.3, where it is discussing **division**. For the
matmul rescale (§2.1) it says only that $C_1, C_2$ are "$Q$-bit integers" with
$C_1/C_2 \approx S_xS_y/S_z$, and never writes that inequality out. The mechanism is clearly the
same one; but if you want the fully explicit version, it is stated for division, not for the
rescale.

:::debate  Who actually restricts scales to powers of two? Not zkGPT.
[[deepprove]] does make a powers-of-two complaint, and makes it twice, but never against
[[zkgpt]]. Of [[zktorch]] it says the "use of scaling factors is limited to powers-of-2, which
incurs greater precision loss than the flexible quantization approach adopted in DeepProve", and
of [[zkllm]] it says that protocol "only uses scaling factors of the form $2^k$ with $k \in
\mathbb{Z}$ where as we allow for $k \in \mathbb{R}$". Its objection to zkGPT is a different one
altogether: that "using a fixed scaling factor without clamping" can push intermediate values past
what the lookup table can hold, "thus forcing a larger lookup table to commit."

So the powers-of-two conflict recorded against zkGPT, in our `papers.yml` `conflict_flag`, and
repeated on our own [quantization](./quantization/) page, is **ours, not DeepProve's**, and zkGPT's
own text does not support it either. As quoted above, zkGPT searches $[1, 2^Q]$ for the *nearest
fraction* $C_1/C_2$ to the true float ratio: an arbitrary rational, not a power of two. DeepProve
and zkGPT both admit arbitrary float scales; they differ in **mechanism**, not in generality, 
DeepProve puts the arbitrary part in the *multiplier* and keeps a power-of-two *divisor*; zkGPT
keeps both arbitrary and pays with an inequality instead of a division. The real powers-of-two
restriction is zkTorch's and zkLLM's, and DeepProve is right about it.
:::

### Since rounding is the cost, round less often

If range checks dominate, the optimization writes itself. Three papers found it independently and
gave it three names:

- [[zkgpt]], **constraint fusion**: merge the computation between two adjacent roundings into one
  rounding. It is explicit that this generalizes a trick [[zkcnn]] and [[zkml-kang]] used only in
  the narrow convolution→ReLU case.
- [[deepprove]], **delayed requantization**: fuse the non-linearity with the requantization that
  follows it and prove both in one lookup.
- [[jolt-atlas]], accumulate in **i64** across a node and rebase only at node boundaries, so
  intermediate products never round at all.

Same insight, three vocabularies: *minimize the number of seams.*

### And a fourth, which does not make the seam cheaper, it makes it free

[[bionetta]] found the same thing a fourth time, in R1CS rather than sum-check, and pushed it to
the limit the other three stop short of.

Its observation is one line long. **ReLU already bit-decomposes its input**, that is how you
extract a sign from a field with no order, and it costs $b$ booleanity constraints plus one. But
*once you are holding the bits, a right shift is free*: you drop the low ones and recompose. So the
rescale, the precision cut, the division, the thing this entire page has been about, costs
**nothing at all when it rides on a ReLU you were already paying for**. Bionetta's proposition is
that `ReLU(x) >> ρℓ` costs $b+1$ constraints, which is exactly what a bare `ReLU(x)` costs.

zkGPT, DeepProve and Jolt Atlas all fuse seams to make them *cheaper*. Bionetta fuses the seam into
a range check it had **already bought**, which makes it not cheaper but free. That is the strongest
available form of "the range check is the entire proof": if the range check is the proof, then a
rescale that reuses an existing range check is not a cost at all.

The price is that you only get it where a ReLU is. It is a **ReLU-family-only** result, which is
precisely why Bionetta supports the ReLU family and nothing else, and why it has no softmax.

:::gap  Is bit width actually the expensive knob? Two systems now say no.
[[deepprove]] reports that raising its bit width by four bits costs well under one percent of
prover time, because the *number* of lookup tables barely changes. If the cost is the number of
rounding **seams** rather than their **width**, then a decade of aggressive quantization has been
optimizing the wrong variable, trading accuracy for a saving that was never there.

**[[bionetta]] is the second data point, and it is a much sharper one, and neither paper knows the
other exists.** Bionetta does not quantize activations to a narrow integer at all. Every value is a
full BN254 field element carrying $\rho$ fractional bits, and a non-linearity costs $b+1$
constraints where $b$ is the width of the **field** (254), not the width of the *value*. So
raising $\rho$ **does not change the constraint count by one**. And the accuracy it buys is not
marginal: measured against TensorFlow over $10^5$ random inputs, worst case across five models,
relative error falls from $5.2\times10^{-3}$ at $\rho = 15$ to $9.4\times10^{-7}$ at $\rho = 60$.
**Four orders of magnitude of accuracy, for zero constraints.**

There *is* a cost to more precision, and it is exactly the one this section predicts: a higher
$\rho$ means products blow past the modulus sooner, so you must insert precision cuts **more
often**. The bill for precision does not arrive as *width*. It arrives as **seams**, and when a
seam lands on a ReLU, it is free, and when it does not, it costs a full decomposition.

Two systems, two unrelated proof systems, one answer: **the expensive knob is the number of seams,
not the number of bits.** It is still true that nobody has run the experiment deliberately. It is
no longer true that there is no evidence.
:::

## Softmax is the worst thing in the building

$\text{softmax}(x)_i = e^{x_i} / \sum_j e^{x_j}$ is hostile to fixed point in three independent
ways, and they map exactly onto the three things §"What a field refuses to give you" says are
missing:

1. **Unbounded dynamic range.** $e^{20}\approx 4.9\times10^{8}$ and $e^{-20}\approx 2.1\times10^{-9}$
seventeen orders of magnitude from a modest input range. That is what a float's exponent
   field is *for*, and what fixed point cannot represent.
2. **It needs a max-subtraction to be numerically stable** ($e^{x_i - \max x}$). But $\max$ is a
   **comparison**, and the field has no order, so numerical stability itself costs range checks.
3. **It ends in a division** by the sum, on a value whose magnitude you do not know in advance.

Range, order, and division: softmax hits all three weaknesses at once. So it is unsurprising that
it is where every system spends its cleverness, [[zkllm]] builds a bespoke `zkAttn` to avoid
bit-decomposing it; [[zkpytorch]] gives up on arithmetic and looks $\exp$ up in a piecewise table;
[[jolt-atlas]] runs a four-stage batched sumcheck with a one-hot `argmax`, an operand link, and a
saturating clamp made unique by a complementary-slackness argument.

And [[hao-et-al]] gives the cleanest measurement anyone has of what non-linear dynamic range
costs, by benchmarking the operators standalone: softmax against ReLU, same system, same hardware.
The gap between them, in both proving time and communication (this is an interactive,
designated-verifier system; the megabytes are bandwidth, not a proof object), is the price of the
exponent field, and it is not a small gap. RMSNorm/LayerNorm is the same story in miniature: a sum
of squares (magnitude grows quadratically) followed by a reciprocal square root (both ends of the
range at once).

**The map of "hard to quantize" and the map of "expensive to prove" are the same map.** That is
not a coincidence, both are measuring dynamic range.

### Why softmax is unquantizable *by construction*

There is a deeper reason than "exp has a big range", and it is the most elegant fact I found while
writing this page. Bondarenko et al. (*[Quantizable
Transformers](https://arxiv.org/abs/2306.12929)*) point out that an attention head often wants to
emit a **no-op**, to attend to nothing. But softmax can never output exactly zero:

> $\text{softmax}(x)_i = 0$ would require an infinite dynamic range.

So to approximate "attend to nothing", training drives the losing logits *apart without bound*. The
network manufactures enormous activations because the only way to express zero attention is to push
a logit toward $-\infty$. **The outliers are not a defect of the model. They are softmax's boundary
condition, made of activations.**

That single observation ties the whole page together. The outliers of §"the statement is
conditional" (which threaten field overflow), the dynamic range of §1 (which forced BF16), and the
expense of softmax in every prover here are *the same phenomenon*, seen from three angles. And it
is empirically load-bearing: Bondarenko et al. report that a vanilla BERT-base is **destroyed** by
W8A8 quantization, and that swapping in a *clipped* softmax which **can** emit exact zeros
collapses the activation infinity-norm and restores a working model.

The industry's own carve-outs confirm the diagnosis from the other side.
[SmoothQuant](https://arxiv.org/abs/2211.10438) quantizes the linear layers and attention BMMs to
INT8 and explicitly keeps **Softmax, LayerNorm and the residual connections in FP16**.
[DeepSeek-V3](https://arxiv.org/abs/2412.19437), the largest publicly documented FP8 training run
puts all three Linear GEMMs in FP8 but keeps the **normalization operators and attention
operators** in BF16/FP32.

**The parts of a transformer that industry refuses to put in 8 bits are exactly the parts zkML
must put in a lookup table.** Both are paying for the same missing exponent field.

## Overflow: proving the wrong statement, correctly

Return to the field's silent failure mode, because it deserves its own section.

**If an accumulator exceeds $p$, the arithmetic wraps, and the prover then produces a completely
valid proof of the wrapped result.** The proof is not lying. The circuit really did compute what
the proof says. It is just that the circuit computes in $\mathbb{Z}/p\mathbb{Z}$ and you *thought*
it was computing in $\mathbb{Z}$.

This is a **semantic** gap, not a cryptographic one, and that makes it nastier: no amount of
soundness analysis of the argument system will catch it. The proof system is working perfectly.
The *encoding* is what broke.

There are three postures, and the literature takes all three:

1. **Prove it cannot happen.** Range-check every intermediate. Correct, and expensive.
2. **Argue it cannot happen, offline.** [[zkpytorch]] runs a calibration phase that estimates
   value ranges and checks the chosen bit width avoids intermediate overflow. [[safetynets]] does
   the analytic version, it derives the largest representable value for its Mersenne prime and
   *rules out* scaling factors that would exceed it. Sound **iff** the calibration set covers the
   true input distribution: an ML assumption doing cryptographic work.
3. **Assume it away.** Which is what most of the field did.

That last posture is not my characterization, it is [[deepprove]]'s. Its actual contribution in
§4.3.2 is *Case 2*: proving requantization when the input is **out** of range, via lookup tables
that emit $-1/0/+1$ to detect and correct overflowing elements. It introduces this by observing
that the in-range case is

:::quote{src="DeepProve" sec="§4.3.2, Case 1"}
the only scenario considered by prior works
:::

citing [[zkllm]] and [[zkgpt]], which is accurate: those two do assume it.

But **DeepProve is the only *paper* to give an explicit out-of-range protocol, not the only
*system* to have one.** [[jolt-atlas]] arrives at the same place by a different route, and only its
source code says so: a saturating clamp (`SatClamp`, materializing an `i64` accumulator clamped to
`i32`) discharged by a prefix-suffix Shout sumcheck and **fused into the same rebase seam as the
rescale**, the seam-minimization principle of the previous section, applied to overflow. Its paper
never mentions this.

The two mechanisms are genuinely different, and the difference is worth naming: DeepProve *detects*
out-of-range with a proven predicate (a zero-detector table and a sign-extractor table, blended to
$\pm 2^{q-1}$); Jolt Atlas *saturates unconditionally* with a single clamp lookup. **A proven
predicate versus a proven function.** Both are real out-of-range handling.

Jolt's coverage is also partial, and in the places that matter for an auditor: in ZK mode `Add`,
`Sub` and `Sum` are proved *un-clamped*; the standalone ONNX `Clamp` operator is an unproven
passthrough (`// TODO: Clamp`); and the `tanh`/`erf`/`sigmoid` clamps are prover-side `assert!`s
over unconstrained advice. A `debug_assert` is not a constraint.

:::audit  The statement is conditional, and the condition is unproven
For most of zkML's history the systems have proved: *"the network was evaluated correctly,
**assuming** no intermediate value ever left its expected range"*, and have not proved the
assumption.

That would be a footnote if out-of-range activations were a rare accident. **They are not.**

Dettmers et al.'s LLM.int8() work characterizes them precisely: transformers undergo a *phase
transition* at around the 6.7B-parameter scale, after which the same outlier appears in **all
layers, in the same feature dimension**, for roughly 75% of sequence positions. Those outliers run
**3–20× larger** than the largest magnitude in any other feature dimension (which typically sit in
$[-3.5, 3.5]$). They are ~0.1% of features, in a 6.7B model, on the order of 150,000 outliers per
sequence, concentrated in about **six feature dimensions**. And the trigger is *perplexity*, not
parameter count: it is a property of how good the model is, not how big.

So the hazard is **structural, not statistical**. It is systematic, it is concentrated, it lives in
known dimensions, and it is exactly what [[deepprove]]'s rotation trick and every SmoothQuant-style
method exist to fight. A calibration range estimated on benign data is being asked to hold against
an input the *prover* chose.

So the question for any system here: **can an adversarially chosen input drive an accumulator past
the modulus, and yield a valid proof of a wrong inference?** As far as I can tell this is
unanalyzed everywhere. DeepProve and Jolt Atlas both *bound* the accumulator, one by a proven
predicate, one by a saturating clamp, but neither asks whether a chosen input can drive a value
past the modulus in the first place, and the rest of the field does not bound it at all. It pairs
naturally with the
Fiat–Shamir question, both are cases where the proof is fine and the
*statement being proved* is not the one anybody thinks it is.
:::

## So can we just use floats?

Every paper in this section says no, in a tone suggesting it is settled. **It is not settled, and
the folklore is wrong.** This is the part of the document I would most want a reader to take away,
because the entire literature is organized around a premise that two papers outside it have
already falsified.

### Why the naive answer is "no"

Floats are expensive because IEEE-754 is *an algorithm, not an operation*: align exponents, add
mantissas, renormalize, round, handle subnormals, handle NaN and $\pm\infty$. Every step is
data-dependent branching, and branching in a circuit means evaluating **all** branches and
selecting, bit decomposition, comparisons, shifts.

Two independent primary sources agree on what that costs, and they agree with each other exactly.
Here is the comparison as [[zip]] compiles it, and as the ZKLP paper independently restates it:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§5.1, Comparison With Other Works"}
Naively converting FP32 operations compliant to IEEE 754 requires 2456 and 8854 boolean gates for
addition and multiplication [22]. FP64 addition and multiplication require 15637 and 44899 boolean
gates respectively [21].
:::

:::debate  The number the field leans on deserves an asterisk
We traced those double-precision figures back to their source, [[archer-ieee]], and they check out
arithmetically, but they are the *most generous* of several defensible numbers. Archer's table
reports the FP64 circuits by gate type: addition is 5,385 AND + 8,190 XOR + 2,062 INV; multiply is
19,626 AND + 21,947 XOR + 3,326 INV. Sum each row and you get exactly the 15,637 and 44,899 that
ZIP and ZKLP quote.

But in most MPC and ZK settings **the AND gates are what cost**, and XOR is cheap or free, so the
load-bearing figures are 5,385 and 19,626, two to three times smaller. Archer et al. go further
and say that for their engine "the dominant cost is not the number of AND gates but the *depth*".

So the citation chain runs: an MPC paper's total-gate column → quoted as "gates" by two ZK papers →
absorbed by the zkML literature as proof that floats are hopeless. The conclusion still holds
(19,626 AND gates is enormous next to a field multiply). But this is a number that has been
travelling for years without anyone opening the table it came from.
:::

Compose that up to a real activation and it gets ugly. [[zip]] adds up those primitives, plus
$\sqrt{\cdot}$ and $\tanh$, and estimates that "a single GeLU activation requires approximately
1,302,142 R1CS constraints in single precision (and 6,808,760 R1CS constraints in double
precision)." For one activation, on one scalar. GPT-2 evaluates a GeLU on every one of its 3,072
MLP hidden units in each of its 12 layers, roughly $4\times10^4$ of them per token, before a
single matmul is proven.

That is the number the whole field is quietly reasoning from, and it *is* hopeless. But it is the
cost of **naive** emulation, transliterating a software float routine into gates. It was never a
lower bound, and two lines of work have since beaten it, in two completely different ways.

### Camp 1: relax the semantics (Garg et al., CCS '22)

[[garg-fp]] (*Succinct Zero Knowledge for Floating Point Computations*) makes the
observation that you do not actually need to prove the IEEE rounding *procedure*. You need to
prove the result is **accurate**. So instead of arithmetising round-to-nearest, prove a
relative-error bound on each gate:

$$|c - g(a,b)| \le \delta\,|g(a,b)|$$

where $g$ is the exact product or sum, and $\delta$ can be set to machine epsilon, *"the relative
error bound in the IEEE standard."* Zeros, infinities and NaN are handled as separate corner
cases. The paper is candid that this is a **deviation**, not a compliance:

:::quote{src="Garg et al., CCS '22" sec="§2, Our Model"}
our model does not guarantee that the value in the output wire of a step of the computation is
rounded to the nearest number (as is done in the IEEE standard). Instead, our model allows a
larger (by a factor of 2 in some cases) absolute error.
:::

Against the prior method of verifying that the computation followed IEEE exactly, Garg et al. report
that their prover is
"~57× faster for 32-bit floating point numbers, and 236× faster for 64-bit floating point numbers."

**And that is precisely [[zip]]'s technique, one level up.** ZIP applies the same relative-error
relation not to individual float gates but to whole *activations*, cite-for-cite, it is Garg's
numerical-analysis machinery reused at the layer level. Which reframes ZIP: it is not a
"native IEEE-754" system in the sense a reader assumes. It is a **relative-error** system whose
honest prover happens to compute in double. That is exactly the gap the audit box below is about,
and now we can see it is inherited, not invented.

### Camp 2: keep the semantics, optimize the circuit (ZKLP)

The other camp refuses the trade, and this is the result that should change how this section is
written.

[[zklp]] (*Zero-Knowledge Location Privacy via Accurate Floating-Point SNARKs*) builds
floating-point circuits that are **fully compliant with IEEE 754**, 
validated against the Berkeley TestFloat conformance suite, subnormals and all, by expressing the
awkward parts as **lookups** (LogUp, in gnark) rather than as gates. Because the lookup tables are
shared across operations, the cost *amortizes*:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§1, Introduction"}
The extensive use of lookups leads to amortization — 2¹ single precision floating point (FP32)
multiplications require 209 constraints, whereas 2¹⁵ FP32 multiplications require 64 constraints
per operation.
:::

**Sixty-four constraints, amortized, for a bit-exact IEEE-754 single-precision multiply**, against
the naive gate count quoted two paragraphs up. The "floats are infeasible" premise does not survive
that sentence.

And it gets sharper. ZKLP compares its float circuits not against other float circuits but against
*fixed point*, and finds fixed point **losing**: measured against an unoptimized fixed-point
baseline, "our optimized implementation has 15.9× less constraints utilizing single precision
floating-point values, and 12.2× less constraints when utilizing double precision floating-point
values," because achieving comparable accuracy in fixed point demands so many bits. In that
application, **floating point is the cheaper circuit.** The core trade of this whole document
"give up dynamic range, buy cheap arithmetic", is not a law. It is a bet that can go the other
way.

ZKLP also makes the soundness argument I make in the overflow section above, and makes it harder:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§1, Introduction"}
with randomly generated test cases, fixed-point representation fails some tests whereas
floating-point passes all. Even worse, this inconsistency can be exploited by adversaries to
generate valid proofs for maliciously crafted statements, thereby breaking the soundness of ZKLP.
:::

That is not a precision complaint. They say it of their own protocol; but the mechanism is not
specific to ZKLP. It is the fixed-point/float mismatch, and it is **an exploitable soundness gap
wherever it appears**, found by people who went looking.

:::debate  Is the field's founding premise just wrong?
Every zkML paper in this section justifies quantization by asserting that native floating point is
infeasible in a circuit. That assertion is sourced, when it is sourced at all, to the *naive*
gate-count, and it has been repeated across the literature for years without being rechecked.

The oldest instance of it in this repo is the 2023 [[modulus-cost-of-intelligence]] report, which
states the "fundamental incompatibility" of floats with a finite field as flat assertion, no
citation, no measurement, and it has been passed down ever since. Worth noting too what Modulus
actually says about field size. It is a benchmark report, not a system, it compares Groth16,
Gemini, Winterfell, Halo2, Plonky2 and zkCNN, and the reason it gives for Plonky2 winning on
prover time is not precision but hardware: "elements within the Goldilocks field can be represented
in 64 bits, resulting in faster arithmetic operations on standard hardware." Nowhere in the report
does the choice of field follow from a precision requirement. So the tidy *precision → bit width →
field size* story that [[zkpytorch]] tells (and that this page opened with) looks like a **later
rationalization**: the fast field was there first, and the numerics were fitted to it.

Two papers outside the zkML bubble have now beaten it: one by relaxing IEEE semantics to a
relative-error bound, one by keeping full IEEE compliance and moving the work into lookup
arguments. **Not one system that proves a transformer cites either of them.** [[range-arithmetic]]
lists [[garg-fp]] in its reference section without engaging with it, and that is the whole of the
contact, [[deepprove]], [[zkgpt]], [[zkllm]], [[zkpytorch]] and [[jolt-atlas]] do not mention this
line at all. The one exception is [[zip]], which cites [[garg-fp]] and adopts its relative-error
model wholesale, and [[zip]] is not a transformer prover. See [the bridge](./bridge/) for the
shape of the gap, which is stranger than a simple absence.

**The honest position is not "zkML should use floats."** For an LLM's *matmuls*, integer
sum-check remains overwhelmingly cheaper, 64 constraints per multiply is wonderful next to 8,854
and terrible next to a sum-check that proves a whole matrix product almost for free. The claim
that survives is narrower and more useful: **for the non-linear operators and the
precision-critical seams, exactly the places this document has shown the cost actually lives, 
"floats are infeasible" is an inherited assumption that nobody in zkML has retested against the
current state of the art.** Somebody should.
:::

### ZIP: high precision without paying for it

[[zip]] (CCS '25) is the counter-thesis, and its trick is worth understanding exactly:

1. **Offline**, approximate the activation by a piecewise polynomial, GeLU gets 8 pieces of
   degree 10, and store the coefficients in a lookup table so small that ZIP can say "to prove
   GeLU, ZIP requires 70 table entries. This is one to three orders of magnitude smaller than prior
   schemes."
2. **Online**, the prover computes the activation *exactly, in IEEE-754 double*, and feeds **that
   exact value** forward. The polynomial output is never used downstream, which is what stops
   approximation error from compounding across depth. This is the key move.
3. **Prove** two things: that the correct, correctly-*ordered* block of coefficients was selected
   (an extended Caulk lookup plus a private-interval range proof), and an **approximation-soundness
   relation** binding the exact value $y$ to the polynomial $f(y')$:

$$|y - f(y')| \;\le\; \delta\,|f(y')|$$

enforced division-free by witnessing $l_1 = y - f(y')$, $l_2 = \delta f(y')$ and
$z_3 = (l_1+l_2)(l_2-l_1)$, then proving $z_3 \ge 0$, i.e. $l_1^2 \le l_2^2$. Non-negativity of a
float is just "sign bit is zero or mantissa is zero", which is nearly free.

The result: against the multi-million-constraint naive estimate quoted above, ZIP reports that "to
prove a single GeLU activation ZIP requires 5,830 R1CS constraints", while the value flowing
through the network is a genuine double. The cost of an activation is now decoupled from the
*complexity* of that activation, which is why it generalizes to SeLU and ELU with no redesign. **Quantization
is a design choice made to fit the prover, not a law of nature.**

### But read the guarantee carefully

:::audit  ZIP proves a ball, not a value
**ZIP does not prove that $y$ is the correct IEEE-754 activation of $y'$.** $y$ is a *witness*, and
the only constraint binding it is the relative-error inequality above. What the proof establishes
is that $y$ lies within a **$\delta$-relative ball** around a certified polynomial approximation of
the true activation. An honest prover puts the exact double in that ball. A **malicious** prover
may put anything in it.

And the ball is not tight. ZIP's own experimental parameters: $\delta = 9\times10^{-4}$ for SeLU
and ELU, but $\delta = 9\times10^{-2}$ for **GeLU**, its flagship. That is a **9% per-activation
relative-error budget available to an adversary.** For comparison, bfloat16, the "imprecise"
format from the top of this page, has a machine epsilon of $\approx 7.8\times10^{-3}$, *an order
of magnitude tighter* than the slack ZIP's GeLU proof permits.

**A paper headlined "double precision" has, on its flagship activation, a soundness guarantee
looser than bf16.**

The comparison that sharpens this: ZIP's relative-error relation is **Garg et al.'s**, and Garg et
al. set $\delta$ to *machine epsilon*, the tightest value the model admits, chosen precisely so
the relaxation is invisible. ZIP inherits the machinery but not the parameter. Its $\delta$ is a
piecewise-polynomial *approximation* bound, which is a different quantity from a per-gate rounding
bound and legitimately larger, but the soundness consequence is identical in form and vastly
larger in size.

In fairness: this is not a bug, and the authors do not hide it. Their soundness theorem is stated
with respect to $\hat{F}$, the *approximated* network, and is honestly proved. The gap is between
the colloquial claim ("IEEE-754-compliant inference") and what the constraint system enforces. The
precision is a property of **what the honest server computes**, not of **what the proof enforces**,
and a reader will not necessarily catch the difference.

And it is not only the activations. ZIP's **linear** layers are not exactly bound either, in the
configuration whose timings it advertises: they are checked by a randomized (Freivalds-style)
linear combination *with a relative tolerance* to absorb IEEE-754 rounding. The paper is open that
this is what buys the speed, proving "without RLC and thus preserving full numerical precision"
takes roughly **two to three times longer** than the headline figures. So the advertised
configuration is tolerance-bounded end to end: approximate activations *and* approximate linear
layers.

Whether the slack is *exploitable*, whether an adversary can steer a classification by nudging
each activation within its ball, and whether the error compounds or cancels across layers, is
**not analyzed in the paper**. It is an excellent research question, and it is the numerics
analogue of the Fiat–Shamir situation: the cryptography is sound; the question is what statement
it is sound *about*.
:::

### The honest summary

Four positions, and the field only knows about one of them:

| Approach | What it proves | Cost |
|---|---|---|
| **Naive IEEE-754 emulation** | bit-exact IEEE, incl. rounding | "approximately 1,302,142 R1CS constraints" per GeLU, on ZIP's own estimate. Hopeless. |
| **Relative-error floats** ([[garg-fp]]) | result within $\delta$ of exact; $\delta$ = machine epsilon | Garg et al.: "~57× faster ... for 32-bit floating point numbers, and 236× faster for 64-bit" |
| **Lookup-based exact floats** ([[zklp]]) | **bit-exact IEEE, TestFloat-validated** | ZKLP: "2¹⁵ FP32 multiplications require 64 constraints per operation" |
| **Integer quantization** | the *quantized* network, assuming no overflow | what everyone ships; cost moves into range checks |

The cost of floats did not disappear, it **moved**, exactly as the cost of quantization moved.
Quantization pushed the bill from the arithmetic into the range checks at every rounding seam.
Lookup-based float arithmetic pushes it into a shared table that amortizes. **Neither is free;
both are affordable; and only one of them is in this literature.**

**"Floats are infeasible in a circuit" is no longer true, and the zkML literature has not
noticed.**

## The design space

Everything above collapses to five independent choices:

1. **Where do you put the dynamic range?** An exponent field (expensive per op), extra mantissa
   bits (forces a big field), or nowhere and trust calibration (what everyone does).
2. **How do you kill the arbitrary float scale?** Integer multiplier + power-of-two shift
   ([[deepprove]]), or rational approximation + inequality ([[zkgpt]]). Neither needs a division.
   Or sidestep it: [[bionetta]]'s scale is a power of two *by construction* ($2^{\rho}$), which is
   available to it only because it never has to match a pre-quantized model's arbitrary
   per-layer scales.
3. **How often do you round?** The actual cost driver. Fuse aggressively, and if you can, fuse
   the rounding into a range check you were buying anyway ([[bionetta]]), which is the only way
   anyone has made a seam cost zero.
4. **How do you get non-linearity?** Lookup table ([[zkpytorch]], [[zkllm]], [[jolt-atlas]]),
   polynomial approximation ([[zip]]), or restrict the model so you don't need one
   ([[safetynets]]' quadratics, [[bionetta]]'s ReLU family), noting that these two "restrict the
   model" answers restrict it in *opposite* directions, and the debate above is about which one is
   actually cheap.
5. **Do you prove range, argue range, or assume range?** Most of the field assumes. That is where
   the bodies are buried.

And one closing observation. [[safetynets]], the oldest system here, has **no rescale seam at
all**: quadratic activations are polynomial, so the whole network is one arithmetic circuit with
no rounding anywhere. Its prover overhead over unverified execution is a few percent. Every LLM
prover here is orders of magnitude worse, [[deepprove]] puts its own cost at
"roughly 24× slowdown" against plaintext GPT-2, and at "almost three orders of magnitude" on
short-output prompts. That gap is not only the price of zero-knowledge and commitments, which
SafetyNets does not provide. **A large part of it is simply the price of rounding**, the cost of
insisting the model may be an arbitrary network rather than one the prover got to choose.

:::debate  Does a polynomial network really have no seam? Bionetta says the seam just moves.
That closing observation is the one I would most like to be right, and [[bionetta]] is the reason
I am no longer sure it is.

Bionetta considers polynomial activations explicitly, Π-nets, the same family SafetyNets
belongs to, and **rejects them**, for a reason that is precisely this page's reason. A degree-$d$
polynomial costs only $d$ constraints per value, which looks like a bargain. But evaluating it
*multiplies the precision*: a value carrying $\rho$ fractional bits, raised to the $d$-th power,
carries $\rho d$ of them. Stack a few layers and the accumulator walks straight into the modulus.
So you must insert a precision cut, and a precision cut costs $\approx b$ constraints, which
swallows the $d$ you saved. In Bionetta's words, the benefit of $d$ constraints per value *is lost
in the overhead of precision cuts*.

**A polynomial activation does not abolish the rescale seam. It relocates it, from the
non-linearity to the precision blow-up the non-linearity causes.**

Both claims are in this SoK and neither paper has read the other. The reconciliation is probably
depth: SafetyNets' networks are shallow enough, and its Mersenne field wide enough, that the
$2^{\text{depth}}$ precision growth never reaches the modulus, it *analytically rules out* scaling
factors that would overflow, which is posture 2 in the overflow section below, and it works because
the model is small. Bionetta is describing what happens when you try to take that trick to a real
network. If that is right, then SafetyNets' few-percent overhead is not a standing indictment of
everything since; it is **a number that only exists at a depth nobody wants to deploy**, and the
"price of rounding" is not optional after all, it is what you pay the moment the network is deep
enough to be useful.

Somebody should settle this. It is one experiment: take SafetyNets' quadratic network, scale the
depth, and plot where the precision cuts become unavoidable.
:::

## Why ZK cannot borrow MPC's shortcut

One more thing worth settling, because it looks like free money and is not.

MPC has been rescaling fixed-point values for a decade, and it has a much cheaper trick: the
**probabilistic truncation** of SecureML and ABY3, which is non-interactive and therefore far
faster than an exact protocol. The obvious question is why ZK does not simply adopt it, especially
since, as [the bridge](./bridge/) shows, ZK has *already* adopted plenty of other MPC numerics
without saying so.

The answer is in its failure mode, and it is not the one people assume. Probabilistic truncation
is not "occasionally off by one". When it fails, it fails *badly*, a wraparound producing, as
[[prob-truncation]]'s analysis of these protocols puts it, **"a large error"**, with some small
probability per operation.

In MPC's usual threat model, a rare large error is an *accuracy* problem: it degrades the model,
you bound the probability, you move on. **In ZK it is a soundness problem**, and a much worse one,
because the prover is adversarial and gets to *choose the inputs*. A failure mode that occurs with
small probability on random data is not rare at all when someone is hunting for it. Every
structural advantage MPC gets from accepting a small error probability, ZK must forfeit, the
adversary would simply steer into it.

This is the cleanest illustration of the theme running through this whole page: **the same
arithmetic problem has different answers under different threat models**, and numerics techniques
do not transfer across that boundary for free.

### And the two truncations sit side by side in the same literature

We made that argument for a long time without reading the papers it is about. Both are now in the
corpus, and they turn out to be a matched pair, which is better than the argument deserved.

**[[cheetah]] is the probabilistic one, and it is explicit.** It *deliberately* keeps a 1-bit
truncation error with probability $\tfrac12$, discarding only the "harsh" error, and it buys
$13\ell$ bits of communication where a faithful protocol costs
$\lambda(\ell + f + 2) + 19\ell + 14f$. That is the MPC bargain, stated in the open: accept a
bounded benign error, pay far less. And it is exactly the bargain ZK must refuse, because in ZK the
prover chooses the input and a coin that lands badly half the time is not a rare event, it is a
lever.

**[[sirnn]] is the exact one, and it is also cheap.** All four of its truncation flavours (logical
shift, arithmetic shift, truncate-and-reduce, C-style division by a power of two) compute the wrap
and borrow terms *exactly*. Nothing in the paper fails with any probability. And
truncate-and-reduce costs about $\lambda(s+1)$ bits, roughly **4.5× less than a garbled circuit**.

So the MPC world did not only have the shortcut ZK cannot take. **It also had the exact protocol,
and the exact protocol is fast.** That is precisely the one the ZK papers borrowed, which is why the
borrowing was possible at all, and it is why the shortcut is the *exception*, not the rule.

**Probabilistic truncation is the one technique the threat model genuinely forbids. It has been
mistaken for the whole relationship.**

But do not over-read it. This is an argument about *one* technique, not a licence for the two
columns to ignore each other, and the [bridge](./bridge/) page shows that the ones who bothered to
look transferred a great deal. [[hao-et-al]] proves exponentials and reciprocal square roots in ZK
using [[sirnn]]'s digit decomposition, [[sirnn]]'s Goldschmidt iteration, and [[sirnn]]'s parameter
settings, citing it **five times in its body**.
Probabilistic truncation is the *exception* that the threat model forbids; it has been mistaken for
the rule.

## Open questions

Ranked by how much I would want the answer.

1. **Is bit width actually the expensive knob, or is it the number of seams?** [[deepprove]]'s
   near-free precision increase says cost tracks the *count* of rounding seams, not their *width*.
   **[[bionetta]] now says the same thing from a different proof system**, four orders of magnitude
   of accuracy for zero extra constraints, because its decomposition is over the field element and
   not over the value. Two independent systems, one answer, and no citation between them. If it
   generalizes, the field has been trading accuracy for a saving that was never there. Directly
   testable, still the highest-value experiment here, and it now has a hypothesis worth stating
   sharply enough to fail: *precision is paid for in seams, not in bits.*
2. **Can an adversarial input force an overflow?** Most systems prove correctness *conditional on*
   intermediates staying in range and never prove the condition. Outliers in transformers are
   emergent and documented, not accidental. [[deepprove]] and [[jolt-atlas]] at least *bound* the
   accumulator; nobody asks whether an adversary can *reach* the bound.
3. **Is [[zip]]'s $\delta$-ball exploitable?** Nine percent of relative slack per GeLU, and no
   analysis of whether it compounds or cancels across layers.
4. **Has anyone retested "floats are infeasible" since [[zklp]]?** A bit-exact FP32 multiply for a
   few dozen amortized constraints is a different world from the naive gate count the literature
   still cites. No system that proves a transformer cites either float-SNARK line.
5. ~~**Does a polynomial network escape the rescale seam, or only postpone it?**~~ **Answered, and
   the answer was in an MPC paper the whole time.** [[safetynets]]' few-percent overhead is the
   whole basis for calling everything since "the price of rounding", and [[bionetta]] argued that a
   degree-$d$ activation inflates precision by $\rho d$ and forces the seam back. We asked for one
   experiment: scale the depth of a quadratic network and find where it breaks.

   **[[delphi]] ran it in 2020.** Not as a numerics experiment, as a *training* experiment, because
   Delphi wanted quadratic activations for a completely different reason (they cost 192× less online
   communication than a garbled circuit). What it found:

   :::quote{src="Delphi" sec="§5.1, Adapting NAS for DELPHI's planner"}
   Prior work [Moh+17; Gil+16; Gho+17; Cho+18] and our own experiments indicate that networks that
   use quadratic approximations are challenging to train and deploy: the quadratic activations cause
   the underlying gradient descent algorithm to diverge, resulting in poor accuracy.
   :::

   `[Gho+17]` **is SafetyNets.** Delphi needed gradient clipping, ReLU6, and a "gradual activation
   exchange" annealing schedule just to make quadratic networks converge at all, and *even then* it
   runs a neural architecture search to keep **most** activations as ReLUs, because it cannot afford
   to replace them.

   So the all-quadratic network **does not train**. SafetyNets' famous ~5% overhead is a number that
   exists at a depth and width nobody would deploy. **The price of rounding is not optional. It is
   what you pay the moment the network is big enough to be worth anything**, and the floor of this
   field is higher than this page has been saying.

   That the answer sat for six years in a privacy-column paper cited by nine of our own PDFs is the
   [bridge](./bridge/) page's entire thesis, delivered as a punchline.

:::gap  It is not a third island, it is the seabed
The obvious way to write this up is: *the zkML and MPC clusters are disconnected, and the
float-in-ZK line is a third island adjacent to both and read by neither.* That is what we believed
before the graph was rebuilt, and it is wrong.

The numerics layer is not a third cluster. **It is the one place the other two touch.** All three
nodes that both columns cite, SIRNN, Cheetah, and [[secfloat]], are MPC numerics primitives, and
the ZK papers that reach for them are precisely the ones whose subject matter *is* arithmetic
([[garg-fp]], [[zklp]]), or whose engine is an MPC protocol ([[zkpot-garg]]), or which prove
operators rather than models ([[hao-et-al]]).

What survives, and is worse than the island story: **the borrowing happens entirely at the edges.**
Every system at the centre of the verifiability column, [[deepprove]], [[zkgpt]], [[zkllm]],
[[zkpytorch]], [[jolt-atlas]], and now [[bionetta]], reaches into none of it, and
justifies quantization with a claim about floating point that the floating-point specialists
refuted years ago, in papers two citations away from work it already cites. ([[zip]] is the
exception that proves the point: it is the one system here that *refuses* quantization, and it is
also the one that reads [[garg-fp]] and builds on it.) [[bionetta]] is the sharpest case yet,
because it did not merely *skip* the arithmetic literature: it sat down and
**re-derived a fixed-point quantization error bound from first principles**, in an appendix, in
2025, in a field where [[secfloat]] has shipped a library for exactly that since 2021. A full-text
scan of its PDF returns zero occurrences of "MPC", "homomorphic", "SIRNN", "Cheetah" or "SecFloat".
The bridge exists. Nobody in the middle walks it.
[Full argument, with the caveats it needs](./bridge/).
:::
