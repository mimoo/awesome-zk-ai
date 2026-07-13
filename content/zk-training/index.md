---
title: The hardest claim in the table
section: zk-training
order: 10
lede: >-
  Proving inference means proving one pass over a fixed function. Proving training means
  proving an iterative, stochastic, data-dependent search for that function -- and then
  proving that the function you ended up with is the one you are showing people. Every
  system in this cell survives by refusing to prove part of that.
papers: [pol, pol-adversarial, pol-broken, kaizen, zkdl, zkpot-garg, optimum-vicinity, verilora, zkboost, veriml, zkmlaas, summer, zkprov, artemis]
status: reviewed
---

## Why this cell exists

Start with the paper that is *not* cryptographic, because every system below is arguing with it and
until July 2026 this SoK did not contain it.

**[[pol]]** (Jia et al., IEEE S&P 2021) proves training without any cryptography at all. Log your
checkpoints and your batch indices; the verifier re-executes the $Q$ **largest** weight updates per
epoch and checks they reproduce. Valid gradient steps are small, so an adversary faking a cheaper run
must introduce error, and error is loudest in the big steps. Elegant, cheap, and deployed.

Its security — *no adversary can forge a proof more cheaply than honestly training* — is **never
proved.** It is offered as **Conjecture 1**, and the authors say plainly they are "not aware of a
mechanism to prove those formally."

It was then broken twice.

**[[pol-adversarial]]** (S&P '22) fakes a training step by *optimizing the data*: exactly as you would
craft an adversarial example, gradient-descend on the input batch until it "generates" the stolen
weights. **[[pol-broken]]** (EuroS&P '23) — written largely by the *original PoL team* — does much
better, and much worse. Its infinitesimal-update attack interpolates the checkpoints and then logs a
learning rate of ~0, so every update is smaller than the verification threshold and the difference
between logged and replayed is trivially below it. Cost: **no training at all** — one floating-point
operation per parameter, bounded by a single forward pass. Its blindfold attack then defeats the
top-$Q$ heuristic by making exactly $Q$ real updates with a huge learning rate, so the verifier's
"check the biggest steps" rule lands on precisely the $Q$ honest ones and never looks at the fakes.

And here is why the two breaks belong in a cryptography SoK. **Both conclude, independently, that the
fix is cryptography** — and one of them prices it:

:::quote{src="Zhang et al." sec="§V, Countermeasures"}
This mechanism is valid, but it will introduce an overwhelming overhead.
:::

That sentence is about SNARKs. It is the cell you are reading.

:::gap  The scheme is unproven, not disproven — and the difference matters
[[pol-broken]] is careful in a way its citers are not. It does **not** show that PoL's guarantee is
false; it shows that it is **unprovable with current understanding**: *"one cannot develop a provably
robust PoL verification mechanism without further understanding of optimization in deep learning."*
Its own experiments find that data-ordering attacks and synthesized data both **fail** to reach the
target weights from an independent initialization — so knowledge of the final weights does appear
essential to a spoofer.

This is the same soundness-versus-statement distinction that runs through the entire SoK, and here it
runs in the *defender's* favour for once.
:::

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
checks binding committed parameters and data to the circuit can dominate the proof. It measures
that on a single forward pass, and we have not seen the equivalent measured for a committed
training set — which is the case a zkPoT actually needs.

**Randomness is part of the statement, and it is adversarially useful.** Initialization,
minibatch order, dropout, augmentation: a training run is a function of its random tape. If the
prover chooses the tape freely, "I trained correctly" is a much weaker claim than it sounds,
because the prover may search over tapes until the run lands somewhere it likes. The honest
version of the claim requires the randomness to be bound — committed in advance, or derived from
a public beacon — before the prover knows what it will produce.

:::gap  Only one paper here tells us how the random tape is bound
[[zkpot-garg]] puts the randomness inside the statement: its commitment is to (data, rand), and it
notes the randomness "can even be generated by the verifier itself to prevent potential choices of
malicious randomness selection". It is also the only paper in this table we hold a PDF for. For
[[kaizen]], [[zkdl]], [[verilora]] and [[zkboost]] we are reading abstracts, the survey's tables,
and the authors' own summaries, and none of those says whether the training randomness is bound
ahead of the run, or what a prover who grinds the seed can achieve. That may well be handled in
the papers. It is not visible from outside them, and it is the first thing we would ask for.
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
there by shrinking what is trained: it claims a proof of the forward pass, backward gradient pass
and weight updates of a LoRA fine-tune, on a frozen base model. The pretraining that produced that
base model is outside the statement. And a real pretraining run is orders of magnitude more steps
over orders of magnitude more data than anything in this table.

So the honest one-line summary of this cell is: **nobody has proven the training of a model
anyone would want to use, and the systems that come closest do so by changing the claim.** The
next page groups them by which part of the claim they gave up; the page after that asks, for each
relaxation, what an adversary can still do.
