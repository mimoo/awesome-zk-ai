---
title: ACORN
paper: acorn
status: reviewed
---

## What is new

ACORN is really **two papers stapled together**, and separating them is the single most useful thing
this note can do, because the headline number belongs to the half that has no zero-knowledge in it
at all.

**Half one: a faster secure aggregation protocol, with no proofs.** Bell et al.'s protocol masks
each client's input with a PRG-derived pad, which costs the client `O(ℓ log n)` work. ACORN swaps
the PRG encoding for a **lattice-based (RLWE) encoding**, which drops it to `O(ℓ + log n)`, and the
server's from `O(nℓ log n)` to `O(n(ℓ + log n))`. Asymptotically optimal, and concretely faster.
This is `RLWE-SecAgg`, and it involves no zero-knowledge whatsoever.

**Half two: zero-knowledge input validation, made cheap.** Secure aggregation hides each client's
update, which is exactly what stops the server checking the update is not poison. ACORN adds ZK
proofs that a client's input satisfies L0, L2 or L∞ bounds, in two flavours, `ACORN-detect` (catch
malformed inputs) and `ACORN-robust` (catch them *and* still finish the aggregation). The genuinely
new cryptography is a **logarithmic-proof-size argument for an L∞ bound on a vector held in a
constant-size commitment**.

The reason ACORN's validation is so much cheaper than [[rofl]]'s or [[eiffel]]'s is structural and
worth internalising: **the encoding was chosen to make the proof cheap.** Everyone else bolts a ZK
proof onto a secure-aggregation protocol they inherited. ACORN co-designed the two, so the
commitment the proof needs is the commitment the aggregation was already producing. That is why its
validation overhead is a small fraction of the base protocol's communication where prior work pays
double-digit multiples.

## What it actually proves

Per client, per round: **that a client's submitted update satisfies a public norm bound** (L0, L2 or
L∞), without revealing the update. Nothing about the *training*, nothing about the *model*, and
nothing about whether the update is honest in any semantic sense, a norm bound stops a client
gaining disproportionate influence, and does not stop a subtle, in-budget poison.

The evaluation covers two settings: analytics (a histogram over ten thousand devices) and federated
learning (averaging model updates from five hundred devices), plus four real-world end-to-end tasks.

The client-side proving cost is reported as an **upper bound on a standard laptop**, the paper's
framing, and a good one, since it is the number a phone-scale participant actually cares about.

## What to distrust

**The headline speedup is not a speedup of the thing this SoK files ACORN under.** `papers.yml` had
the 2–8× recorded as if it were a cost or benefit of the ZK input validation. It is not.

:::audit The 2–8× belongs to the protocol with no proofs in it
From the abstract, verbatim:

> **Our new secure aggregation protocol** improves the computational efficiency of the state-of-the-art
> protocol of Bell et al. (CCS 2020) both asymptotically and concretely: we show via experimental
> evaluation that it results in **2-8X speedups in client computation** in practical scenarios.
> **Likewise, our extended protocol with input validation** improves on prior work by more than 30X in
> terms of client communication…

Two sentences, two different protocols, two different numbers. The 2–8× is `RLWE-SecAgg`, the base
protocol, **without input validation**, beating `PRG-SecAgg`. It comes entirely from swapping a
PRG-based input encoding for a lattice-based one, and it would be exactly the same number if the ZK
half of the paper did not exist.

§6 confirms the range is a span across settings rather than a spread within one: "roughly up to 5x
speedup in the FA setting for ℓ ≥ 2¹⁵, and up to more than 8x speedup in the FL setting."

The figures that actually describe ACORN's zero-knowledge contribution are different ones, the
communication overhead of validation over unvalidated aggregation, and the 30× improvement over
prior ZK-validated schemes. Both are now recorded separately in `papers.yml`.
:::

This matters beyond bookkeeping. If you were building the [federated](../../federated/) comparison
table and reached for ACORN's headline to represent "what ZK validation costs," you would be quoting
a number produced by a protocol that does no proving. The corrected entry keeps the two apart.

**A norm bound is a weak integrity predicate, and the paper is honest that this is the point.**
ACORN proves inputs are *in range*. It cannot prove they were computed by running SGD on real local
data. An adversary who stays inside the L2 ball can still poison, and the entire robustness
literature exists because that attack works. ACORN's value is that it removes the *cheap* attacks, 
the client submitting a vector of magnitude 10⁶, for close to nothing. It is a filter, not a proof
of training. Compare [[zkpot-garg]], which proves the training itself and costs orders of magnitude
more.

**The client-cost headline is an upper bound, and the input sizes are chosen generously.** "Under 80
seconds on a standard laptop" covers a binary vector of length 1M or a dense 16-bit vector of length
250K. Those are large, and the framing is deliberately conservative, this is the paper being
careful, not evasive. But it is a *ceiling*, and it is a ceiling on a laptop, not on the phone that a
real cross-device FL deployment recruits.

**Otherwise this is a clean paper.** The three protocols are stated separately, the security
properties are tabulated against prior work rather than asserted, and the comparison table
([[rofl]], [[eiffel]], [[prio]]) reports where ACORN is *worse* as well as better. The provenance
failure here was ours, not theirs, the paper draws the distinction between its two halves in the
first two sentences of its own abstract, and we collapsed it.
