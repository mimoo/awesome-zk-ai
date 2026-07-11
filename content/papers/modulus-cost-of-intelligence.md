---
title: The Cost of Intelligence
paper: modulus-cost-of-intelligence
status: reviewed
---

## What is new

This is the field's first honest cross-backend benchmark, and it is asking a question nobody else in
this repo asks. Every other paper here picks one proof system and optimizes within it. Modulus picks
one *workload* — MLPs, scaled two ways, by parameter count up to tens of millions and by depth up to
hundreds of layers — and runs it through **six different proof systems**: Groth16, Gemini, Winterfell
(via Cairo), Halo2, Plonky2, and [[zkcnn]]. Same models, same encoding discipline, same machine.

The findings are the useful part, and they have held up:

- **Plonky2 is the fastest prover** on the largest architectures, by a wide margin over Halo2 —
  FRI-based commitments over the Goldilocks field beat pairing-based commitments over a 254-bit
  curve. It pays for that in **peak memory**, at times doubling Halo2's.
- **[[zkcnn]]'s GKR-based prover scales best on both axes simultaneously** — and, per the paper, it
  does so *unoptimized* for this workload. This is the empirical result that arguably launched the
  entire sum-check-for-ML line that dominates this repo: [[zkllm]], [[zkgpt]], [[zkpytorch]],
  [[deepprove]] are all downstream of "GKR wins."

The authors also worked with the original systems' authors to tune the benchmarks, which is more
than most comparative papers do, and they say so.

## What it actually proves

**Prover time and prover peak memory, for MLPs, on one machine.** That is the entire measured
surface, and the paper is explicit about the boundaries:

:::quote{src="The Cost of Intelligence" sec="§3, Benchmarking Methodology"}
Note that we omitt comparing the verifier runtime and generated proof size, as the question of
feasibility lies heavily on the prover side – indeed, this is an excellent starting point for future
work – and is thus beyond the scope of this whitepaper.
:::

It is **not** an LLM benchmark. No transformers, no attention, no tokens, no softmax, no
autoregression. It should not appear on any throughput-vs-parameters chart in this repo, and
`papers.yml` correctly excludes it.

It is also a **whitepaper from a company building a prover**, written to motivate that prover
(Remainder, a GKR system — which is exactly what the benchmark concludes is best). That is not an
accusation of dishonesty; the incentive is disclosed and the code is public. But the conclusion and
the product point the same direction, and a reader should know that.

## What to distrust

**Preprocessing and witness generation are excluded — from everyone.** "all measurements are
performed with respect to proof generation time, and do not take into account pre-processing or
witness generation steps." This systematically flatters the systems whose costs live there. Groth16's
trusted setup and Halo2's key generation are not small; [[jolt-atlas]] makes precisely the opposite
methodological choice, treating ezkl's key generation as a headline cost that dwarfs its proving
time — because for a real deployment it *is* a cost. Modulus's ranking is a ranking of one phase.

**The R1CS systems are handicapped by their encoding, not by R1CS.** ReLU is implemented in Circom
via bit decomposition against `p/2`; fixed-point division is implemented by bit-decomposing and
truncating. That was a reasonable choice in January 2023 — but lookup arguments were already the
known answer to exactly this problem, and the entire subsequent literature ([[zkllm]]'s `tlookup`,
[[zkgpt]]'s Lasso range relations, [[jolt-atlas]]'s prefix-suffix tables) is about not doing that.
The Groth16 and Gemini numbers are a floor on how badly R1CS can do non-linearities, not a measure of
how well it can.

**The generalization from MLPs to real architectures is asserted, and the field has since falsified
it.** The paper argues its MLPs are "roughly representative of prover scaling for such models"
because they match VGG-16 and ResNet-50 on FLOPs and layer count. But FLOP count is not what
determines proving cost — *operator structure* is. [[deepprove]]'s own prover breakdown puts more
than half its cost in activations, Softmax and requantization, with requantization alone the single
largest line item. An MLP-plus-ReLU benchmark contains **none of those operators**. The whole reason
[[zkcnn]] needed a bespoke FFT sum-check, [[zkllm]] needed `zkAttn`, and [[zkgpt]] needed constraint
fusion is that the operators the modern workloads are made of do not look like a stack of dense
layers. A benchmark that matches the FLOPs and misses the operators is measuring the easy part.

**It is a 2023 paper wearing a 2026 eprint number.** The disclaimer is explicit — "no new material
has been added since January 30, 2023" — but the eprint identifier makes it look contemporary in a
citation list, and it predates [[zkllm]], [[zkgpt]], [[zkpytorch]], [[deepprove]] and the entire
lookup-argument generation. Its zkCNN row is the ancestor of half this repo; its Groth16 and Halo2
rows describe a world that no longer exists.

**Read it for the shape, not the numbers.** The result that matters is *GKR/sum-check scales best on
time and memory together*, and that result has been vindicated by everything built since. The
concrete timings are a snapshot of a field that turned over completely in the following two years.
