---
title: The non-linearity problem, twice
section: private-inference
order: 30
lede: >-
  Matmul is easy and GELU is hard -- in both columns of the 2x2, for different reasons,
  with different hammers. The MPC papers and the zkML papers are solving the same three
  operators and have never cited each other once.
papers: [iron, ciphergpt, bolt, nimbus, bootstrapping-fhe, deepprove, zkgpt, zkllm, jolt-atlas, zkpytorch, safetynets]
status: draft
---

Under homomorphic encryption you get addition and multiplication. Under secret sharing you get
addition for free and multiplication for a round of communication. Both of those are enough to
compute a matrix product, which is why the linear layers of a transformer -- the overwhelming
majority of its FLOPs -- are the *easy* part of private inference, and why four of the five
systems in this section spend their linear-layer contribution on packing tricks rather than on
anything conceptually hard.

Then you reach $\mathrm{GELU}(x) = 0.5x\left(1 + \tanh\left[\sqrt{2/\pi}\,(x + 0.044715x^3)\right]\right)$,
and Softmax, which needs $\exp$ and a division, and LayerNorm, which needs a reciprocal square
root. None of these is a polynomial. Every one of them has to be *approximated*, and the shape of
that approximation is what every paper in this section is actually about.

If that framing sounds familiar it is because it is the same sentence you would write about
[[zkgpt]] or [[deepprove]]. Hold that thought; the last section of this page is about it.

## Five strategies, in rough historical order

**1. Multi-step lookup tables over OT.** [[iron]] builds Softmax, GELU and LayerNorm out of
SIRNN's protocol library: a lookup table for $e^{-x}$, another for the reciprocal, then bit-width
extensions and truncations to keep precision through the composition. The virtue of this approach
is that it is *numerically precise* -- [[iron]] preserves the plaintext model's accuracy exactly,
and it is the only system here that can say so without an accuracy table. The cost is that each
step is an OT invocation, and the steps compose.

**2. Piecewise high-degree polynomials.** [[bolt]] replaces the lookup chains with polynomial
approximations of GELU and the Softmax exponential, exploiting the symmetry and linearity of the
curves, and adds a Horner-scheme preprocessing trick that roughly halves the multiplication count
when the coefficients are known in advance. Degree buys accuracy; each degree costs multiplications
and therefore rounds. [[nimbus]] reports that this generation of work settled on four pieces of
degree six for GELU and a degree-six Taylor expansion for the exponential -- and that the resulting
fixed-point error forced everything onto a large ring.

**3. Splines: piecewise *linear*, with a lookup to select the piece.** [[ciphergpt]] observes that
GELU is flat on the left, linear on the right, and only genuinely curved in a narrow band around
zero. So it splits that band into equal-length intervals, fits $y = ax + d$ on each, right-shifts
the whole curve so the band starts at zero (which avoids having to determine the sign first), and
then **indexes a lookup table by the top bits of the shifted input** to recover the interval's
coefficients. Precision goes up, degree goes to one, and the shape of the object is a table lookup
keyed on a range check.

**4. Fit the approximation to the input distribution, not to the function.** This is [[nimbus]]'s
contribution and it is the cleverest idea in the section. Prior work minimises approximation error
uniformly over an interval, as if every input value were equally likely. [[nimbus]] measures the
actual activation distribution at each encoder layer on a batch of training data, and minimises
the *probability-weighted* error instead:

$$\min_{f'} \int_{l}^{h} p(x)\left[f(x) - f'(x)\right]^2 dx$$

Because GELU's inputs cluster where the curve is nearly linear, the budget can be spent almost
entirely on the narrow high-probability, high-curvature band -- which lets [[nimbus]] drop to a
single quadratic piece where prior work used two pieces of degree three and six, and then to drop
the ring size and the fixed-point scale as well, because low-degree polynomials accumulate less
error. The breakpoints are re-searched per layer depth, since the distribution shifts as you go
deeper.

**5. Change the model so the operator goes away.** THE-X swaps GELU for ReLU and Softmax for
ReLU-plus-polynomial. MPCFormer does something similar. [[bootstrapping-fhe]] replaces LayerNorm
with Dynamic Tanh ($y = \alpha \cdot \tanh(\beta x) + \gamma$) and distils a BERT-DyT student from
the original BERT. This is the least discussed and most consequential category, because the system
you benchmarked is no longer the model you were asked to run.

**6. Fuse the approximation into bootstrapping.** [[bootstrapping-fhe]] is the only FHE system
here and it inverts the whole problem. In CKKS, evaluating anything eventually exhausts the
multiplicative budget and forces a bootstrap, and bootstrapping is the dominant cost of the
non-interactive setting. Rather than minimise bootstraps, it makes each one do more work:
*functional bootstrapping* embeds the target function into the periodic function that the bootstrap
already evaluates, so the non-linearity is computed *inside* the noise refresh instead of before
it. The approximation is a **trigonometric minimax** fit -- the prior state of the art used a
Fourier series, which is optimal in $L^2$ but not in $L^\infty$, so [[bootstrapping-fhe]] proves
existence of a trigonometric minimax approximant and derives a trigonometric Remez algorithm to
find it. Worst-case error is the right metric when the failure mode is one bad activation, which
is a point the zkML side would recognise instantly.

:::debate  Is bootstrapping the bottleneck or the answer?
[[bolt]] chose *leveled* BFV specifically to avoid bootstrapping, calling it "still prohibitively
expensive." [[bootstrapping-fhe]], two years later, argues that bootstrapping is the only sane
place to put the computation and that everything else should be fused into it. Both are published;
neither has been refuted; they are not benchmarked against each other because they are not in the
same setting (see the threat-models page). The field has not resolved which of these is the right
bet, and the papers do not engage.
:::

## The same operators, from the other side of the table

Now put the two columns of the 2x2 next to each other.

| Operator | What the zkML papers do | What the MPC/FHE papers do |
|---|---|---|
| **GELU** | lookup argument over a table sized by bit width ([[zkllm]]'s `tlookup`); result-as-witness plus a range proof ([[zkgpt]]); a lookup table baked into the ONNX op ([[jolt-atlas]]) | LUT chain over OT ([[iron]]); high-degree piecewise polynomial ([[bolt]]); spline + LUT on the high bits ([[ciphergpt]]); distribution-weighted low-degree piecewise ([[nimbus]]); functional bootstrapping ([[bootstrapping-fhe]]) |
| **Softmax / exp** | bespoke attention argument ([[zkllm]]'s `zkAttn`); lookup tables ([[zkpytorch]]); result-as-witness ([[zkgpt]]) | OT lookup for $e^{-x}$ and reciprocal ([[iron]]); Taylor/piecewise polynomial ([[bolt]], [[nimbus]]); FBS ([[bootstrapping-fhe]]) |
| **LayerNorm** | proved via auxiliary witnesses -- quotient plus remainder-less-than-divisor ([[zkpytorch]]) | reciprocal-sqrt via OT ([[iron]]); folded into HE weights ([[bolt]]); **replaced by Dynamic Tanh** ([[bootstrapping-fhe]]) |
| **Matmul** | cheap: sum-check is linear in the gate count | cheap: HE packing, or one round of secret-shared multiplication |
| **Where cost actually lands** | prover time and memory on the non-linears | communication rounds, or bootstraps, on the non-linears |

Every row is the same shape. Both worlds have concluded that the linear algebra is free and the
three transcendental operators are the whole problem. Both have converged on **piecewise
approximation selected by a table indexed on the high bits of the input** as the central technique
-- which is what a lookup argument is, and which is also what [[ciphergpt]]'s spline GELU is. Both
have discovered that the *range* the approximation is calibrated on is the real design parameter:
[[deepprove]] calibrates its quantization scales on data, [[nimbus]] fits its polynomials to the
observed activation distribution, and both are making the same bet that inference-time activations
look like the calibration set.

:::audit  The calibrated range is the shared attack surface
In a zkML lookup design, an activation outside the calibrated table range is not merely inaccurate
-- it is unprovable, or worse, provable under an under-constrained range check
(see the quantization audit surface). In [[nimbus]], an activation outside the fitted band gets
whatever the constant or linear tail piece returns, silently, with no error signal and no bound
that anyone has published. The two failure modes are duals of each other and neither literature
has connected them.

[[nimbus]] does argue that the fitted polynomial leaks nothing, because the client never sees it.
That is a claim about *privacy*, and it is correct. It is not a claim about what the polynomial
does on an out-of-distribution input, which is what an auditor would ask.
:::

## The citation graph is empty between them

This is not a subtle observation about intellectual affinity. It is a fact about the reference
lists, and you can see it in the graph.

{{ chart:citations }}

Two connected components, zero edges between them:

- **Proving inference** cites GKR, Lasso, Jolt, zkCNN, Mystique, EZKL, and each other.
  [[deepprove]] cites [[zkgpt]], [[zkllm]], [[zkpytorch]]; [[jolt-atlas]] cites [[deepprove]].
- **Private inference** cites Cheetah, SIRNN, THE-X, BumbleBee, and each other. [[nimbus]] cites
  [[bolt]], [[ciphergpt]], [[iron]]; [[bootstrapping-fhe]] cites all four of the 2PC systems.

Not one paper in either cluster cites a paper in the other. They are working the same two cells of
the same row of the same table, on the same three operators, on the same model (BERT/GPT-2 class),
and they are publishing at the same venues.

:::gap  Nobody has tried the obvious transfer
Concrete questions that fall out of the disconnection, none of which anyone has asked in print:

- **Does [[nimbus]]'s distribution-aware fitting improve zkML lookup tables?** A zkML table is
  sized by the *range* it must cover, and its cost is exponential in the input bit width. Spending
  the table budget where the activations actually are -- rather than uniformly across the range --
  is exactly [[nimbus]]'s move, and the cost model that rewards it (table size) is even more
  punishing than the one it was invented for.
- **Does [[ciphergpt]]'s spline decomposition beat the lookup tables in [[jolt-atlas]]?** They are
  the same object: index a table on the high bits, evaluate a degree-1 piece on the low bits.
  Nobody has compared them.
- **Is trigonometric minimax the right approximation basis for a proof system too?** The argument
  [[bootstrapping-fhe]] makes for $L^\infty$ over $L^2$ -- worst case is what matters when one bad
  activation ruins the run -- applies verbatim to a quantized prover.
- **And in the other direction:** [[safetynets]] restricted the network to quadratic activations to
  make the *proof* cheap, in 2017. The MPC line rediscovered the same restriction, for the same
  operator-cost reason, and calls it "polynomial approximation."
:::
