---
title: Every relaxation, and what an adversary can still do
section: zk-training
order: 30
lede: >-
  Nobody proves a pretraining run. Everyone relaxes something. A relaxation is not a
  weakness -- it is a design choice, and it is the only reason any of these systems exist.
  But each one leaves a specific adversary standing, and the papers name their relaxation
  far more often than they name the adversary it lets through.
papers: [verilora, veriml, zkmlaas, optimum-vicinity, kaizen, zkdl, zkboost, zkpot-garg, zkprov, zkaudit, rofl, acorn, eiffel, opml, proof-of-sampling, optimistic-tee-rollups, lightweight-sampling-inference, fairzk]
status: reviewed
---

This page has one job: for each way of making proof-of-training tractable, state precisely what a
malicious trainer can *still* do while producing a proof that verifies. None of this is an attack
on a paper. All of it is what an auditor should write in the "residual risk" column.

A note on how to read the residuals. The proof is always sound, that is the one thing you get
for free. The question is never "can the prover forge the proof", it is **"what is the set of
models for which an honest proof exists?"** A relaxation is a decision to make that set larger.

## R1: Prove a fine-tune, not a training run

*Taken by:* [[verilora]]. *Cost saved:* everything. It is the only reason a model at that scale
appears in the table at all.

The statement becomes: *starting from base weights $W_0$, these LoRA adapters are the honest
output of fine-tuning on this committed data.*

**What the adversary can still do.** Ship a backdoored $W_0$. The entire base model, where the
capability lives, and where a data-poisoning or weight-editing backdoor would live, is a free
parameter of the statement. The proof binds the delta and says nothing about what it is a delta
*from*. A trainer who wants a model that behaves badly on one trigger phrase does not need to
cheat during fine-tuning; they need to have cheated before it. Worse, the adapters are the part
being *proven*, and they are the part a customer might reasonably assume is the risky part,
because they are the part that changed.

The mitigation is not cryptographic and is easy to state: the statement is only worth something
if $W_0$ is a *published, independently attested* checkpoint, so that "trust the base model"
reduces to a claim someone else already made publicly. Whether [[verilora]] frames it that way,
we cannot tell without the PDF.

## R2: Prove a random sample of the steps

*Taken by:* [[veriml]], [[zkmlaas]]. *Cost saved:* proportional to the sampling rate.

The statement becomes: *of the iterations you challenged, all were computed correctly.*

**What the adversary can still do.** Cheat in the iterations you did not challenge. That is not a
pedantic restatement, it is a real threat model, because **gradient descent does not require many
corrupt steps to land somewhere chosen.** A single adversarially crafted weight update at the end
of a run is enough to install a backdoor while every sampled step verifies. A cheat that is
diffuse over many steps is easy to catch by sampling; a cheat concentrated in one step is exactly
the one sampling is worst at, and it is also the easiest one to mount.

Two preconditions carry the entire guarantee, and both are implementation properties rather than
theorems: the commitment to iteration inputs and outputs must genuinely precede the challenge, and
the challenge must be unpredictable to the prover. A Fiat–Shamir-derived challenge over
prover-chosen commitments is the obvious place this goes wrong.

The honest comparison axis here is the one the sampling-based inference work forces on us: cost
against *detection probability times penalty*, not cost against cost. Compared against
[[proof-of-sampling]] and [[lightweight-sampling-inference]], these systems are early members of
the same family, and they should be evaluated by that family's standard rather than by
cryptographic soundness they never claimed.

## R3: Prove the result, not the process

*Taken by:* [[optimum-vicinity]]. *Cost saved:* the entire length of the computation.

The statement becomes: *the model is within a bounded distance of the optimum of this objective on
this committed data.*

**What the adversary can still do.** Choose any model in the ball. The vicinity bound is a
parameter of the statement, and every model inside it admits an honest proof, including models
the honest optimizer would never have produced. How much freedom that buys depends entirely on how
tight the bound is, and "how much can a model's behaviour differ across the certified vicinity" is
not a question the cryptography answers.

The deeper limitation is the one the paper states itself: this needs training to *be* a convex
optimization problem with an optimum to be near. There is no analogue of the statement for a deep
network, because there is no optimum to bound the distance to. That is not an engineering gap that
better circuits will close.

## R4: Prove the computation, trust the data

*Taken by:* **all** of [[kaizen]], [[zkdl]], [[zkboost]], [[zkpot-garg]], [[verilora]]. This is the
relaxation nobody calls a relaxation, because it is baked into the definition.

The statement is: *I ran the optimizer correctly on the dataset I committed to.* The dataset is a
commitment. A commitment is a hash. **A hash of poison is still a valid commitment.**

**What the adversary can still do.** Everything that data poisoning, backdoor injection, licence
violation, PII inclusion and benchmark contamination let you do. Every one of those attacks is
executed *before* the training run and is fully compatible with a perfect zkPoT. The proof
attests that garbage went in and was faithfully processed into garbage.

This is the single most important sentence on this page, so we will say it without hedging: **a
proof of training is not a proof of a good model, and no amount of prover engineering will make it
one.** What closes the gap is a *second* claim about the committed data or the resulting model, 
which is precisely what [[zkaudit]] (arbitrary audits over the hidden data and weights) and
[[fairzk]] (fairness derived from parameters and aggregate statistics) are for. The properties
cell is not a nice-to-have next to the training cell; it is the half that makes the training cell
mean anything.

## R5: Prove the data, trust the computation

*Taken by:* [[zkprov]]. The mirror image of R4, and the cheap one.

The statement becomes: *this model was trained on that dataset.*

**What the adversary can still do.** Anything at all with the optimizer. Train on the declared
dataset *and also* on an undeclared one. Train correctly and then edit the weights afterwards.
Run a procedure that is nominally SGD on the licensed corpus but is engineered to memorize it.
Nothing in a provenance proof rules any of these out, because the computation is not in the
statement.

Provenance proofs are worth having, for licensing and regulatory questions they may be exactly the
claim a regulator wants, but they must not be read as a discount zkPoT.

## R6: Prove properties of updates, not the training that produced them

*Taken by:* the federated cell, [[rofl]], [[acorn]], [[eiffel]] and the rest.

The statement becomes: *this update satisfies a public predicate the server chose*, in practice a
norm bound ([[rofl]], [[acorn]]), though [[eiffel]] admits any per-client robustness test as the
predicate, including a cosine-similarity check.

**What the adversary can still do.** Submit a poisoned update that satisfies whatever predicate was
chosen. Where the predicate is a norm bound it constrains magnitude and says nothing about
direction; where it is a stronger ML defence, the residual is that defence's own false-negative
rate, which the cryptography does not improve. There is a whole page on this in the federated
section, it is the defining gap of that cell, not a footnote to this one.

## R7: Prove nothing; make cheating expensive instead

*Taken by:* [[opml]], [[optimistic-tee-rollups]], [[proof-of-sampling]]. Not a zkPoT relaxation so
much as an exit from the cell, and often the right one.

**What the adversary can still do.** Whatever the economic or hardware assumption permits: cheat
when no honest challenger is watching (optimistic), cheat if you can break or side-channel the
enclave (TEE), cheat when the expected penalty is below the expected gain (rational sampling). The
guarantees are crisply stateable and much cheaper. They are also not the same guarantee, and
plotting them against proving times would be a category error.

## R8: Prove a quantized run of a quantized model

*Taken by:* every system that has to commit a real number to a field element. It is not always
taken silently, [[zkpot-garg]] names it as a limitation of its own techniques (piecewise-linear
activations, fixed-point instead of floating-point arithmetic), and [[zkboost]] reports a
fixed-point variant of XGBoost, but no entry in the training table records a bit width, which is a
finding in its own right.

**What the adversary can still do.** Nothing, directly, this is not an exploitable relaxation so
much as a *scope* relaxation, and it is the one most likely to be forgotten at deployment. The
proof covers a fixed-point training run producing fixed-point weights. If the artifact that then
gets served is a float model, or a re-quantized model, or the "same" model reloaded through a
different stack, the proof covers a different object than the one answering queries. The binding
between "the weights in the proof" and "the weights in production" is not cryptographic in any
system we have seen; it is operational.

:::gap  Almost nobody states the residual
The one training paper whose PDF we hold is also the one exception: [[zkpot-garg]] concedes in
passing that its definition assumes the commitment to the data and randomness is honestly generated
by the trainer, sketches a signature-based fix for the fine-tuning-over-a-foundation-model case,
and then omits it, and it files its fixed-point and piecewise-linear approximations under a
paragraph titled "Limitations and Extensions of Our Techniques". Nowhere else in the training table
does a summary state, in the form above, what an adversary can still do under the relaxation.
Papers state what they prove. Almost none state what they leave standing. If you are writing in
this space, that section, call it "what an honest proof still permits", is the cheapest possible
contribution and the one an auditor will read first.
:::

## The composition nobody has built

Read as a menu, the relaxations are complementary rather than competing. R4 (prove the compute)
and R5 (prove the data) are duals; R1 (prove the fine-tune) needs an attested base model; R4 needs
an audit of the committed data to mean anything. The end-to-end claim a buyer actually wants, 
*this served model came from this attested base, fine-tuned on this licensed, audited data, with
this optimizer, and here is the artifact*, is a composition of at least three of these.
[[zkaudit]] composes two, ZKAudit-T proves the model was trained by SGD on a committed dataset,
and ZKAudit-I then audits arbitrary properties of that hidden data and the resulting weights, but
nothing we have read binds either half to an attested base model.
