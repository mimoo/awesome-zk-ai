---
title: What private inference actually buys you
section: private-inference
order: 10
lede: >-
  These systems hide your prompt from the server and the server's weights from you.
  They prove nothing at all about whether the answer is right. That is a different
  guarantee from the one the rest of this atlas is about, and the two are routinely
  conflated.
papers: [iron, ciphergpt, bolt, nimbus, bootstrapping-fhe]
status: draft
---

Everything in the verifiability column of the 2x2 produces an artefact a stranger can check.
Nothing in this section does. A 2PC or FHE inference protocol runs the model without either
party learning the other's secret, and then it stops. There is no proof. There is no transcript
a third party can audit. If the server computed something other than the model you agreed on,
the protocol will not tell you, and neither will the cryptography.

That is not a criticism of the work. Confidentiality is the goal, and these systems achieve it
under a clearly stated assumption. The problem is that "secure inference", "privacy-preserving
inference" and "trustworthy inference" all sound like the same phrase, and outside the two
communities that build these systems they get used as though they were.

{{ table:secure_inference_2pc }}

## The guarantee, stated precisely

A client holds an input. A server holds fine-tuned weights. They run a protocol; the client
learns the model's output on its input; the server learns nothing. [[iron]] was the first to do
this for a transformer, and it is careful to hide the intermediate activations of *every* layer,
not just the input — a direct shot at THE-X, which reveals each non-linear layer's inputs to the
client and which [[iron]] argues is therefore not really private at all.

What none of the five systems here provides:

- **Correctness against a deviating server.** All five are secure against a *semi-honest*
  adversary — one that follows the protocol exactly and only tries to learn from what it sees.
  A server that deviates is out of scope.
- **Public verifiability.** Even if the server behaves, the client cannot convince anyone else
  of what came out. There is no proof object.
- **Anything about the model's provenance.** The weights are private, which also means they are
  unaccountable. You are trusting that the ciphertext on the other side is the model you paid for.

## "A malicious server returns a wrong answer" is not a thought experiment

The cleanest demonstration that this line has no correctness story comes from inside the line
itself, and it does not even require a malicious party.

[[iron]] proposed folding LayerNorm's scale and shift into the following linear layer's weights,
saving a matrix multiplication. [[bolt]], reimplementing [[iron]] as its baseline, found that the
optimization is simply wrong: it ignores the residual connections, so the un-normalized value
flows around the skip path and the model falls apart.

:::quote{src="BOLT" sec="Appendix G, Clarification on Iron's LayerNorm Optimization"}
Iron's LayerNorm optimization is inaccurate and will introduce large errors to the inference and
make the model's performance close to random guessing.
:::

[[bolt]] says it confirmed this with [[iron]]'s authors, and removed the optimization from its
reimplementation before benchmarking against it.

:::audit  Nothing in the protocol notices
Read that failure through the threat model. The server was honest. It ran the published protocol
faithfully. The security proof holds — no secret leaked in either direction. And the client got
back something close to a coin flip, with no signal that anything was wrong, because a 2PC
protocol's output is a secret share, not a claim. The bug was caught by a competitor
reimplementing the paper to beat it, which is not a security control.

This is the failure mode the verifiability column exists to close, arriving in the privacy column
where there is no mechanism to catch it. It is also the argument against the reflex that
"privacy-preserving" and "trustworthy" are near-synonyms.
:::

## What it would cost to have both

The two guarantees are composable in principle, and the papers know it. [[bolt]] considers
malicious security and puts it in future work, for a reason that will sound familiar to anyone
who has read the zkML side:

:::quote{src="BOLT" sec="§9, Security Argument & Inference with Malicious Security"}
Supporting malicious security (either for both parties or for clients only) is a very interesting
direction for future work. It is challenging to adapt techniques from current state-of-the-art
malicious secure protocols.
:::

Its stated obstacle is that prior maliciously-secure inference protocols (MUSE, SIMC) handle ReLU
and comparisons — and the transformer non-linears are not that. The same three operators that
make proving expensive in [[deepprove]] and [[zkgpt]] are what make malicious security expensive
here. The page on non-linearities in this section says why that is not a coincidence.

:::gap  Nobody has built the both-and system at transformer scale
Maliciously-secure private transformer inference exists only by adding a party: Mosformer, cited
by [[bootstrapping-fhe]], is the first maliciously-secure *three-party* framework, and three-party
means an extra non-collusion assumption. In the two-party client/server setting that all five
systems here target, malicious security is unimplemented. And no system anywhere in this repo
emits *both* a privacy guarantee against the counterparty and a proof of correctness for a third
party. The 2x2's two columns have not been added together.
:::

## Where the line has actually gone furthest

Two results are worth pulling out of the table, because they are the ones with implications
outside their own community.

**[[ciphergpt]] is the only system here that handles generation.** Everything else evaluates a
BERT-class encoder: one forward pass, one classification. [[ciphergpt]] builds 2PC protocols for
autoregressive decoding — its matmul is specialized for the unbalanced shapes that word-by-word
generation produces — and it gives the first secure top-K *sampling* protocol, so the stochastic
decode step happens under encryption too. That is a capability the verifiability column does not
have: [[jolt-atlas]] proves a forward pass and says nothing about decode or sampling.

**[[bootstrapping-fhe]] is not in the same setting as the other four.** It is FHE, not 2PC: the
client encrypts, goes away, and the server evaluates the whole transformer on ciphertext with no
interaction. Its communication cost is the size of a ciphertext, not a transcript of an
interactive protocol, which is why its number in the table above is in a different unit from the
2PC rows in every sense that matters. Do not read that column as a ranking. The threat-models
page says why.
