---
title: Sigma
paper: sigma
status: reviewed
---

Sigma is the paper that ends the claim this SoK has been making for its entire existence: that the
privacy column caps out at BERT.

It does not. Sigma runs **Llama2-13B** — the same model [[zkllm]] proves in the verifiability
column — with a 37.6-second online phase and 18.9 GB of online communication. [[iron]], the anchor
this repo has quoted for BERT-base, needs 280.99 GB and 216 minutes. Sigma does BERT-base in 1.72
seconds and 0.99 GB.

Four years, same threat-model family, four orders of magnitude.

## What is new

**Function secret sharing, on a GPU.** Our corpus contained no FSS papers at all, and that omission
is most of why the ceiling looked real. FSS moves the work into a preprocessing phase that produces
correlated randomness (the "keys"), after which the online phase is startlingly cheap.

Two ideas inside it are worth having even if you never touch FSS.

**Faithful truncation.** Sigma builds non-local truncation protocols in FSS and explicitly rejects
CrypTen's *local* truncations, which it cites as known-insecure. This is the same fault line the
[numerics page](/numerics/) draws between exact and probabilistic rescaling, and Sigma lands on the
exact side.

**Lookup-table shrinking by domain knowledge**, which zkML would recognize instantly. Rather than
Pika's $2^{50}$-entry table, Sigma observes that $\delta(x) = \mathrm{ReLU}(x) - \mathrm{GeLU}(x)$
is *zero outside* $(-4, 4)$ — so a **256-entry table** suffices for GeLU over 50-bit values. SiLU
gets 1024 entries. That is exactly [[jolt-atlas]]'s neural teleportation and [[deepprove]]'s
decomposable tables: shrink the domain, shrink the table. Two literatures, one move, no citation
between them.

## What it actually proves

Nothing. This is the privacy column — there is no proof object, no verifier, no third party who can
check anything. Sigma hides the client's input from the model owner and the model from the client,
against a **semi-honest** adversary, and that is all.

Read `threat_model` in `papers.yml` before citing it against anyone, because the trust model is
genuinely novel in this corpus and does not fit either existing slot:

- The **online** phase is 2PC, dishonest-majority. Like [[cheetah]], [[iron]], [[bolt]].
- The **preprocessing** is done by a **trusted dealer**. Sigma lists three ways to generate the
  correlated randomness and picks the one with a trusted third party.

So it is neither a peer of [[iron]] (which needs no dealer) nor of [[puma]] (whose third party is
untrusted-but-one-of-three). It is its own point in the space, and the honest way to state the
corrected finding is: *pure dishonest-majority 2PC with no dealer caps out at BERT-class. Private
inference does not.*

## What to distrust

:::audit  The headline is an online number and the preprocessing is enormous
Llama2-13B needs **419.01 GB of FSS keys**. Generating them takes 40.57 s on a GPU dealer, and
**transferring them takes 356.61 seconds** over the same 9.4 Gbps LAN the online phase runs on.

Against a headline of 37.59 s.

True wall-clock is roughly **435 seconds — about 11× the advertised figure.** Llama2-7B: 255 GB of
keys, 217 s of transfer, against 23 s online. The paper is not hiding this; Table 9 is in the
appendix and it is honest. But every number on the cover is the online column, and the online column
is not what a user waits for.

And the keys are **one-shot and shape-specific.** There is no amortization across queries. A second
inference means a second 419 GB.
:::

**The models the title is about have no baseline.** CrypTen OOMs on 7B and 13B. So the "12–19×
speedup" band is measured on BERT and GPT-2 — the models nobody needed FSS for — and the Llama rows,
which are the entire contribution, are compared against nothing.

**Table 4 says the encrypted model is better than the model.** BERT-base on MRPC: PyTorch 84.31%,
Sigma **87.25%**. A faithful fixed-point emulation scoring three points *above* the float model it
emulates is noise on a 408-example validation set — and it appears, without comment, in the table
whose job is to demonstrate faithfulness. It does not undermine the paper, but it tells you how
much weight that table can bear.

**It is a single forward pass.** The strings *KV cache*, *autoregressive* and *decoding* do not
appear. Generating $N$ tokens means $N$ full runs, each with a fresh key set — so at 419 GB per run,
generation is not something this system does. The [decode problem](/zk-inference/decoding-and-kv-cache/)
is unsolved on this side of the 2×2 too.
