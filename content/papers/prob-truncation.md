---
title: Probabilistic truncation in PPML
paper: prob-truncation
status: reviewed
---

## What is new

This is an **audit paper**, and the repo has been mis-filing it as a protocol paper. Its protocol
contributions are real but secondary. Its finding is that **the deployed PPML platforms are getting
away with an unsound truncation only because their code does not implement the protocol they
published.**

The setting: every fixed-point system must *truncate* after a multiply, to rescale the product back
down. The cheap, non-interactive truncation protocols the whole stack relies on, SecureML, ABY3,
EdaBits, Bicoptor, CrypTen, Piranha, are **probabilistic**. They mask the value with a random `r`,
and they fail with probability `2^-(ℓ - ℓx - 1)`, where `ℓ` is the ring size and `ℓx` the value's bit
length. A failure is not a rounding error. It is a **large, wrong value, produced silently**, and
the computation carries on.

The authors read the open-source code. And what they found is the paper:

- Piranha's implementations (P-SecureML, P-Falcon, P-Fantastic) **hardcode the mask `r` to a fixed
  constant** instead of sampling it, "to simplify their implementation."
- With `r` fixed, the failure probability is **exactly zero**. The bug cannot manifest. The published
  accuracy numbers look fine.
- But a uniformly random mask is, in the paper's words, "a necessary condition for security."
  Sampling `r` properly, as the protocol specifies, and as security demands, is what the authors
  then did.

The protocol contributions that follow are the fixes: a non-interactive **deterministic** cut protocol
that removes the probabilistic error entirely (which then lets the ring shrink, since the ring was
only that large to push the failure probability down), and a "truncate-then-multiply" reordering that
stops `ℓx` from doubling into `ℓ` after each product.

## What it actually proves

Nothing, it is MPC, not ZK, and it produces no proof. What it *demonstrates* is a bug, and the
demonstration is the strongest empirical result of the five numerics papers.

:::audit Fix the security hole and the models stop working
The recommended parameters in Piranha are `ℓ_frac = 26` on a 64-bit ring, which does satisfy
`ℓx ≪ ℓ`, until you multiply. After a single multiplication `ℓx` roughly **doubles**, landing at 62
against a ring of 64, which drives the failure probability up enormously.

That never showed up in Piranha's own experiments, because Piranha fixes `r = 2^26` rather than
sampling it, which forces the failure probability to zero. The authors replaced the fixed mask with a
correctly sampled random one and re-ran the inference. Table 2, CIFAR-10:

| Mask | 2-party (P-SecureML) | 3-party (P-Falcon) | 4-party (P-Fantastic) |
|---|---|---|---|
| **fixed** `r` (as shipped) | 54.89% | 54.89% | 54.89% |
| **random** `r` (as specified) | **0.43%** | **0.41%** | **0.50%** |

Random guessing on CIFAR-10 is 10%. The correctly-implemented protocol scores **below random**. The
model is producing garbage, and the only thing standing between the shipped platforms and that
outcome is a constant where a random number should be.
:::

This is the thing this repo has been looking for. Our
[quantization page](../../zk-inference/quantization/) has carried "quantization as an audit surface"
as an **open question, our own observation, no paper, no known bug.** That is no longer true. There
*is* a bug, it is in the re-quantization step, it is in shipped code, and it is a security/correctness
trade in which the security hole is what makes the accuracy look good. It is in the neighbouring
column, on the same operator that [[deepprove]]'s own prover breakdown identifies as its single
largest cost.

The failure modes differ, and the difference is the one genuinely reassuring thing here:

- **In MPC**, a truncation failure yields a silently wrong value; the computation continues and
  nobody is told.
- **In ZK**, the analogous event is an out-of-range value that **cannot be looked up at all**, the
  honest prover fails to produce a proof, rather than the verifier accepting a bad one. That is a
  *liveness* failure, not a *soundness* failure, and it is strictly the better place to be.

The zkML column got the better failure mode largely by accident: a lookup table simply has no entry
for a value outside its range. What this paper supplies is the number nobody in zkML has computed, 
how often you would be *hitting* that condition.

## What to distrust

**The headline is narrower than "probabilistic truncation is broken."** By the paper's own analysis,
the protocol is sound whenever `ℓx ≪ ℓ` is genuinely maintained. What fails is the *recommended
parameterisation*, because it is stated for the pre-multiplication bit length and nobody tracked what
happens after. So the finding is: **the parameters in the literature are wrong, and the code hides
that they are wrong.** That is bad enough, and precise, and it is not the same as a break of the
primitive.

**The load-bearing evidence is not in the PDF we hold.** The AAAI camera-ready is eight pages, and
the accuracy sweeps that justify the central claim are repeatedly deferred, "Fig. 4 (see our full
version)", "Fig. 5 (see our full version)", "Tab. 6 (see our full version)". Table 2 is in the
version we have and is damning on its own. But a reader who wants to check the parameter analysis
across models and ring sizes cannot, from this document. `papers.yml` also records that the paper
carries **no DOI, arXiv id or eprint number**, only a proceedings header. For a paper making an
accusation of an implementation bug in named open-source projects, that is a thin paper trail.

**The transfer to ZK is our inference, not the authors'.** The paper never mentions zero-knowledge
proofs; the word does not appear in it. The connection drawn above is ours, and should be read as a
research pointer, *go and compute the failure rate of your own re-quantization*, rather than as a
result the authors claim.

**It is MPC, and none of its costs belong on a chart here.** Communication and rounds are not proving
times. Same caveat as [[secfloat]] and [[archer-ieee]].
