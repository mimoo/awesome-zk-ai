---
title: Proof-of-Learning
paper: pol
status: reviewed
---

This is the paper the entire [zkPoT cell](/zk-training/) is arguing with, and until July 2026 this
SoK did not contain it.

## What it is

A **non-cryptographic** proof of training. The prover logs a tuple: model weights every $k$-th step,
the indices of the batch used at each step, signatures of those data points, and the hyperparameters.
The verifier checks the initialization was drawn from the claimed distribution (a Kolmogorov–Smirnov
test), then **re-executes the $Q$ largest weight updates per epoch** and fails if the replayed
weights diverge from the logged ones by more than a slack parameter $\delta$.

Why the largest updates? Because valid gradient-descent steps are small, you do not want to overshoot
so an adversary faking a cheaper run has to introduce estimation error, and error is most visible in
the big steps. It is a genuinely elegant heuristic, and it is doing all the work.

## What it actually proves

Less than it looks like, and the paper is honest about this in a way its citers are not.

The security property everyone wants, *no adversary can produce a valid proof more cheaply than
honestly training*, is **Property 2**, and it is **never proved.** What is offered instead is:

:::quote{src="Proof-of-Learning" sec="§VII-B3, Conjecture 1"}
Inverting a training sequence using numerical root finding methods will always be at least as
computationally expensive as training, given the same model.
:::

A conjecture. The authors say plainly they are "not aware of a mechanism to prove those formally."

**Two papers then went and broke it.** See [[pol-adversarial]] and [[pol-broken]].

## Why it belongs in this SoK

Because the failure of this scheme is the *reason* for everything in the [training
cell](/zk-training/). Both breaks reach the same conclusion by different routes, and one of them names
the answer explicitly:

[[pol-adversarial]] lists verifiable computation, citing SNARKs and STARKs by name, as the sound
alternative, and prices it in one sentence: *"This mechanism is valid, but it will introduce an
overwhelming overhead."*

[[pol-broken]] concludes: *"One possible solution to circumvent these fundamental limits in ML theory
and our understanding of optimization, is to rely more on cryptography."*

Kaizen, zkDL, VeriML, zkPoT, every system in this category is an attempt to pay that overwhelming
overhead. The cell exists because this paper was spoofed.

## What to distrust

Beyond the unproven Property 2, the paper is candid about three things worth carrying:

**Verification requires handing the training data to the verifier.** For a scheme whose motivating
application is proving ownership of a proprietary model trained on proprietary data, that is a
substantial hole, and the paper says so.

**The storage cost is the entire checkpoint history.** They downcast fp32 to fp16 to halve it. Merkle
hashing does not work, "due to the error accumulated when the verifier reconstructs the weights."

**The guarantee degrades with reuse:** "our probability of success for our verification scheme
degrades multiplicatively with each usage," which bounds how long a chain of proofs can get, relevant
to any provenance story that wants to chain fine-tunes.
