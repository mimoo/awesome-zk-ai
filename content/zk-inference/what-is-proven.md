---
title: What is actually being proven
section: zk-inference
order: 20
lede: >-
  Several systems report a throughput number and the community ranks them against each
  other. They are certifying different claims on different inputs on different hardware,
  and in one case nobody knows what the claim is.
papers: [deepprove, zkgpt, zkllm, jolt-atlas, zkpytorch, zkml-kang, zktorch, nanozk, hao-et-al, artemis, lu-et-al]
status: draft
---

Take the throughput column of the [inference table](./). It is the number that gets
screenshotted, and it is the number this page exists to break.

A tokens-per-minute figure is a rate: *proven tokens* over *wall-clock minutes*. The
denominator is at least honest. The numerator is not a single quantity. Across the systems
in this section, "a token" silently means at least four different things.

## Four different claims

**1. All the tokens the model generated.** [[deepprove]] is explicit that this is its
contribution, and it is the strongest claim anyone makes:

:::quote{src="DeepProve" sec="Abstract"}
In this work, we present DeepProve, the first system to enable efficient end-to-end
verification of full LLM inference (i.e., for all generated tokens of a prompt) on
untrusted cloud servers using zero-knowledge proofs (ZKPs). In contrast, prior work either
provides only a proof-of-concept partial implementation for a single token (zkGPT,
USENIX'25), or focuses exclusively on specific components of the inference pipeline, such
as Softmax (zkLLM, CCS'24).
:::

Its throughput figure is therefore a genuine decode rate: the prompt is generated, and the
proof covers the whole generation. It is the only number in the table that means what a
casual reader assumes all of them mean.

Note carefully *how* it gets there. DeepProve does not put the autoregressive loop in a
circuit — it "achieves end-to-end verification by certifying the correctness of the output
sequence rather than encoding the expensive inference computation in-circuit," which it
says would force circuit size quadratic in the sequence length or in-circuit RAM. That is a
design decision with a cost profile, not a free lunch: among the succinct provers in the
table, DeepProve's proofs are orders of magnitude larger than [[zkgpt]]'s, which is what
certifying a whole sequence rather than one pass buys you.

**2. Exactly one forward pass.** [[zkgpt]] proves a single token. So, in effect, do
[[zkml-kang]], [[artemis]], [[lu-et-al]] and [[zktorch]] — their reported quantity is
*seconds to produce one proof of one pass*, and the tokens-per-minute entry attached to them
in `papers.yml` is marked `derived`: we computed it, by dividing sixty by their proving time.
Nobody in those papers claims it as a decode rate, and nobody should. ([[deepprove]]
characterises [[zktorch]] the same way — "proofs of correctness for one output token at a
time".)

The derivation is not merely conservative — it is *generous to the wrong system*. Sustained
generation is not one forward pass repeated. It has a growing KV cache, growing attention
cost per step, and a batching structure that a one-shot prover never has to confront. A
single-pass prover extrapolated to a rate is being credited with solving a problem it
never faced.

**3. A batched circuit over a sequence, with the loop decoupled.** [[zkpytorch]] does
something more interesting than either, and it is routinely missed because the paper is
filed as "a compiler". At its model level it observes that a proof only *verifies* the
output — it does not compute it — so the token-by-token dependency can be broken and all
tokens proven in a single batched circuit, turning many small matmuls into one large one.
That is the same insight DeepProve builds a whole system around, published earlier, in a
paper whose headline number is a per-token cost on a *single CPU core*.

:::gap  Is zkPyTorch's batched circuit the same claim as DeepProve's?
Both decouple the autoregressive dependency by exploiting the fact that the output is
already known. DeepProve claims priority for end-to-end multi-token verification and
[[zkpytorch]] does not contest it. But zkPyTorch's own §4 describes batching *all output
tokens of an LLM* into one proving circuit, which sounds like the same statement. We have
not resolved whether the difference is substantive (KV-cache handling? attention masking
across the batch?) or presentational. Until someone does, treat "the first to prove a full
generation" as a claim we are relaying, not one we have verified.
:::

**4. Nobody knows.** [[jolt-atlas]] reports an end-to-end proving time for GPT-2 and states
neither the sequence length nor the token count. It never discusses autoregression or KV
caching anywhere in the paper. Its GPT-2 result cannot be converted into a rate, cannot be
placed on the throughput axis, and cannot be compared to anything above — not because the
number is bad, but because the *unit is unknown*. `papers.yml` records its
`tokens_per_minute` as `null` and its `context_window` as `null`, and that is the honest
entry.

And a fifth, off the axis entirely: [[hao-et-al]] and [[nanozk]] prove *pieces*. Hao et al.
prove individual non-linear operators; NANOZK proves a transformer block. Neither has
proven a model. They belong in an operator comparison, not a system one.

## And sometimes, a different model

There is a further degree of freedom, and it is the one most likely to invalidate a
comparison outright: **the network in the circuit may not be the network in the model zoo.**

[[deepprove]]'s related-work section makes a specific and checkable accusation against
[[zkgpt]] — that it proves a modified GPT-2 which "doesn't contain residual connections,
attention masks, and the final projection layer," and that these relaxations "significantly
circumvent the outlier issues" that make quantization hard. It levels a second one at
[[zkml-kang]], calling its GPT-2 "slightly modified" too.

We cannot confirm the implementation from the outside. What we can confirm is the paper:
**the strings "residual", "attention mask" and "projection layer" do not appear anywhere in
[[zkgpt]]'s text** — a full-text search of the PDF returns nothing. That is not proof of the
accusation, but for a paper whose central claim is proving GPT-2, the silence is
conspicuous. A GPT-2 without residual connections is a different function, and residual
paths are precisely where the large-magnitude activations that make quantization hard tend
to live.

:::debate  Whose GPT-2?
Every LLM row in the table says "GPT-2". If [[zkgpt]] proves a GPT-2 without residuals,
attention masks and the final projection, and [[deepprove]] proves the whole thing, then the
two systems are not proving the same function — and the throughput gap between them is
partly a measurement of how much of GPT-2 each chose to include. The accusation comes from a
competitor and should be weighed as such. It is also *checkable in principle* — DeepProve is
open source; `papers.yml` records zkGPT's availability as unknown, which is itself part of
the problem. Until someone checks, this belongs alongside bit width and context length on
the list of confounders, not in the footnotes.
:::

## The confounders stack, and they all point the same way

Set aside what is proven for a moment and suppose every system reported the same claim. The
comparison would still be broken, because at least four variables move at once between the
two systems at the top of the table:

| Variable | Effect on the comparison |
|---|---|
| **What is proven** | A full generation versus a single forward pass. Not the same numerator. |
| **Which model** | A GPT-2 with residual connections and attention masks, versus one possibly without. Not the same function. |
| **Context window** | The systems' benchmark sequence lengths differ by more than an order of magnitude. Attention is quadratic in it. |
| **Bit width** | The faster system runs at the *lower* precision. Lookup-table cost scales with bit width. See [Quantization](./quantization/). |
| **Hardware** | CPU core counts, clock speeds and memory differ across every row. [[zkgpt]] attributes its entire gap to [[zkllm]] to CPU-versus-GPU, not to protocol. |

Every one of those pushes in the same direction — they all flatter the same system. That
does not make its result wrong. DeepProve is, by a wide margin, the fastest reported LLM
prover, and its lead is large enough to survive a lot of normalization. But the headline
ratio between it and [[zkgpt]] — the one people quote — is *not a protocol comparison*, and
**nobody has isolated the protocol contribution.** The honest statement is that the two
systems are two orders of magnitude apart on a rate whose definition differs between them.

:::debate  Should derived throughput numbers exist at all?
The case for: without them there is no way to put a single-pass system on any chart with a
multi-token one, and the alternative is a table with holes where the comparison should be.
The case against: a derived number is indistinguishable from a reported one once it has
been screenshotted, and the derivation embeds an assumption (that decode is a forward pass
in a loop) that is *false*. We keep both, and tag `tokens_per_minute_source: reported`
versus `derived` in `papers.yml` so the chart can shape them differently. If you take one
thing from this page: **a hollow marker is not a slower system, it is a different claim.**
:::

## Hardware is not held constant either

[[zkgpt]] is CPU-only. [[jolt-atlas]] deliberately runs on a laptop with consumer memory —
its entire thesis is on-device proving, and its numbers should be read as *what a laptop can
do*, which is a far more impressive framing than the row it occupies in the table.
[[zkllm]] is a datacenter GPU. [[zkml-kang]] and [[artemis]] use very large multi-core
machines. [[zkpytorch]]'s headline is a *single core*, which makes it the most sandbagged
entry in the table and the one most likely to be misread as slow.

A cross-system throughput comparison across that hardware spread is, at best, indicative of
which *engineering effort* is furthest along. It is not a measurement of which protocol is
better.

## What a paper in this field should report

None of the systems here report all four of these. Most report one or two.

1. **The sequence length** used in the benchmark, and the **number of tokens** the proof
   covers. Without these the throughput figure has no unit.
2. **The bit width**, and the **accuracy delta** it costs on a named metric and dataset. A
   throughput number with unbounded accuracy loss is not a result — any system can go
   arbitrarily fast by quantizing to garbage.
3. **The hardware**, including thread count, and which machine the *headline* figure came
   from when several were used. ([[deepprove]] is exemplary here and it still takes care:
   its headline throughput comes from its *secondary* machine, not its primary one.)
4. **Whether the proof covers a generation or a pass**, stated in one sentence, in the
   abstract.
5. **Every layer of the reference architecture the circuit does not implement.** If the
   residuals or the attention mask were dropped to make quantization tractable, that is a
   result about a different network and it belongs in the abstract, not in a competitor's
   related-work section.

:::gap  Nobody has done this
Not one system in this section reports sequence length, token count, bit width *and* an
accuracy delta together. The two that come closest — [[deepprove]] and [[zkgpt]] — each
miss at least one, and the field's fastest laptop prover ([[jolt-atlas]]) misses three of
the four. Until a paper does, cross-system throughput ranking is a genre convention, not a
measurement.
:::
