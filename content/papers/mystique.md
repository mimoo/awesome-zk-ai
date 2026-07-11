---
title: Mystique
paper: mystique
status: reviewed
---

## What is new

Mystique is not a proof system. It is a set of **conversions**, plus one matrix-multiplication
protocol, bolted onto an existing sVOLE-based interactive ZK backend. The thesis is that no single
representation is right for a whole neural network, so the thing worth optimising is the cost of
*changing representation*:

- **Arithmetic ↔ Boolean** (`zk-edaBits`), so linear layers can live in 𝔽ₚ and non-linear layers in
  a Boolean circuit.
- **Publicly committed ↔ privately authenticated** (`C2A`), which is the conversion that makes
  "prove against a model the world has already seen a commitment to" possible at all. It is
  instantiated with a PRF (LowMC) evaluated inside a Boolean circuit.
- **Fixed-point ↔ IEEE-754 floating point**, so the non-linear layers can be evaluated in *real
  single-precision floats*.

That third conversion is the one that separates Mystique from everything else in this collection.
[[zkllm]], [[deepprove]] and [[jolt-atlas]] all quantize the entire network and then spend their
prover budget fighting the consequences — requantization, clamping, lookup-table domains, outlier
smoothing. Mystique refuses. Non-linearities are computed on honest IEEE-754 floats, which is why
its accuracy holds up across a hundred layers and why it needs no calibration story at all. The
`Requant` operator that costs [[deepprove]] the largest single slice of its prover *does not exist
here*.

The matmul protocol is a generalised Freivalds check. To prove `A · B = C` on authenticated
matrices, the verifier samples random vectors `u`, `v` and the parties reduce to proving the single
inner product `uᵀ·A·B·v = uᵀ·C·v`. The circuit shrinks from `O(n³)` private multiplications to one
dot product, with communication independent of the inner dimension.

## What it actually proves

**That a committed CNN was correctly evaluated on a private image — interactively, to exactly one
verifier, who had to be online for the whole thing.**

This is a genuinely different object from the proofs elsewhere in this section, and the differences
are not cosmetic.

**There is no proof.** Mystique is a *designated-verifier interactive* protocol. What it produces is
a conversation, not an artifact. The prover and verifier co-generate the transcript, and the
transcript convinces nobody who did not participate in it — the verifier's authentication key is
what makes it sound, so anyone holding that key could have forged it. You cannot post it on a chain,
cache it in a CDN, hand it to a regulator, or let a second customer check the same proof. The paper
is admirably direct about this in its conclusion:

:::quote{src="Mystique" sec="§8, Conclusion"}
In particular, our ZK protocol can only prove to one verifier at a time, and the communication cost
is fairly high compared to succinct ZK proofs like zk-SNARKs.
:::

**What `papers.yml` calls `proof_size_mb` is not a proof size.** It is total interactive
communication. A succinct proof's size is what the verifier *stores*; this number is what the two
parties *exchange*. The two are not comparable quantities and should never be plotted on the same
axis.

**The memory/communication trade runs the opposite way from a SNARK.** Mystique's own motivation for
sVOLE is that a zk-SNARK prover's memory scales with the statement, which it argues would put a
billion-constraint statement out of reach on commodity hardware. The sVOLE prover streams, so
ResNet-101 fits in a fraction of the machine's RAM. That is the actual bargain: **small prover
memory, enormous transcript.** [[deepprove]] takes the opposite side of exactly the same trade,
scaling *out* to a cluster and shipping a proof measured in megabytes. Neither is free; they are
different bets about which resource is scarce.

**Three settings, three prices.** Model and image can each be private or public, and Table 3 prices
all three combinations separately. The cheapest is the one where the model is public — which is to
say, the one where nothing about the model is hidden and the motivating threat (a service provider
lying about which model it ran) is the only thing being addressed. See the audit note below; this
distinction has already gone missing once.

**It is a CNN paper.** LeNet-5, ResNet-50, ResNet-101, CIFAR-10. No attention, no softmax over a
sequence, no autoregression. Reading it as an LLM result is a category error — but reading its
*mechanism* as inapplicable to LLMs would also be a mistake, which is why it now carries scheme
entries on the operator atlas.

## What to distrust

:::audit `papers.yml` records the setting where the model is *not* private
The ResNet-101 row in `papers.yml` (262 s, 990 MB, `numbers_source: survey`) is exactly Table 3's
**public-model, private-image** column at 200 Mbps — the cheapest of the three settings, and the one
in which the model parameters are revealed to the verifier.

The setting Mystique actually sells — a *private, publicly committed* model, i.e. the "ZK proofs of
correct inference" application from its own introduction — is roughly twice that on both axes
(535 s, 1.98 GB). And the end-to-end application including the commitment pull is the abstract's
headline: an inference "using a committed (private) ResNet-101 model in 28 minutes", against "the
same task when the model is public in 5 minutes".

So the repo currently credits Mystique with the cost of the configuration that answers the *weaker*
threat model. Both numbers are real and both are in the paper; the row should say which one it is.
:::

**Batch Normalization eats the paper.** The float-circuit trick buys accuracy, and the bill arrives
at the conversion boundary:

:::quote{src="Mystique" sec="§7.2, Microbenchmark"}
Note that the Batch Normalization takes around 70% of time in both cases because it involves
complicated arithmetic operations and conversions between floating-point and fixed-point numbers,
which are costly to maintain accuracy.
:::

This is the honest reading of Mystique: it does not escape the non-linearity tax that dominates
[[deepprove]] and [[zkllm]]. It *relocates* it — out of lookup tables and into arithmetic–Boolean
conversion — and then pays it in the same proportion. A normalization layer costing the majority of
the prover is the single most reproducible finding in this whole literature. [[hao-et-al]] exists
precisely to attack this bill, and is the paper to read next.

**The matmul speedup is a circuit-size result, not a prover-time result.** The Freivalds trick
removes private multiplications from the *circuit*; it does not remove the multiplication from the
*prover*, who still has to compute `A · B` locally to know `C`. The paper says so:

:::quote{src="Mystique" sec="§7.1, Benchmarking Our Building Blocks"}
The main efficiency bottleneck is the local computation of matrix multiplication by the prover.
:::

Read the headline improvement as a statement about communication and circuit size. The prover's
asymptotic work is unchanged.

**The amortization argument quietly assumes the property the protocol does not have.** On the cost
of converting a public model commitment into authenticated values, the paper says:

:::quote{src="Mystique" sec="§7.3, End-to-End Applications"}
The cost to “pull” a publicly committed model to be used in ZK proofs is high, but it could always
be amortized over multiple private inferences.
:::

Amortized over multiple inferences *for the same verifier*. Authenticated values are bound to the
verifier's MAC key, so a second verifier means redoing the pull, and the whole interaction, from
scratch. In the MLaaS setting the paper motivates — one model owner, many clients — the pull is
therefore **per-client**, not one-off, and does not amortize in the direction the sentence implies.
This is the designated-verifier limitation resurfacing as an economic one, and it is the strongest
argument for why the succinct lineage won despite being slower per proof.

**Credit where due.** The accuracy evaluation is the best in this cluster: the full CIFAR-10 test
set, a reported accuracy delta against the plaintext model, and — unusually — the ℓ₂ distance
between the plaintext and ZK probability vectors, not just top-1 agreement. Nobody in the sum-check
lineage reports the distribution of the error. They should.
