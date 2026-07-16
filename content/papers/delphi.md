---
title: Delphi
paper: delphi
status: reviewed
---

Delphi was the largest bibliography hole this SoK had: **cited by nine of the thirty PDFs we hold**,
and absent from `papers.yml` entirely until July 2026.

It is famous for two ideas. It is *important to us* for a third one, which is not why anyone cites it.

## What it is famous for

**The offline/online split.** The server's weights are known *before* the client's input arrives, so
push all the homomorphic encryption into preprocessing, and the online linear layer becomes plain
secret-shared arithmetic. Every offline/online accounting table in [the private inference
section](/private-inference/) descends from this paper, including the ones that make [[sigma]] and
[[mosformer]] look faster than they are.

**The ReLU budget.** Use neural architecture search to decide *which* ReLUs to replace with quadratic
approximations, because a quadratic costs **192× less online communication and 10,000× less online
compute** than a garbled circuit. That is the founding move of the "co-design the network for the
protocol" school, which runs through MPCFormer, [[nimbus]] and [[encryption-friendly-llm]].

## What it is important to us for

**Delphi is the one paper in the privacy column that cites a paper in the verifiability column.**

It cites [[safetynets]]. Twice. In the body.

And *not for verifiability.* It cites SafetyNets as prior evidence about whether **quadratic
activations train well.** Delphi's body contains **zero** occurrences of "verifiable", "integrity",
"zero-knowledge", "proof of correctness", or "malicious server".

**It does not know it is citing a verifiability paper.** It is citing an ML result about activation
functions, and the fact that the ML result happens to live inside a zkML paper is invisible to it.

That single edge is the best evidence in this corpus for [the bridge page](/numerics/bridge/)'s
thesis. The two columns do not read each other *as cryptography*. Where they touch, and they do touch
they touch at the **numerics**, and they touch without noticing.

## And it answers an open question we posted last week

[The numerics page](/numerics/) has an open problem: *does a polynomial network escape the rescale
seam, or only postpone it?* [[safetynets]]'s celebrated ~5% prover overhead comes from an all-quadratic
network, and [[bionetta]] argues that polynomial activations merely relocate the seam into a precision
blow-up.

Delphi tried to scale the idea in 2020 and reported what happened:

:::quote{src="Delphi" sec="§5.1, Adapting NAS for DELPHI's planner"}
Prior work [Moh+17; Gil+16; Gho+17; Cho+18] and our own experiments indicate that networks that use
quadratic approximations are challenging to train and deploy: the quadratic activations cause the
underlying gradient descent algorithm to diverge, resulting in poor accuracy.
:::

`[Gho+17]` is SafetyNets.

Delphi needed gradient clipping, ReLU6, and a "gradual activation exchange" annealing schedule just to
make quadratic networks converge *at all*, and even then, it uses NAS to keep **most** activations as
ReLUs, because it cannot afford to replace them.

So the answer to our open question has been sitting in an MPC paper since 2020, cited by nine of our
own PDFs: **the all-quadratic network does not train.** SafetyNets' 5% is a number that exists at a
depth and a width nobody would deploy. The price of rounding is not optional; it is what you pay the
moment the network is big enough to be worth anything.

## What to distrust

**The bandwidth is never stated.** For a paper whose entire cost model is communication, Delphi
reports only the AWS regions its two instances sat in (us-west-1 and us-west-2) and never a Mbps or a
millisecond figure. Every latency number in it is therefore unreproducible in the dimension that
matters most.

**The accuracy delta is not tabulated**, only drawn, as curves, in Figures 7–9. Do not extract a
number from them.

**The planner leaks training data.** Delphi is unusually candid: because the NAS planner uses the
training set to decide where quadratics go, "revealing the network architecture reveals some
information about the data ... at most $\ell$ bits" ($\ell = 32$ for ResNet-32). A privacy system whose
*architecture* is a side channel on its *training data* is a nice reminder that the threat model always
has one more clause.
