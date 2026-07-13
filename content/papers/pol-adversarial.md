---
title: "\"Adversarial Examples\" for Proof-of-Learning"
paper: pol-adversarial
status: reviewed
---

The first break of [[pol]], and the idea is lovely.

## The attack

To fake a training step you need a data batch whose gradient carries you from one logged checkpoint
to the next. So **optimize the data.**

Exactly as you would craft an adversarial example — gradient descent on the *input* rather than on the
weights — the attacker synthesizes a batch that makes an update land on the stolen final model. The
attack is explicit that it exploits an assumption the original paper granted it: that the adversary
"has full access to the training dataset and can modify it."

:::quote{src="Zhang et al." sec="Abstract"}
in a similar way as optimizing an adversarial example, we could make an arbitrarily-chosen data point
"generate" a given model, hence efficiently generating intermediate models with correct data points.
:::

## The cost

Honest training of their ResNet-20/CIFAR-10 target is **78,000 gradient computations**. The attack
needs 31 gradient computations per faked step, so it wins whenever the faked run is shorter than about
**2,516 steps**. The stronger variant amortizes over the checkpoint interval and wins below ~251,600.

And empirically the spoof is *better than the real thing*: it passes verification, it reproduces with
**lower** error than the genuine proof, it is **smaller** than the genuine proof, and it works from a
**non-overlapping dataset** on strictly **weaker hardware** than the victim's.

## What it kills

[[pol]]'s Property 2 — the claim that spoofing costs at least as much as training. The paper is blunt
about the status of that claim: Jia et al. "did not provide a proof to back their claim."

## Why it matters here

Because its proposed fix is this entire SoK. §V lists verifiable computation — citing SNARKs and
STARKs by name — as the sound alternative, and then prices it in a single sentence:

> *"This mechanism is valid, but it will introduce an overwhelming overhead."*

That is the [zkPoT cell](/zk-training/), named and costed by an attack paper in 2022. Everything in it
is an attempt to make that sentence false.

## What to distrust

The follow-up, [[pol-broken]], substantially corrects this paper — and it is worth reading the
correction before citing the attack. Attack 1 here is **not reproducible**: neither the original team
nor the [[pol-broken]] authors could make it work. And Attack 2 assumes the adversary controls the
checkpoint interval $k$ and the threshold $\delta$, which "should be set by the verifier and is thus
out of the attacker's control" — reduce them by an order of magnitude and the attack does not
converge.

So the break is real, but it is weaker than it reads, and it targets a weakened instantiation of the
scheme. The *durable* break is the next paper.
