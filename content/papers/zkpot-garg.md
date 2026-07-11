---
title: zkPoT (Garg et al.)
paper: zkpot-garg
status: reviewed
---

## What is new

Two things, and the definition is the more durable one.

**The definition.** This is the paper that says what a zero-knowledge proof of training *is*. The
statement being proven is: *"the prover possesses a model M consistent with a commitment c_M, a
dataset D consistent with a commitment c_D, and M is the result of running training algorithm L on
D."* Both the model and the data stay hidden; the verifier holds only commitments and the training
specification (architecture, step count, learning rate, batch size). Everything else in the
zk-training cell — [[kaizen]], [[zkdl]], [[optimum-vicinity]], [[zkboost]] — is proving some
version of this statement, and this is where the statement got written down.

**The construction.** A hybrid, and the motivation for it is the sharpest paragraph in the paper.
zkSNARKs give tiny proofs but need the entire training trace in RAM and impose a
several-orders-of-magnitude prover overhead. MPC-in-the-head gives a nearly free prover but a proof
as large as the circuit. So: use MPC-in-the-head for the bulk of the witness, and use a
**hash-based polynomial commitment (FRI, via Winterfell) to compress the expensive parts** — no
elliptic curves anywhere. The payoff that matters for ML is structural: **proof size is linear in
the number of records N and independent of the feature count D**, and the design is
*streaming-friendly*, so the prover never needs the whole trace resident.

That last property is the real contribution. It is the one thing in this cell that could plausibly
scale to a dataset that does not fit in memory.

## What it actually proves

**Correct mini-batch gradient descent training of a logistic regression model** on a committed
dataset, hiding both the data and the resulting model.

Not a DNN. Not a transformer. Logistic regression. The paper is entirely upfront about this — the
title is *"Experimenting with"* — and its defence is a good one: logistic regression is exactly the
shape of a classifier fine-tuned on top of a frozen foundation-model feature extractor, so a zkPoT
for it is already useful. Take that at face value, but do not let the definition's generality
launder the instantiation's scope.

Two more things the proof does not cover:

- **Security is 115 bits**, not 128 — FRI with 95 queries plus 20 bits of grinding. Stated plainly,
  which is more than most papers here manage.
- **The field is 128-bit, and the numerics chose it.** The paper is explicit that the large field
  "is required by the secure truncation protocol for fixed-point arithmetic," and that a 64-bit
  field "would further speed up the protocol and reduce proof size." That is the [[prob-truncation]]
  problem, arriving from the other direction: the truncation step does not merely cost gates, it
  sets the field size, which then taxes every other operation in the proof.

## What to distrust

**One of the three phases was never benchmarked, and the number people quote is the sum of the
other two.** The evaluation splits the protocol into an offline phase (data- and model-independent),
a data-checks phase, and an online phase.

:::audit The paper does not state a total prover time
From §1.1, reproduced exactly — note the two dashes:

| Phase | Prover (s) | Verifier (s) | Size (MB) |
|---|---|---|---|
| Online | 518 | 24 | 196 |
| Data Checks | 3690 | 2.5 | 5.3 |
| Offline | **–** | **–** | < 140 |
| **Total** | **–** | **–** | < 350 |

"The offline prover/verifier time have not been benchmarked, see Section 7 for details on how proof
size was estimated."

So the paper reports **no total prover time and no total verifier time at all** — both Total cells
are dashes. The 4208 s currently in `papers.yml` is `518 + 3690`: the sum of the two *measured*
phases, silently excluding an unmeasured third one that the paper itself calls "an expensive
pre-processing phase." The offline proof size is estimated, not measured, too.
:::

**The property that makes the paper interesting is not the property that was measured.** The
headline architectural claim is streaming-friendliness — "there is no fundamental memory limit to
how large a model and data set can be trained using our approach." The benchmark ran on a **512 GB
machine, single-threaded**. The paper is honest about the gap ("the high RAM requirement is an
artifact of our implementation and is not necessary... if our implementation is upgraded to a
streaming-friendly version, we expect that it can be run on consumer-grade laptops") — but *expect*
is the operative word. The streaming prover is a design argument, not an artifact. Nobody has run
it.

**Where this paper is a model for the rest of the repo.** It reports **two** baselines for its
cryptographic overhead — the time to train the model natively in `f64`, *and* the time to train it
over the 128-bit field the protocol requires — and explains why both are meaningful: one gives the
overhead over an optimized training algorithm, the other isolates the cost of the cryptography from
the cost of merely leaving the CPU's native datatypes.

That is precisely the disclosure [[safetynets]] does not make. SafetyNets reports its prover
overhead only against field-arithmetic execution, which flatters it enormously, and the README has
been reading that figure as a floor on the cost of verifiable inference. zkPoT prints both numbers
and lets you compute either ratio. Every paper in this repo that reports a "cryptographic overhead"
should be held to this standard.
