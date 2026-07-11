---
title: ZEN
paper: zen
status: reviewed
---

## What is new

ZEN is the first paper in this collection to argue that **the network, not the prover, is the
thing to optimize**. Everything in the [[safetynets]] → [[zkcnn]] → [[zkllm]] lineage attacks the
argument system; ZEN leaves the argument system alone (arkworks Groth16 over BLS12-381, entirely
off the shelf) and instead compiles a floating-point PyTorch model into an R1CS circuit that is
*cheap to prove because of how it was quantized*. The paper is explicit that this is the bet:
"the selection of underlying zero-knowledge proof systems is largely orthogonal to our ZEN
design."

Three techniques, and the first two are the ones worth carrying forward.

**Sign-bit grouping.** Affine quantization gives you $Q_Y = z_Y + M(Q_W - z_W)(Q_X - z_X)/2^k$,
where the two bracketed factors can go negative — and a negative intermediate in a prime field
means a bit-decomposition to recover the sign, which is where the constraints go. ZEN rewrites the
matrix product by *grouping operands of the same sign*, using associativity, so that both sides of
the equation are guaranteed non-negative and the element-wise zero-comparisons disappear
altogether. No approximation is involved: it is an algebraic identity.

**Remainder-based verification.** The `/2^k` rescale is an integer division, which R1CS cannot do
natively. Rather than bit-decompose the dividend, ZEN has the prover supply the remainder as a
witness and constrain `dividend = quotient·divisor + remainder` with `remainder < divisor`. This
is the same auxiliary-witness trick [[zkpytorch]] would rediscover four years later for division
and softmax, and it is the ancestor of the *result-as-witness* paradigm [[zkgpt]] builds on.

**Stranded encoding.** A SIMD trick: a BLS12-381 field element is ~254 bits and the activations
are 8 bits, so pack several dot products into one pair of field elements,
$x_i = \sum_j a_{j,i}\delta^{\phi(j)}$, chosen so that $\sum_i x_i y_i$ has the $s$ separate dot
products sitting in non-overlapping digit ranges of the result. The real contribution here is
negative and honest: naive stacking loses, because extraction costs more than the packing saves.
ZEN formulates the packing as a discrete optimization problem, derives a cost model, and lets the
compiler pick the batch size per kernel. It is the smallest of the three wins.

The framing that has aged best is the last line of §1.2: co-design the domain algorithm and the
constraint compilation, rather than improving the backend. That sentence is the [[zkpytorch]] and
[[jolt-atlas]] research programme, written in 2021.

## What it actually proves

Two schemes, and they are genuinely different claims — this is one of the few systems that
straddles the *inference* and *testing* objectives, and the only one in that pair that defines
both formally.

**ZEN-infer** proves: *this committed model, on this committed input, produced this output.* The
weights stay hidden (Pedersen commitment, statistically hiding), the input stays hidden, the result
is revealed. One image, one forward pass. No batching, no sequence, no autoregression — these are
CNNs.

**ZEN-acc** proves: *this committed model achieves this accuracy on the testing set you just sent
me.* It is an interactive setup protocol — the prover commits first, the verifier then supplies the
dataset and labels as a challenge, and the accuracy is the public output. That challenge structure
is the right shape for the claim, and it is a better-specified testing protocol than most of what
followed.

**The accuracy claim is measured, not asserted — but it is measured against the wrong baseline in
the abstract.** Table 7 gives floating-point accuracy, quantized accuracy, and the delta, for all
six models. That is exactly what this SoK asks of a quantization paper, and ZEN is one of the few
that supplies it. However, the abstract's headline — savings "without any accuracy loss" — is *not*
a claim about floating point. It is a claim relative to ZEN-vanilla, i.e. relative to the
Jacob et al. quantization scheme ZEN reimplements as its baseline. The paper says so in §4.2, in a
sentence that never makes it to the abstract:

:::quote{src="ZEN" sec="§4.2, R1CS Friendly quantizations"}
As a result, our techniques incur similar accuracy loss as [JKC+18]. Nonetheless, we note that
[JKC+18] itself introduces accuracy loss.
:::

So the correct reading is: ZEN's *own optimizations* are semantics-preserving (true, and provably
so — they are algebraic identities), and the residual accuracy cost is whatever int8 quantization
costs, which Table 7 measures and which is small on these models. Both halves are honest. Only the
composition, as compressed into the abstract, is not.

## What to distrust

:::audit The headline constraint saving excludes the largest term in the circuit
Table 3 has four columns: **Commitment**, **ZEN-vanilla**, **ZEN-infer**, and **Saving**. The
saving column is `vanilla / ZEN-infer` — it divides the *neural-network* constraints only. The
commitment column sits right next to it and is not in the ratio.

But the commitment circuit *is inside the proved circuit*. You can verify this from the paper's own
tables without any outside information: for every one of the six models, Table 3's
`Commitment + ZEN-infer` reproduces Table 1's total constraint count, to the rounding.

And for the smaller models the commitment **dominates**. On ShallowNet-MNIST the commitment
constraints exceed the optimized network constraints by more than an order of magnitude, so
dividing the *whole* circuit before by the whole circuit after leaves a saving that rounds to
nothing. Recomputing end-to-end across all six rows, the real range is a low single-digit factor —
against a headline of 5.43–22.19×.

None of the arithmetic is hidden; the paper prints every number needed to do it and simply does not
do it. But `papers.yml` and the README both carry the 5.43–22.19× figure as ZEN's contribution, and
it is a per-kernel figure, not an end-to-end one.

The finding also has a forward pointer. The reason the commitment is so expensive is that ZEN
proves the Pedersen commitment *in-circuit*, and that is precisely the bottleneck [[artemis]] would
attack three years later, cutting commitment-verification overhead on VGG by an order of magnitude.
ZEN's Table 3 is the earliest measurement of the problem Artemis exists to solve, and ZEN does not
notice it.
:::

**The largest model's numbers are estimates, and the paper marks them with an asterisk.** In both
Table 1 and Table 2, LeNet-Face-large's setup time, prove time, verify time and CRS size carry a
`*` — "indicates an estimated value." The proving time and CRS size in particular are round numbers.
`papers.yml` correctly quotes only the measured range, and it should stay that way; anyone citing
ZEN's largest-model cost is citing an extrapolation.

**ZEN-acc's reported time is not the time to prove ZEN-acc's reported circuit.** The constraint
counts in Table 2 "consist of the commitment to the neural network model, the inferences on 100
images, and a commit to the final accuracy." The runtimes in the same rows do not. Footnote 6:

:::quote{src="ZEN" sec="§6.4, footnote 6"}
We record the time spent on model commitment, inference on one image plus the final accuracy
commitment check circuit as the ZENacc execution time.
:::

One image, in a table whose constraint column is priced for a hundred. The two columns of Table 2
are measuring different circuits, and the paper does not flag it in the body. Any *testing*-objective
comparison that uses ZEN's proving time against, say, [[zkdt]] or [[pvcnn]] — both of which prove
over a real test set — is comparing a hundred-sample claim to a one-sample cost.

**The models are too weak for the accuracy claim to transfer.** ZEN's CIFAR-10 networks are LeNets,
and Table 7's floating-point column has them scoring closer to a coin toss than to a usable
classifier — this is nowhere near a model anyone would deploy. Quantization damage generally grows
with model capability, so a scheme shown to preserve the accuracy of a weak model has not been shown
to preserve the accuracy of a strong one. The delta column in Table 7 is also non-monotone — the
*largest* model's quantized accuracy comes out **above** its floating-point accuracy — which is the
signature of a curve sampled inside its own noise, exactly as in [[deepprove]]'s and
[[safetynets]]'s quantization tables.

**A spec-level bug in ZEN-infer's definition.** §3.2 declares
`ZENinfer.Prove(pk, a, r, s, Q)` with two openings `r` and `s`, then commits with
`cm_a ← COMM(r, a)` and `cm ← COMM(r, Q)` — the *same* randomness for both Pedersen commitments,
with `s` never used. Almost certainly a typo, and the open-source implementation is where you would
settle it, but as printed the scheme reuses an opening across two commitments, which is not a thing
a hiding argument gets to do casually. The same section also calls `a` a "public input" one
paragraph before committing to it and claiming input privacy.

**Bit width was recoverable and the repo had it as unknown.** ZEN is an **8-bit** system —
uint8 activations and weights, packed into a ~254-bit BLS12-381 field element, which is the entire
premise of stranded encoding. The README's quantization table listed ZEN's bit width as `?`. It is
not stated in a "we use 8 bits" sentence, which is presumably why it was missed, but it is
unambiguous from §1.2 and §5. Fixed in `papers.yml`.

**And the price of the smallest proof in the table.** Groth16 gives ZEN a constant-size proof — the
smallest of any system in the inference table, by a wide margin — and it is bought with a per-circuit
trusted setup whose common reference string runs to gigabytes on the mid-size models and, by the
paper's own estimate, to hundreds of gigabytes on the largest. The proof is tiny; the ceremony is
not, it is model-specific, and it must be redone whenever the weights change. That is the trade the
proof size is hiding, and it is why nothing after 2021 in this table uses Groth16.
