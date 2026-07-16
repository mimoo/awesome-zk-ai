---
title: Remainder
paper: remainder
status: reviewed
---

## What is new

Remainder is best understood as **one GKR engine with two lives**, and separating them is the
most useful thing this note can do, because the paper and the shipped code prove different things,
on opposite threat models, and only one of them has numbers.

**Life one: the paper (Modulus Labs, March 2024): verifiable decision *forests*.** Not a neural
net. The paper proves that a **gradient-boosted decision forest** ran correctly, via a structured,
data-parallel GKR circuit committed with Ligero and made non-interactive with a Poseidon
Fiat–Shamir. Its motivating deployment is an on-chain price oracle:

:::quote{src="Remainder" sec="§1.2"}
As a concrete example, Upshot Technologies applies a very large decision forest model to the task
of asset appraisals. For their first on-chain price oracle, a model composed of over 2500
gradient-boosted decision trees is used to predict granular prices for individual NFT assets.
:::

The two technical contributions are real and measured: a **multi-stage claim-aggregation
optimization** that sharpens the interpolation strategy of Thaler13, and a **data-parallel
generalization of the linear-time prover** from XZZ+19 (the paper calls it "Libra-Giraffe"). It
descends from [[zkdt]]'s structured-circuit idea, but proves each tree path by sum-check rather than
by a matrix-subset argument, squarely inside the [tree line](../../zk-inference/vision-and-trees/)
of this SoK, not the CNN line.

**Life two: the code (`Remainder_CE`, 2026, now Worldcoin): a client-side iris prover.** The same
GKR engine, carried into Worldcoin/Tools for Humanity after it acquired Modulus Labs, and pointed at
a completely different job. We established this not from a README but from a source-reading workflow
over the actual crates (`shared_types` → `prover` → {`ligero`, `hyrax`} ← `frontend`). What it now
proves: that a **private iris image** was correctly transformed into a Worldcoin iris code by a
**public** Gabor-style linear filter bank, and then Shamir-secret-shared to a 3-party MPC. Two
things the paper did not have appear here:

- a **Hyrax/Pedersen zero-knowledge wrapper** (BN256 G1) as a second commitment backend, plain
  GKR+Ligero is *not* zero-knowledge, so ZK is entirely this layer's doing;
- an **inverted threat model**, see below.

## What it actually proves

Read the two lives against the [privacy modes](../../landscape/): they sit on opposite ends of the
same switch, and the switch is a per-input-layer `Committed | Public` visibility flag.

- **The paper hides the model.** Upshot's forest weights are IP; the model owner commits them once
  and attaches a GKR proof to each appraisal. Classic MLaaS, the prover is the model owner, the
  secret is the weights, the client is the verifier. This is the **🔒model** end.
- **The code hides the input.** The iris filter bank is *public* (baked into the circuit as
  constants); the secret is the user's biometric, and the proof is generated **client-side** on the
  user's device. This is the **🔒input** end, the same inverted setting as [[bionetta]], reached
  by a completely different proof system.

Same engine, inverse guarantee. Nothing about "Remainder proves X privately" is true without saying
which life you mean.

## What to distrust

**The deployed workload has no published performance numbers, at all.** The only benchmark in the
primary source is the 2024 *decision-forest* figure:

:::quote{src="Remainder" sec="Abstract"}
we are able to create GKR proofs for a decision forest of 128 trees, each of height 9, over a set of
128 inputs, each with 64 features, in under 54 seconds. Notably, this represents a per-tree-per-sample
proof time of just over 0.003s, representing a mere 180x prover-side blowup with respect to simply
running the computation on CPU.
:::

That number is for a workload **nobody deploys anymore**. The workload that *is* deployed, the iris
pipeline, is unmeasured in public.

:::audit  The only figure in the shipped code is a memory *target*, not a proving cost
The `Remainder_CE` repository states no proving time, no proof size, and no verifier time for the
iris pipeline anywhere, the end-to-end iris tests are even marked `#[ignore]` as too slow to run in
CI. The single quantitative claim in the codebase is a **memory ceiling**: the sequential ten-proof
World prover is asserted to run "under 300 MB" (Makefile `MEM_LIM=300`, enforced via
`docker run --memory=300m`). That is a *target the build checks*, not a measurement of typical cost,
and it is not comparable to any proving-time row in the [inference table](../../zk-inference/). Do not
launder it into one.
:::

Two more cautions:

- **"Community Edition" is a disclaimer, not a footnote.** The README states the code is **not
  deployed in production** and carries **no security guarantees**; a Least Authority 2025 audit is
  included in-repo. So the open cut is not necessarily bit-identical to what runs on the Orb, cite
  it as the CE, not as "the World ID prover".
- **It is not vanilla GKR.** Two claim-aggregation strategies (interpolative and Libra-style RLC),
  with matrix-multiply layers forced to the interpolative one, and a Fiat–Shamir hardening (a
  SHA-256 hash-chain over inputs, defending the eprint 2025/118 GKR-transcript attack) whose own
  comment says the iteration count must grow for deeper circuits. Attribute it as a *structured*
  GKR variant, and treat any soundness claim as pending the caveats in the source, not the abstract.
