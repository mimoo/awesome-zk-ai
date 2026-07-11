---
title: CipherGPT
paper: ciphergpt
status: reviewed
---

## What is new

CipherGPT is the only paper in either column of this repo that takes **generation** seriously, and
that is what makes it worth reading from the zkML side.

Everyone else — [[iron]], [[bolt]], [[nimbus]], [[bootstrapping-fhe]] on the privacy side;
[[zkgpt]], [[zkllm]], [[deepprove]], [[jolt-atlas]] on the verifiability side — computes or proves a
forward pass. CipherGPT builds protocols for what an LLM *actually does*: emit one word, append it,
run again, and sample from the resulting distribution. Three contributions follow from that framing:

**sVOLE matmul specialized for autoregression.** Each generated word is one inference producing an
*unbalanced* matmul (a thin activation against a fat weight matrix). Subfield VOLE is efficient
exactly when the dimensions are lopsided, and — crucially — the *same* weight matrix recurs across
every generated word, so the correlations can be preprocessed once for the whole response.

**Spline-based GELU.** One lookup to find which interval the input falls in, then a single
per-interval linear function `y = ax + d` evaluated by multiply-then-truncate. This dodges both
failure modes of the alternatives: the error accumulation of SIRNN/[[iron]]'s multi-step iteration,
and the approximation error of [[bolt]]'s and BumbleBee's high-degree polynomials. It is the most
precise GELU in the cluster and it costs the fewest primitives. Genuinely good.

**The first secure top-K *sampling* protocol.** Shuffle the logit vector, then run a modified
quicksort that only recurses into partitions containing the top-K — the comparison results leak
nothing because the vector was shuffled first, and the recursion cuts comparisons from `O(n log n)`
to `O(n)`. Then sample one element according to secret-shared probabilities with `K−1` comparisons
and `K` multiplexers. Prior work either used garbled circuits (unaffordable) or simply took the
argmax, "thereby diminishing the utility of the LLMs."

That last sentence is the one the zkML column should sit with. **[[deepprove]]'s certification
argument depends on argmax determinism, and it concedes that randomized decoding "is not included in
our implementation, same as all prior works."** The privacy literature built the sampling protocol
that the verifiability literature has not.

## What it actually proves

Nothing — no proof is produced. What it *computes*, privately and against a semi-honest
counterparty, is a full 256-word GPT-2 generation, with the bit widths stated (12 fractional bits, a
37-bit ring), single-threaded, over a LAN.

And it tells you what that costs, in a sentence the rest of the field's summaries do not quote:

:::quote{src="CipherGPT" sec="§IX, Discussion"}
Our benchmark (Table V) shows that CipherGPT requires a latency of 20 minutes and a bandwidth of 15
GB to produce a token.
:::

**Per token.** That is the number that belongs in `papers.yml`, which currently records only
component-level speedups for this system. It is the anchor for autoregressive private inference the
way [[iron]]'s figure is the anchor for a single BERT pass, and it is far more sobering: a
several-hundred-word response is measured in days and terabytes. The paper says so plainly — "this
level of cost is currently impractical" — which is more than most papers here manage.

## What to distrust

**The headline matmul speedup is amortized in a way the baselines are not, and the authors say so.**

:::quote{src="CipherGPT" sec="§VIII-D, Evaluation results"}
We acknowledge that this comparison may be considered unfair, but it accurately reflects the setting
for GPT inference.
:::

The headline matmul figure is measured by amortizing the sVOLE preprocessing across a 256-word
response, exploiting the fact that the weight matrix is constant across iterations. The baselines
([[iron]], [[bolt]], BumbleBee) get no such amortization, because their protocols cannot use it —
which is, to be fair, precisely CipherGPT's structural advantage. But it means the figure is not a
protocol-against-protocol comparison, it is a *deployment-setting* comparison, and it grows
arbitrarily with the response length the authors choose. `papers.yml` and the README carry the
matmul speedup with no caveat; the caveat is in the paper, written by the authors, and should travel
with the number.

**The paper's flagship contribution is never evaluated for its effect on output quality.** The
accuracy experiment compares CipherGPT's outputs against floating-point GPT-2 on 10,000 WikiText
sentences and finds them near-identical — but:

:::quote{src="CipherGPT" sec="§VIII-D, Evaluation results"}
To eliminate the interference of top-K sampling, we set K = 1 for both CipherGPT and GPT-original to
predict the most possible word.
:::

`K = 1` is argmax. The accuracy of the system is measured with **the secure sampling protocol turned
off**. It is a defensible experimental choice — you cannot compare two stochastic decoders by
equality — but it means the paper's most-touted novelty, the thing that distinguishes it from every
other system in this repo, has **no reported effect on the model's output distribution at all**. Does
the secret-shared probability arithmetic distort the sampling distribution? Does the fixed-point
truncation of the softmax outputs bias which of the top-K gets picked? Unknown. For a protocol whose
whole justification is that argmax "diminish[es] the utility of the LLMs," not measuring the utility
you restored is a conspicuous gap.

**LAN only.** Every result is on a fast local link with sub-millisecond latency. This is a
communication-bound protocol shipping gigabytes per token; on any realistic WAN the numbers change
character entirely. [[bolt]] reports across several network settings, and its speedup spread turns
out to be almost entirely explained by bandwidth. CipherGPT reports one network.

**Single-threaded, which cuts the other way.** Every number here is from one thread on a c5.9xlarge.
That is a *conservative* choice and worth saying out loud, since most of this cluster reports
multi-threaded figures.
