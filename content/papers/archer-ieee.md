---
title: Archer et al. — the cost of IEEE arithmetic
paper: archer-ieee
status: reviewed
---

## What is new

The first careful measurement of what **IEEE-754 compliance actually costs in secure computation**,
set against the two real-number approximations the MPC world had settled on instead: Catrina–Saxena
fixed point, and MPC "floating point" (which is not IEEE floating point). The authors compile
IEEE-compliant double-precision addition, multiplication and division to Boolean circuits, run them
under binary-circuit MPC, run the LSSS-based approximations under Scale-Mamba, and compare.

The paper's importance to this SoK is entirely secondhand: **it is where the double-precision gate
counts come from.** When [[zip]] argues that hardcoding IEEE-754 into a circuit is hopeless, and when
[[zklp]] tabulates the naive-emulation baseline it beats, both are quoting Archer. It is upstream of
the numerics argument in the verifiability column, and almost nobody who cites it has read it.

Its own conclusion is not the one it gets cited for:

:::quote{src="Archer et al." sec="Abstract"}
We compare the relative performance, and conclude that the addition cost of IEEE compliance maybe too
great for some applications. Thus in the secure domain standards bodies may wish to examine a
different form of real number approximations.
:::

That is not "use fixed point." That is *"the secure-computing community should go and design a better
real-number standard,"* which is a live research call and not a settled verdict.

## What it actually proves

Nothing — it is MPC, and it produces no proof. There is no prover, no verifier, no soundness
argument; the string "zero-knowledge" does not appear anywhere in the paper.

What it *measures* is gate counts and wall-clock for three IEEE-754 double-precision operations under
**binary-circuit MPC** (garbled circuits, and Q2-access-structure LSSS modulo 2), against
**arithmetic-circuit MPC** over `F_p` for the approximations. Its headline table gives AND, XOR and
INV counts, plus AND-depth, for `add`, `mul` and `div`.

## What to distrust

Not the paper. The paper is careful, honest and says exactly what it measured. What deserves
suspicion is **how the verifiability column quotes it**, and there are two distinct problems.

**One: the cost model does not transfer, and Archer says so.** These are gate counts for *Boolean*
circuits under *MPC*. In that setting XOR is often free and the real cost is depth, which the authors
state outright:

> since when operating in the Q2-domain using an LSSS-based MPC engine modulo 2 the dominant cost is
> not the number of AND gates but the **depth** of the AND gates in the circuit.

So even inside its own paper, the gate *count* is not the figure of merit. Transplanting a total gate
count from garbled-circuit MPC into a claim about *SNARK constraint counts* — a completely different
arithmetization, with a completely different cost model, over a large prime field rather than `F_2` —
is a category error. The conclusion it is used to support (floats are expensive in a circuit) may well
be right; this is simply not evidence for it in the form it is being used.

**Two: the number that gets quoted is the largest of several defensible ones.** The figures that
[[zip]] and [[zklp]] both reproduce for FP64 are the **AND + XOR + INV totals**, summed across the
rows of Archer's table. Both secondhand quotes are arithmetically correct — we checked, and
`papers.yml` records the derivation. But the AND-only cost, which is what most MPC and ZK settings
actually pay for, is a few times smaller; and by Archer's own argument neither is the right metric
for their engine.

So when the zkML literature cites a five-figure gate count for a double-precision multiply as proof
that floating point is hopeless, it is citing **the largest of several defensible numbers, from a
cost model that does not apply, in support of a conclusion the source paper does not draw.** The
conclusion may survive all of that — a few thousand AND gates is still enormous beside a field
multiply, and nothing here threatens sum-check on integer matmuls. But the figure deserves its
asterisk, and it has never been given one.

:::gap What Archer actually asked for, nobody built
Archer's closing recommendation is that standards bodies design a real-number approximation *tailored
to the secure domain*, rather than importing IEEE-754 wholesale or falling back on ad-hoc fixed point.

Read the numerics cluster as a set of uncoordinated answers to that call. [[garg-fp]] relaxes the
semantics to a relative-error model. [[zklp]] keeps IEEE and moves the hard parts into lookups.
[[range-arithmetic]] keeps fixed point and proves the rounding arithmetically. [[secfloat]] rebuilds
the operations from crypto-friendly integer primitives. Four incompatible proposals, in two
literatures that do not cite each other, and no standard.
:::
