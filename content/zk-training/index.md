---
title: The hardest claim in the table
section: zk-training
order: 10
lede: >-
  Proving inference means proving one pass over a fixed function. Proving training means
  proving an iterative, stochastic, data-dependent search for that function -- and then
  proving that the function you ended up with is the one you are showing people. Every
  system in this cell survives by refusing to prove part of that.
papers: [kaizen, zkdl, zkpot-garg, optimum-vicinity, verilora, zkboost, veriml, zkmlaas, summer, zkprov, artemis]
status: draft
---

A proof of training (zkPoT) is supposed to discharge a sentence like this:

> These weights $w$ are the output of running *this* training procedure, with *these*
> hyperparameters, on a dataset I committed to before I started.

Read that sentence carefully, because almost none of it is about arithmetic. It quantifies over
a dataset the verifier never sees, over a procedure that is stochastic, and over a computation
that ran for a long time. [[zkpot-garg]] is the paper that pinned the definition down and then
demonstrated it on logistic regression — the contribution is the definition and the feasibility
experiment, not the scale. Everything that came after is an attempt to make that sentence cost
less by proving less of it.

{{ table:training }}

## Why this is not "inference, but more steps"

The reflexive framing is that training is a forward pass repeated with a backward pass attached,
so proving it should cost some multiple of proving inference. That framing is wrong in four
separate ways, and each of them is a distinct engineering problem.

**The witness is the whole run, not the final state.** An inference proof's witness is the
activations of one pass. A training proof's witness is every activation, every gradient, and
every weight delta of every minibatch of every epoch. The final weights are a rounding error in
that object. This is why the interesting per-system trick is almost always about *composition* —
[[kaizen]] recursively composes a per-iteration proof so that proof size and verifier time stay
independent of how many iterations there were, and [[zkdl]]'s `FAC4DNN` circuit design
deliberately aggregates across layers *and across training steps* without being bound by their
sequential order. Both are answers to the same question: how do you avoid materializing the
entire run as one circuit?

**The computation is inherently sequential, and the proof system wants it not to be.** Step
$t+1$ consumes the weights produced by step $t$. That is a dependency chain as long as the
training run, and it fights every parallel prover. Recursion (Kaizen) and reordering (zkDL) are
the two known escapes, and both are the load-bearing idea of their paper rather than an
optimization detail.

**The statement is about data the verifier cannot see.** Inference proofs let the verifier hold
the input. Training proofs cannot — the dataset is the asset. So the dataset has to be
*committed*, and the proof must additionally establish that the same commitment was consumed at
every step. This is where cost quietly relocates: [[artemis]] exists because the consistency
checks binding committed parameters and data to the circuit can dominate the proof, and that
effect is strictly worse when the committed object is a training set rather than one image.

**Randomness is part of the statement, and it is adversarially useful.** Initialization,
minibatch order, dropout, augmentation: a training run is a function of its random tape. If the
prover chooses the tape freely, "I trained correctly" is a much weaker claim than it sounds,
because the prover may search over tapes until the run lands somewhere it likes. The honest
version of the claim requires the randomness to be bound — committed in advance, or derived from
a public beacon — before the prover knows what it will produce.

:::gap  Nobody in this cell tells us how the random tape is bound
We have no PDF for any paper in the training table, so we are reading abstracts, the survey's
tables, and the authors' own summaries. Across those, not one of [[kaizen]], [[zkdl]],
[[zkpot-garg]], [[verilora]] or [[zkboost]] is described as committing the training randomness
ahead of the run, and none of the summaries states what a prover who grinds the seed can achieve.
That may well be handled in the papers. It is not visible from outside them, and it is the first
thing we would ask for.
:::

## Fixed-point training is not the training you did

Finite fields have no floats. Every system here therefore proves a *quantized* training run, and
training is far less forgiving of that than inference is: quantization error in a forward pass is
absorbed once, whereas quantization error in a gradient is fed back into the weights and
compounds across steps. [[zkboost]] is the system that makes this visible, because it cannot
simply prove XGBoost — it has to define a fixed-point XGBoost and then argue that the fixed-point
variant reaches the same accuracy as the standard one.

The consequence is worth stating plainly, because papers in this cell tend not to: a zkPoT
certifies *a* training run, in the prover's arithmetic, of *a* model. It does not certify the run
you would have gotten from your GPU stack, and the weights it certifies are the fixed-point
weights. If a deployment then serves the float model, the proof covers a different object than
the one answering queries. Nothing in the literature we can see addresses that seam.

:::audit  What an auditor should ask a zkPoT first
Not "how fast is the prover." Ask: (1) what exactly is committed — data, hyperparameters, random
tape, architecture, initial weights? (2) is the final committed model the model that gets served,
bit for bit? (3) how many iterations does the proven run actually cover, and is that the whole
run or one iteration extrapolated? (4) what happens if the prover restarts the run and only
proves the attempt it liked?
:::

## The scale gap is not a detail, it is the field

Read the table with the model column in mind rather than the timing column. The systems that
prove *every step* prove them for logistic regression, a small CNN, a modest DNN, or a
gradient-boosted tree. The one system that reaches a genuinely large model, [[verilora]], gets
there by not proving a training run at all — it proves a LoRA fine-tune, with the base model
frozen. And a real pretraining run is orders of magnitude more steps over orders of magnitude
more data than anything in this table.

So the honest one-line summary of this cell is: **nobody has proven the training of a model
anyone would want to use, and the systems that come closest do so by changing the claim.** The
next page groups them by which part of the claim they gave up; the page after that asks, for each
relaxation, what an adversary can still do.
