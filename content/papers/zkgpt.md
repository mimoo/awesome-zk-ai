---
title: zkGPT
paper: zkgpt
status: reviewed
---

## What is new

Two ideas, and they are genuinely orthogonal to each other, which is why the paper works.

**Constraint fusion** is the better one. Every quantized operator ends in a rounding step, and
every rounding step costs a range relation, and range relations — not the arithmetic — are what
the prover actually pays for. zkGPT classifies constraints into four types (arithmetic, division,
square root, exponentiation), builds a profitability table for merging adjacent pairs, and merges
greedily. Merging LayerNorm's mean, variance and square-root constraints collapses three range
relations into one. The error analysis is the part I did not expect to be sound and is: since
rounding a composed function is at least as accurate as composing two roundings, **fusion can only
reduce quantization error, never increase it**. That is a rare thing — an optimization that is
free in both directions.

**Circuit squeeze** is the more surprising one. GKR forces layer-wise dependency, so the prover
synchronizes threads at every small layer and wastes most of its parallelism on synchronization.
zkGPT observes that because every rounding result is already committed as *advice* in the input
layer, the subcircuits that check those roundings have **no topological dependency on each other**
— so they can all be flattened into the same set of layers. The circuit becomes wide and shallow,
and the threads have something to do. This is a Plonk idea imported into GKR, and it costs nothing
because the commitments were already there.

The rest — the bookkeeping-table grouping algorithm for Thaler's matmul protocol, the z-GeLU
approximation — is careful constant-factor work.

## What it actually proves

**One forward pass, over a 32-token context, at 16 bits, without zero-knowledge.**

Each clause is load-bearing:

- **One token.** There is no autoregression, no KV cache, no decode loop, no sampling. [[deepprove]]
  is right about this, and zkGPT does not dispute it.
- **32 tokens of context.** The evaluation section never says so, which is why `papers.yml` marked
  the context window as *inferred* from a matmul shape. It should not be marked inferred any more:
  §9.1 states it outright while explaining why one aggressive constraint merge is infeasible — the
  softmax input is described there as a vector of length 32 whose elements are 16-bit, giving a
  hypothetical merged lookup table of 2^512 entries. That is a stated sequence length, not an
  inference. It is also the shortest context of any LLM system in this collection by an order of
  magnitude, and the single most important variable when normalising zkGPT against
  [[deepprove]] or [[zkllm]].
- **Not zero-knowledge.** This is the finding. The paper's *title* is "An Efficient Non-interactive
  **Zero-knowledge** Proof Framework," and §4.4 ends with: "The zero-knowledge property can be
  incorporated into the protocol by using masking polynomials." *Can be.* It is not. Every prover
  time in the paper excludes the cost of the masking polynomials that would make the scheme
  zero-knowledge. The model weights are committed with Hyrax (which is hiding), but the ZK
  property of the *protocol* is future work. A paper whose stated motivation is that "the model
  parameters are trade secrets" does not implement the property that protects them.
- **The embedding layer is outside the circuit.** "our LLM circuit takes the input embedding matrix
  as public input." The token-to-vector lookup is not proven; the verifier must already hold the
  embedded input. Compare [[deepprove]], which proves embedding as a sparse one-hot matmul.
- BN254 at "around 100 bits of security" — the paper says so, honestly, and it is the weakest curve
  of any system here.

The quantization accounting is the best-documented of any zkML paper in this collection: the bit
width is stated, the scheme is stated, and the perplexity delta is reported on three datasets. Use
it as the reference point when normalising the others.

## What to distrust

**The headline end-to-end speedup silently folds in multi-threading.** §7.3 says the constraint
and circuit optimizations "accelerat[e] the end-to-end performance by 14.7×, unlocking great
optimization opportunities aside from trivially accelerating everything by multi-thread
parallelism." The sentence explicitly disclaims multi-threading — while the number does not.

:::audit The 14.7× is not the optimizations
Table 3, all on GPT-2:

| Configuration | Prover time |
|---|---|
| Single thread, no optimizations | 319.6 s |
| **32 threads**, no optimizations | 52.3 s |
| 32 threads, all optimizations | 21.8 s |

The 14.7× is `319.6 / 21.8` — one thread to thirty-two threads *and* both optimizations. The
optimizations alone are `52.3 / 21.8` ≈ 2.4×. The paper's own Table 5 agrees: disabling constraint
optimization costs 1.5×, disabling circuit optimization costs 1.7×. Neither the text nor the table
supports 14.7× as an optimization result.
:::

**The zkLLM comparison is argued, not measured.** zkGPT's prover is *slower* than [[zkllm]]'s in its
own Table 3. The paper's response is a TFLOPS ratio — the A100 has vastly more nominal compute than
the Xeon, so being only slightly slower means zkGPT "utilizes computation power in a much more
effective way" and is "very likely to outperform them under the same hardware."

That is a hypothesis, not a result, and it rests on the wrong normalization. **TFLOPS measures
floating-point throughput, and a zk prover performs none.** It does finite-field arithmetic and
multi-scalar multiplications over a 254-bit curve, where a GPU's advantage over a CPU is a small
fraction of its advertised FLOPs ratio. Nor are the two systems on the same curve: zkLLM runs over
BLS12-381, a materially larger field than zkGPT's BN254, which cuts in zkLLM's favour and is never
mentioned. Nobody has run these two provers on the same machine, and until someone does, the claim
is unfalsified rather than supported.

**The accuracy table and the timing table may not describe the same computation.** The perplexity
deltas are reported for the quantized model, but the evaluation never says at what sequence length
perplexity was measured — and a perplexity computed over a 32-token window would be a strange
thing to report. The accuracy claim also silently bundles two changes: the 16-bit quantization
*and* z-GeLU, zkGPT's own bespoke GeLU approximation. Their contributions are not separated, so
you cannot tell which one costs what.

**The baselines are real, which is worth saying.** Unlike most of this literature, zkGPT ran its
competitors rather than copying their abstracts — it re-measured ZKML and Lu et al. on its own
hardware and reports numbers that *disagree with those papers' own claims* (and with the
[[zkml-survey]]). Both conflicts are recorded in `papers.yml`. A paper that publishes numbers
making its baselines look *better* than the survey does is a paper doing its job.
