---
title: PUMA
paper: puma
status: reviewed
---

PUMA is the paper that shows the BERT ceiling is a **2PC** ceiling, not a privacy ceiling.

[[iron]] needs 280.99 GB and 216 minutes for one BERT-base inference. PUMA runs **LLaMA-7B** — sixty
times the parameters — in 200 seconds and 1.79 GB. Nothing about *privacy* forbids scale. What
forbids scale is dishonest-majority two-party computation.

## The threat model, which is the whole story

:::quote{src="PUMA" sec="§3.3, Threat Model"}
PUMA is secure against a semi-honest adversary that corrupts no more than one of the three computing
parties.
:::

**3PC, semi-honest, honest majority.** Model owner and client secret-share the weights and the input
to three non-colluding servers; the result is reconstructed to the client. PUMA picks this setting
explicitly because it "has the highest concrete efficiency."

That third party is not free, and it is the reason a PUMA latency cannot be placed next to an
[[iron]] latency without a sentence of explanation. But it is also not exotic — it is the standard
honest-majority MPC assumption, and an entire branch of the field runs on it. Our corpus simply
contained none of that branch.

## What is new

The interesting parts are all about the same three operators the [verifiability
column](/zk-inference/) fights.

**GeLU** gets a four-piece low-degree polynomial (split at $-4$, $-1.95$, $3$), fitted with
`numpy.polyfit` and evaluated with three secure comparisons — rather than composing tanh and sigmoid
out of generic exponential and reciprocal protocols.

**Softmax** gets a clipped Taylor "negExp": add $\varepsilon$ so every exponent input is strictly
negative, clip below $-14$, evaluate $(1 + x/2^t)^{2^t}$ by repeated squaring, and replace $n$
divisions with **one reciprocal and $n$ multiplies**. The max-subtraction, the range clipping, the
division-avoidance — every move here has a twin in [[zkgpt]] or [[deepprove]], reached independently.

**Secure Embedding** builds the one-hot vector *inside* MPC via secure equality tests, which is why
unmodified HuggingFace checkpoints load. MPCFormer had pushed one-hot generation to the client.

And the accuracy holds where it is measured: GLUE within 0.011 of plaintext, GPT-2 perplexity within
0.02.

## What to distrust — and there is a lot

:::audit  The number on the cover is in no table
The title says five minutes. The abstract says "around 5 minutes to generate 1 token." §5.4 says
"around 200 seconds."

**Table 6 says 200.473 s** for eight input tokens and one output token, and **364.527 s** for two
output tokens. Three framings of one measurement, and the one on the cover is not the one in the
table. 200 seconds is 3.3 minutes; 364 is 6.1.
:::

**The LLaMA-7B prompts are four and eight tokens.** No realistic prompt length is ever run on
LLaMA-7B, and softmax cost is superlinear in sequence length, so the number does not extrapolate.

**The LLaMA-7B row is on completely different hardware from everything else in the paper.** BERT and
GPT-2 run on 32-vCPU / 128 GB machines over a 5 Gbps link. LLaMA-7B runs on **128-thread, 1 TB RAM
machines over a 20 GB/s link.** The headline assumes a datacenter.

**No accuracy number for LLaMA-7B exists.** The GLUE and perplexity tables cover BERT and GPT-2. The
evidence for the model in the title is one prompt in an appendix, "with fixed randomness."

**No KV cache.** The paper never mentions one. Going from one output token to two costs 1.82× — close
to a full re-run of the forward pass. Whatever this is, it is not efficient decoding, and it is the
same wall [[ciphergpt]] hit.

**And the win evaporates at length.** At GPT-2 with 256 input tokens, PUMA's communication is
**0.936×** MPCFormer's — that is, *worse* than the baseline it beats everywhere else. The paper
reports this. Nobody who cites the five-minute figure does.
