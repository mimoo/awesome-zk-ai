---
title: Where the cost goes, and why the numbers do not compare
section: private-inference
order: 40
lede: >-
  2PC pays in communication and rounds; FHE pays in homomorphic compute. Neither
  runtime is a property of the protocol alone -- it is a function of a network the
  paper chose, a fixed-point scale the paper chose, and in one case a model the paper
  modified. The headline number of the whole line is a competitor's reimplementation.
papers: [iron, bolt, ciphergpt, nimbus, bootstrapping-fhe, deepprove, zkgpt]
status: draft
---

In the verifiability column, cost means prover time and prover memory: a single machine grinds,
and then emits a small object that anyone can check cheaply. In this column, cost means something
structurally different, and it is worth being precise about what.

## 2PC: the bill is communication, and the invoice is itemised by operator

A secret-sharing-based protocol communicates on every non-linear operation. Multiplications need
a round. Comparisons need OT. A piecewise polynomial needs a comparison per breakpoint, a
multiplication per degree, and a truncation after each. The bytes add up per *activation*, and a
transformer has a lot of activations -- [[bolt]] points out that a single GELU layer in BERT-base
operates on a 128x3072 matrix, and there are twelve of them.

Two consequences follow, and they are the whole deployment story.

**First, the non-linears end up owning the bill.** [[bolt]] publishes a per-layer communication
breakdown of [[iron]] alongside its own, and the shape of it is the argument of this whole
literature. In [[iron]], the matmuls and the non-linears both cost gigabytes per encoder layer.
[[bolt]]'s HE matmul then cuts the linear layers by three orders of magnitude -- and once you have
done that, **essentially the entire remaining bill is Softmax, GELU and LayerNorm.** GELU is the
largest single line item in both systems. This is the exact inverse of the plaintext cost model,
where the matmuls are almost all of the FLOPs and GELU is a rounding error.

**Second, latency matters as much as bandwidth,** because the round count is dominated by the same
operators and each round pays a network round-trip. A linear layer in [[bolt]] costs a couple of
rounds; a Softmax costs *hundreds*, because every comparison and truncation in the approximation is
a round. This is why [[bolt]]'s advantage over [[iron]] widens as the simulated network gets
slower, and why [[bolt]] reports -- honestly, in a paragraph that is easy to miss -- that its
run-time savings "become less significant in extremely low-latency network settings." A 2PC runtime
is not a property of a protocol. It is a function of two numbers the paper picked.

## Which network did they pick? Different ones.

- [[iron]] evaluates in a **LAN** setting only.
- [[bolt]] evaluates in one LAN and **four** WAN settings, and its headline comparison against
  [[iron]] is drawn from a WAN setting.
- [[ciphergpt]] follows SIRNN and [[iron]] and evaluates in a **LAN** setting.
- [[nimbus]] evaluates in a LAN and a WAN setting -- neither of which is the same WAN [[bolt]] used.
- [[bootstrapping-fhe]] has essentially no network cost at all, so the axis does not apply.

Runtimes across these papers are therefore not on a common axis, and the *ratio* of runtimes
between any two of them is a function of a network neither of them ran on. Communication in bytes
is the more portable quantity, which is why the papers headline it -- but see below, because bytes
have their own confounder.

## The anchor number of the entire line is a reimplementation

Everyone quotes [[iron]]'s cost for one BERT-base inference as the thing to beat. That number is
not [[iron]]'s. [[iron]] never reports it.

It comes from [[bolt]], which had to build its own [[iron]]:

:::quote{src="BOLT" sec="§7.1.4, Iron's System"}
Because Iron [28] is not open-sourced, we implement Iron's end-to-end system following the
protocols described in their paper.
:::

And [[bolt]]'s reimplementation is not a faithful copy, for a defensible reason: it *removed*
[[iron]]'s LayerNorm optimization, having found that the optimization breaks the residual
connections and reduces the model to near-random output (this is the story on the section's index
page). It also ran [[iron]] at [[bolt]]'s own fixed-point scale, while noting that [[iron]] would
need a larger scale to hold its accuracy, because [[iron]] does not do secure-computation-aware
fine-tuning.

So the reference point that frames this entire literature is: a competitor's reimplementation, of
a paper with a bug in it, with the bug removed, at a precision the original would not have used,
on a network the original never ran.

:::debate  It gets worse, because the reimplementation chain has two links
[[ciphergpt]] compares against [[bolt]] -- and reimplemented it, because [[bolt]]'s code was not
yet released when [[ciphergpt]] was written ("Since Bolt is still unavailable, we implemented it
based on SIRNN with Ferret OT and followed the parameters given in their paper"). It also
reimplemented the secret-shared shuffle it needed for top-K. So a chain of reported speedups runs:
[[iron]] (as rebuilt by [[bolt]]) -> [[bolt]] (as rebuilt by [[ciphergpt]]) -> [[ciphergpt]], with
each baseline built by the party that wanted to beat it.

To be fair to the field: [[bolt]] and [[nimbus]] both released code, and [[bootstrapping-fhe]]
reports that it *reproduced* its baseline's published results before improving on them, which is
the practice the rest should be held to. But no independent party has ever benchmarked these five
systems against each other on one harness, and until someone does, the cross-paper speedup factors
are claims about reimplementations, not about protocols.
:::

## Two more confounders, both familiar from the zkML side

**The fixed-point scale is this column's bit width.** [[nimbus]] gets a real part of its win by
moving from a large ring and a large scale to a smaller ring and a smaller scale -- which it can
only do because its low-degree polynomials accumulate less fixed-point error. [[bolt]] benchmarks
[[iron]] at a scale it says [[iron]] could not actually use. Precision is a free parameter that
trades accuracy for communication, exactly as bit width trades accuracy for proving time in
[[deepprove]] and [[zkgpt]]. The zkML section of this SoK calls that the hidden variable. It is the
same variable, and the private-inference papers do not normalise for it either.

**Some of the speedup is a smaller model.** [[bolt]]'s word elimination ranks input tokens by their
attention scores -- summing the query-key product across an axis gives a per-token score -- and
obliviously discards the below-median half before the encoder stack runs, using a bitonic sort so
that neither party learns which tokens went. It is a good idea, it is done obliviously, it is
disclosed, and its accuracy cost against the floating-point baseline is small. It is also *not a
protocol improvement*: it is a model change, and it is responsible for a large fraction of
[[bolt]]'s reported communication advantage over [[iron]] -- as [[bolt]]'s own
no-word-elimination row makes plain. The honest protocol-versus-protocol comparison is that row,
and it is not the one that gets quoted downstream. Likewise, [[bootstrapping-fhe]]'s benchmarked
network is a *distilled* BERT-DyT, not BERT.

:::gap  Nobody reports the three numbers that would make this comparable
To compare two private-inference systems you need, in the same row: (1) communication in bytes
under a stated network, (2) accuracy delta against the floating-point model on a named task, and
(3) the model actually evaluated -- BERT-base, or BERT-base-minus-half-its-tokens, or BERT-DyT.
Every paper here reports some of these. None reports all three in a way that lines up with any
other paper's. That is not a lapse by any individual author; it is a missing convention.
:::

## FHE: the bill is compute, and it is paid in bootstraps

[[bootstrapping-fhe]] moves the entire cost to the server's CPU. The client encrypts once and
decrypts once, so communication collapses from the 2PC systems' hundreds of gigabytes to the size
of a few ciphertexts -- a difference of many orders of magnitude, and the whole reason anyone
tolerates FHE's compute. The dominant cost becomes bootstrapping, which is the operation that
refreshes a ciphertext's noise budget; [[bootstrapping-fhe]] reports that it accounted for the
majority of runtime in the prior state of the art, and its contribution is to make each bootstrap
do more work rather than to do fewer of them.

Two caveats before you read its runtime as a like-for-like win over 2PC:

1. **It is a batched, amortised figure.** The evaluation runs a batch of sequences per query and
   reports per-query cost amortised across the batch. That is a *throughput* number. The 2PC
   systems report single-inference *latency*. A service that gets one query at a time does not see
   the amortised figure, and the paper does not claim it would.
2. **It is not the same model** (BERT-DyT, LayerNorm replaced), and the comparison against the
   prior FHE state of the art is noted in the paper's own table as being against a system that
   still uses LayerNorm.

None of which makes the result less impressive. It makes it a different result.

## The scale ceiling, and why it is lower here

The verifiability column has proved inference for models in the billions of parameters
([[zkllm]]-class work, and [[deepprove]] on GPT-2 and Gemma-class models with real decode
throughput). This column is stuck at BERT-base, roughly 110M parameters, and the reason is
structural rather than incidental: prover cost in a sum-check system is roughly linear in the
circuit and can be sharded across machines, while 2PC communication is linear in the activations
*and* has to cross a network in sequence. You cannot shard your way out of a round trip.

That, and not any claim about which guarantee is more valuable, is why the two columns of the 2x2
have such different scale stories. They are limited by different physics.
