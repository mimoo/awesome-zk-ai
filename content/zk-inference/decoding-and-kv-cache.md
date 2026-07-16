---
title: Decoding, autoregression, and the KV cache
section: zk-inference
order: 55
lede: >-
  Everything else on this site proves one forward pass. But an LLM generates by looping that
  pass, each step depending on the last -- and that loop, plus the KV cache it usually needs,
  is where the systems diverge most sharply. Three of them make the loop disappear; one
  actually runs it.
papers: [deepprove, jolt-atlas, zkpytorch, ciphergpt, zkgpt, zkllm]
status: reviewed
---

A transformer forward pass turns a length-$s$ context into logits. Proving that pass is what the
rest of this section is about. But that is not what an LLM *does*, it **generates**, one token
at a time, each step feeding the previous output back as input. Two problems fall out of that
loop, and they are the sharpest fork in the design space.

**The quadratic problem.** Generating $t$ tokens the honest way is $t$ forward passes over a
sequence that grows each step: $O(t^2)$ work. In plaintext inference you avoid this with a **KV
cache**, you keep each layer's past keys and values so step $t$ only computes the new token, not
the whole prefix. But a KV cache is *mutable state*: a buffer written and later read at
data-dependent positions. Proving a computation with mutable state means proving **read/write
consistency**, which is exactly the expensive thing (`RAM emulation in-circuit`) that every
system here would rather not do.

**The determinism problem.** A soundness statement about "the output" presumes there *is* one.
Greedy (argmax) decoding is deterministic, so it is provable. **Sampling**, top-$k$, temperature
is not: the output depends on randomness the verifier cannot see, so proving it requires
proving the sampler drew honestly from the claimed distribution.

## Four answers

The verifiability column mostly makes the loop *disappear*. The privacy column can't, so it is
the one that actually runs it.

**[[deepprove]], certify the whole sequence.** Rather than prove $t$ sequential steps, feed the
concatenated prompt *and* claimed output into the model as a single pass, and check that every
position predicts its successor. The causal mask guarantees position $t$'s computation cannot
see token $t{+}1$, and argmax supplies determinism, so if position $t$ predicts the claimed
token $t{+}1$, that token was correctly generated. This turns $O(t^2)$ into $O(t)$, needs **no
in-circuit KV cache**, and, because a single pass produces all $s$ predictions at once, 
throughput *rises* with sequence length (DeepProve reports 127 → 175 TPM as context goes 64 →
512, as matmul's sub-linear prover cost amortises over more tokens). This is the strongest idea
in the proving column, and it is why "tokens per minute" is even a meaningful axis for it.

**[[jolt-atlas]], prove one forward pass, and stop.** Read from the source, the prover proves a
*single* fixed-length forward pass: every entry point sets `("past_sequence_length", 0)` and
calls `prove` once. There is **no KV-cache machinery anywhere** in the codebase (grep
`kv_cache` / `past_key_values`, nothing), and no autoregressive proving loop. Generation exists
only as an *unproven* tracer helper (`gpt2_generate.rs`) that reloads the model and re-runs a
full forward pass over the whole growing sequence per token, the naive quadratic path, used to
sanity-check quantised-vs-float coherence, producing no proof. This is the concrete reason its
"~38 s for GPT-2" [cannot join the throughput axis](./comparison/): it is one pass at some
sequence length, not a per-token decode rate. Jolt Atlas *could* express a KV cache as read/write
consistency, it already carries Jolt's Twist-and-Shout memory machinery for `Gather` reads, but
it does not, because there is no cache to check.

**[[zkpytorch]], batch all the tokens.** A proof only has to *verify* the output, not *compute*
it, so the autoregressive dependency (token $t$ waits on $t{-}1$) can be **decoupled**: since
all output tokens are already known at proving time, prove them together in one batched circuit.
Batched transformer matmul is $O(WH + LH)$ gates versus $O(LHW)$ for $L$ sequential ones. Same
destination as DeepProve's certification trick, make the loop vanish, reached from the
compiler side rather than the protocol side.

**[[ciphergpt]], actually run the loop, privately.** The odd one out, and it lives in the
[privacy column](../private-inference/). Because privacy does *not* get to decouple, the server
genuinely has to compute the next token to return it, CipherGPT is the only system in either
column that builds bespoke protocols for real autoregression: each response word is one secure
inference producing an *unbalanced* matrix multiplication, and it combines them over subfield
VOLE. And it is the only one to tackle the determinism problem head-on, with the **first secure
top-$k$ sampling protocol**, securely drawing one element from a secret-shared probability
vector. The capability the whole verifiability column sidesteps, the privacy column had to
confront.

## The shape of it

| | Autoregression | KV cache | Sampling |
|---|---|---|---|
| [[deepprove]] | certified in one pass (anti-quadratic) | avoided — no RAM introduced | argmax only (determinism is the soundness lever) |
| [[jolt-atlas]] | not in the prover — single forward pass | none in the codebase | none |
| [[zkpytorch]] | batched — dependency decoupled | avoided — batch, don't cache | argmax |
| [[ciphergpt]] | genuinely run, word by word | *(2PC state, not in-circuit RAM)* | **first secure top-$k$ sampling** |

The through-line: **materialising a KV cache is the thing everyone avoids**, from opposite
directions. The proving systems avoid it by never introducing mutable state (certify the whole
sequence, or batch it); the MPC world avoids in-*circuit* RAM but still pays for stateful
interaction, which is why the 2PC literature has its own line of work, MPCache, on making
KV-cache eviction cheap under secret sharing. Two columns, one avoided data structure.
