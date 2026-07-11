---
title: The systems, grouped by what they gave up
section: zk-training
order: 20
lede: >-
  Grouping these by proof system tells you nothing -- they are almost all sum-check or VOLE.
  Grouping them by which part of the training claim they refused to prove tells you
  everything, because that choice is what sets their scale, and it is the only axis on which
  they actually differ.
papers: [kaizen, zkdl, zkboost, zkpot-garg, summer, optimum-vicinity, verilora, veriml, zkmlaas, zkprov, zkaudit, private-lora-he]
status: draft
---

Every system below would, in a world with an infinitely fast prover, prove the same sentence:
*these weights are the honest output of this procedure on this committed data*. None of them do.
The taxonomy that matters is which clause each one dropped.

{{ papers:training }}

## Group 1 — Prove every step (and pay for it)

These accept the full claim and attack the cost of composing a proof across a long, sequential
computation. They are the reference points, and they are all demonstrated on small models.

**[[kaizen]]** is the canonical DNN zkPoT. The prover runs mini-batch gradient descent and emits
a commitment plus a succinct proof at each iteration, recursively composing GKR-style proofs with
aggregatable polynomial commitments. Two properties are the actual contribution: the iteration
count does not have to be fixed in advance, and proof size and verifier time are independent of
both the iteration count and the dataset size. That is exactly the shape you want — the verifier
should not pay for the length of a run it did not watch. The prover, of course, still does.

**[[zkdl]]** goes the other way: instead of recursion, it makes the circuit itself
training-shaped. `FAC4DNN` aggregates proofs across layers *and across training steps* without
being constrained by their sequential order, and `zkReLU` gives ReLU and its backward pass a
bespoke argument rather than a generic one. It runs on GPU and is open source. It is also the one
entry in the table whose reported proof size is implausible on its face — see the note in
`papers.yml` and the conflicts page; do not cite that figure without checking the paper.

**[[zkboost]]** is the useful corrective to a deep-learning-shaped field: it is the first zkPoT
for XGBoost, built from a generic zkPoT template with a VOLE-based instantiation. Gradient-boosted
trees are what most tabular and financial production models actually are, so this is arguably the
first zkPoT aimed at a model class someone is currently deploying. It also claims to fix a
security gap in prior zero-knowledge training proofs — a claim we have not been able to attribute
to a specific prior protocol, and which is tracked as an open item on the soundness page.

**[[zkpot-garg]]** is the definitional paper (MPC-in-the-head composed with zkSNARKs, streaming-
friendly), instantiated only for logistic regression. **[[summer]]** targets recursive proofs for
RNN training and we have not read it.

:::gap  We are reading this group from the outside
There is no PDF in `references/` for any paper in this section. Every characterisation above
comes from abstracts, author summaries and the survey's tables. Treat the *mechanisms* as
reported and the *numbers* as secondhand.
:::

## Group 2 — Prove the result instead of the process

**[[optimum-vicinity]]** is the most interesting conceptual departure in the cell, and it is the
only one that changes the logical form of the statement rather than its size. Instead of proving
that every step of the optimizer executed correctly, it proves that the *result* lies within a
bounded distance of the mathematical optimum of the committed objective. A statement about a very
long computation becomes a statement about a very short one, and the circuits shrink accordingly.

The price is the model class: this only makes sense where training *has* an optimum to be near —
convex problems. Deep networks do not qualify, and the paper does not claim they do. Note also
what the verifier learns: that the model is close to the optimum of some objective on some
committed data. It learns nothing about how it got there, which is fine, and nothing about
whether the data was any good, which is the subject of the next page.

## Group 3 — Prove a smaller computation

**[[verilora]]** is the only system here that touches a model of the scale people actually use,
and it does so by proving a *fine-tune*, not a training run: forward propagation, backward
gradients and LoRA weight updates over a frozen base model. This is a much cheaper claim, and it
is a much weaker one — the base model, which is where all the capability and all the plausible
backdoors live, is outside the proof. It is also the natural contrast pair with
[[private-lora-he]] on the privacy side: the same workload, the opposite guarantee.

We flag one thing about this entry loudly: its numbers in `papers.yml` come from the survey's
table, not from the paper, and it is exactly the entry where we would most like a primary read.

## Group 4 — Prove a random sample of the steps

**[[veriml]]** and **[[zkmlaas]]** are the ancestors, and they made the trade everyone else
refused. Neither proves every iteration. They commit to iteration inputs and outputs, and let the
verifier challenge a randomly chosen subset. The proving cost collapses, and so does the
guarantee: soundness becomes statistical, and it holds only if the commitments really precede the
challenge and the challenge is genuinely unpredictable. This is the same bargain that the
sampling-based inference line makes, and it should be compared on the same axis — cost against
detection probability — not against cryptographic soundness.

## Group 5 — Prove where the data came from, not what you did with it

**[[zkprov]]** proves *which dataset* a model was trained on without proving the training
computation at all. This is a much cheaper claim, and for the compliance use case (licensing,
data provenance) it may be the claim that matters. It is also, on its own, nearly vacuous as an
integrity statement: a proof that a dataset was used is not a proof that anything correct was
done with it, or that nothing else was used afterwards.

**[[zkaudit]]** sits across the boundary and is worth pulling in here even though it is filed
under properties: its first phase, `ZKAudit-T`, *is* a zkPoT — it proves the model was trained by
SGD on a committed dataset — and its second phase audits arbitrary properties of the hidden data
and hidden weights. Notably, it keeps the weights secret but makes the **architecture public**,
which is precisely the mitigation the Fiat–Shamir question on the soundness page turns on.

:::debate  Is Group 5 in this cell at all?
`papers.yml` files [[zkprov]] under `training:`, so it appears in the table above with no
benchmark row. We think that is the right call — it competes for the same budget and the same
buyer as a zkPoT, and pretending it is a different subject is how a survey lets a weak claim
stand in for a strong one. But it proves nothing about the optimizer, and a reader who skims the
table could easily miss that.
:::

## What the grouping shows

Cost and scale track the relaxation, not the proof system. The step-by-step group (1) tops out at
small models. The result-only group (2) buys enormous circuit savings and pays for them in model
class. The shrunken-computation group (3) reaches a large model by leaving most of it outside the
statement. The sampling group (4) buys speed with probability. The provenance group (5) is cheap
because it barely proves anything about the computation.

There is no system in this cell that proves a full training run of a large model, and there is no
plausible path to one from any of these designs. What there is, is a menu of things you can give
up. The next page is that menu, read from the adversary's side.
