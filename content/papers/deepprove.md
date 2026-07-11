---
title: DeepProve
paper: deepprove
status: reviewed
---

## What is new

The contribution that matters is not cryptographic. It is a *certification argument*, and it is
almost embarrassingly simple:

:::quote{src="DeepProve" sec="§3.1, Certification of the LLM Inference"}
It just feeds the entire sequence of input and output tokens into the model at once, essentially
performing a single inference step.
:::

Because a causal attention mask means the model's prediction at position `t` cannot see position
`t+1`, running one forward pass over the *concatenated* prompt-plus-answer sequence and checking
that each position predicts its successor certifies the whole generation. Proving cost drops from
quadratic in the token count to linear — really, to the cost of a single forward pass, whatever
the answer length. Everything else in the paper (per-layer PIOPs for requantization, RMSNorm,
grouped-query attention, RoPE; delayed requantization; outlier clamping) is competent
engineering in service of that one observation.

Two things genuinely distinguish it from the rest of the field. First, it is the only system here
that **proves round-by-round knowledge soundness for each component** — "We formally prove that
each component is round-by-round (knowledge) sound" — which is precisely the property that makes
the Fiat–Shamir compilation safe, and therefore the only direct answer anyone in this repo has
given to the Fiat–Shamir/GKR attack. Second, it is a *complete, open-source* system rather than a
proof-of-concept for one layer, which is a fair criticism of [[zkgpt]] and [[zkllm]] and DeepProve
is right to make it.

## What it actually proves

A **single forward pass over the concatenated prompt-and-answer sequence**, under **greedy
(argmax) decoding**, at 12-bit quantization, against a model the prover committed to.

Unpack that, because the abstract's "full LLM inference (i.e., for all generated tokens of a
prompt)" invites a stronger reading than the system supports:

- **The prover does not re-run the generation loop.** It proves one pass and *infers* the rest
  from the attention mask. This is sound, and it is the paper's contribution — but the *cost* is
  one forward pass, exactly like [[zkgpt]] and [[zkllm]]. What differs is what the paper counts
  against that cost (see below).
- **Sampling is not proven.** The certification depends on argmax giving determinism. The paper
  sketches a de-randomization via a public randomness beacon and then states plainly: "we do not
  include this in our implementation, same as all prior works on verifiable LLM inference." Every
  benchmarked number is greedy decoding. Real serving uses temperature and top-p. Note that
  [[ciphergpt]], on the *privacy* side, does build a secure top-K sampling protocol — the zkML
  column still has no answer here.
- **Zero-knowledge is not achieved.** The paper defines zero-knowledge in an appendix and never
  claims its construction satisfies it; there is no hiding commitment, no masking polynomial, no
  ZK theorem. DeepProve is a succinct *argument*, not a zero-knowledge one. The weights are
  committed, not hidden. That is fine for the "lazy cloud swapped the model" threat, and fatal for
  the "model weights are a trade secret" motivation the introduction leans on.
- **The quantization is assumed, not proven.** The prover picks the calibration set, the scale
  factors, and the outlier-smoothing rotation. Nothing in the proof binds the committed integer
  model to any floating-point model a user would recognise.

## What to distrust

**The throughput metric is not the metric the baselines are measured with.** DeepProve counts
every token in the certified sequence against the cost of one forward-pass proof. Its comparison
table converts [[zkgpt]] and [[zktorch]] to the same units by counting *one* token per proof —
which is what those papers claim, but not what their provers *cost*. zkGPT's forward pass over
its context would, under DeepProve's own certification argument, certify nearly all of those
tokens too; the argument is a property of the GPT-2 architecture, not of DeepProve's prover. So
the headline multiple is mostly the certification insight, and it is a *free* insight that any of
these provers could adopt. The genuine prover-speed advantage is unmeasured, and is certainly far
smaller.

**The comparison table normalises the wrong variables.** It lists CPU, thread count and RAM — and
omits the two variables that actually decide the answer: sequence length (DeepProve's context is
an order of magnitude longer than zkGPT's, and attention is quadratic in it) and bit width
(12 vs 16). Both cut in DeepProve's favour once you see them.

**The fastest prior system is excluded.** "We exclude the comparison with zkLLM [SLZ24] since
their performance numbers rely on GPU acceleration and are not replicable in CPU environments."
The hardware objection is legitimate. But by [[zkgpt]]'s own measurements, zkLLM's prover beats
zkGPT's on GPT-2 — so the abstract's speedup over "the state of the art" is measured against a
system that, on the evidence of the very paper it cites, is not the state of the art.

**The Gemma 3 accuracy table is not a usable accuracy claim**, and the reason is not the one the
paper gives. Its floating-point Gemma 3 perplexity baseline is an order of magnitude worse than
its floating-point GPT-2 baseline on the same dataset under the same protocol — for a model with
more than twice the parameters. Either the 256-token non-overlapping evaluation window suits
Gemma 3 badly, or the baseline is misconfigured. You cannot measure quantization damage against a
broken baseline, which is why the quantized model *beats* it.

:::audit Internal inconsistencies, printed without comment
Three, and the repo owner should know all of them:

1. **Peak throughput contradicts itself.** §5 states the peak is 174 TPM "for GPT-2 at sequence
   lengths 512 using BaseFold", then in the next paragraph: "Remarkably, the best TPM we achieved
   in our experiments is 175, obtained for GPT-2 at sequence length **256** using the secondary
   machine." The same section also asserts throughput *increases* with sequence length. Table 3
   uses 175.08. The abstract uses 174. Three numbers, two sequence lengths, one claimed trend that
   contradicts the claimed peak.
2. **Verification time.** The abstract says 1–3.7 s; §1.2 says ~1.2 s (GPT-2) and ~4 s (Gemma 3);
   Table 1 prints 3.22 s and Table 2 prints 1.65 s for GPT-2 at the same sequence length on
   different machines. There is no single verification figure in this paper.
3. **Table 4's quantization curve is non-monotone in two places** — GPT-2's cosine similarity is
   *worse* at 12 bits (0.9966) than at 10 (0.9993), and Gemma 3's 12-bit perplexity (454.72) is
   *better* than its own fp32 baseline (515.46). Neither is explained.
:::

**The memory criticism is self-inflicted.** §1 dismisses [[zktorch]] because "the experimental
evaluation of [CTK25] reports results for a machine with 4 TB RAM." §5 then concedes that
DeepProve at its largest evaluated instance needs most of a workstation's memory, and that
"proving models with more than 3 billion parameters, such as GPT-J, would likely require over a
terabyte of RAM." That is the same objection, aimed at the same model class, arriving one
paragraph too late.

**Credit where it is due.** The paper is unusually honest about its own overhead — it reports the
plaintext CPU throughput of GPT-2 alongside its own, and concedes that for short-output queries
the gap is close to three orders of magnitude. Most papers in this collection do not print the
number that makes them look worst. This one does.
