---
title: zkLLM
paper: zkllm
status: reviewed
---

## What is new

**`tlookup`** replaces the sequential, univariate-polynomial lookup arguments of the plookup
lineage with a sum-check over multilinear extensions of *tensors*. The logarithmic-derivative
identity it rests on is standard; the contribution is noticing that once you phrase it over
tensors, every step parallelizes onto a GPU, which the univariate constructions cannot. That is
why zkLLM was the fastest LLM prover of its generation, and it is a systems insight dressed as a
protocol.

**`zkAttn`** is the sharper idea. A lookup table for Softmax is impossible, the function is
multivariate, so you would have to tabulate every input *vector*. zkAttn escapes by exploiting two
properties of the exponential: shift-invariance lets you normalize each row so the outputs sum to
one, and *homomorphism* lets you decompose the shifted input into base-`b` digits and take the
**product of per-digit exponentials**, each of which is a univariate table. The normalizer `ẑ`,
which is the genuinely un-provable part, is never proven directly, instead the prover is forced to
show that the row sums of the output land in a narrow tolerance band. It is a lovely piece of
protocol design: an intractable equality replaced by a tractable range check that pins it just as
tightly.

The optimization on top is the part worth stealing. Segments at the extremes of the digit
decomposition are set to *constant* tables, the most-significant digits become an indicator
(saturation region: the exponential is already zero), the least-significant become the constant 1
(the exponential is already one). Only the middle segments need real tables. The error bound in
Theorem 7.1 falls out of that split and is what sets the tolerance band.

## What it actually proves

**One forward pass, over a 2048-token sequence, with hidden weights, against a semi-honest
verifier, interactively.**

- **The sequence length is the headline nobody quotes.** "applying samples with the default
  sequence length of 2048 from the C4 dataset." zkLLM's proof covers a context two orders of
  magnitude longer than [[zkgpt]]'s and four times longer than [[deepprove]]'s. `papers.yml` records
  it as `null`. It should not. Any cross-system throughput comparison that ignores this is
  meaningless, attention is quadratic in sequence length, and zkLLM is paying the most.
- **It is still one forward pass.** "the entire inference process" means the whole model over the
  whole prompt, not a multi-token generation. [[deepprove]]'s criticism, that zkLLM does not handle
  autoregression, is correct, though DeepProve's own answer also costs exactly one forward pass.
- **It is genuinely zero-knowledge**, and it is the only LLM prover here that both claims and
  proves it (Theorem 7.4, with hiding Pedersen/Hyrax commitments and ZK sum-check). [[zkgpt]]
  defers ZK to future work; [[deepprove]] never claims it. On the property that the whole MLaaS
  motivation depends on, zkLLM is the honest one.
- **But the ZK holds only against a semi-honest verifier.** "A semi-honest assumption is applied to
  the verifier." A verifier who deviates, who chooses its challenges adversarially rather than at
  random, is outside the model. That is a real weakening, and it is stated once and never
  revisited.
- **And there is no Fiat–Shamir.** The string does not appear in the paper. Protocol 1 has the
  verifier sending live random challenges. As written, zkLLM is an *interactive* protocol, like
  [[safetynets]] and unlike everything else in this table. See the flag below.
- **The accuracy accounting is complete and clean.** C4 perplexity, floating-point baseline and
  quantized, for eight models across two families, with the delta shrinking monotonically as the
  model grows. `papers.yml` records zkLLM's `accuracy_retention` as `null`. That is wrong, and the
  correction matters: zkLLM's accuracy reporting is arguably better than [[zkgpt]]'s, which covers
  one model.

## What to distrust

:::audit The abstract contradicts Table 1 on verification time
The abstract and §1 both promise proofs "verified within 1-3 seconds." Table 1 prints verifier
times of **3.71 s** (OPT-13B) and **3.95 s** (LLaMA-2-13B). The two largest models, the ones the
paper's headline claim is about, both fall outside the range the paper states for them.

This one propagates. The [[zkml-survey]]'s Table VI records zkLLM's verification as "< 3s,"
faithfully copying the abstract rather than the table. `papers.yml` currently carries 3.0 s from
the survey. The correct figure, from the paper's own table, is 3.95 s.

The survey's proof size for zkLLM ("< 10KB") matches neither the abstract's "less than 200 kB" nor
Table 1's 141–188 kB. That number appears to be simply wrong, and it is the clearest evidence in
this collection that survey Table VI cannot be used as a source.
:::

**The headline speedup over ZKML is partly extrapolated.** "Beyond the size of GPT-2 (1.5B
parameters), where zkML results in an out-of-memory (OOM) error, we provide an estimation of the
required proving time." Every comparison point in Figure 4 above that size is an *estimate*, marked
in red, of a baseline that **could not run**. The claim of extending verifiability to an order of
magnitude larger models is real and important, zkML exhausts memory and zkLLM does not, which is
itself the result. The claim of a specific *speedup* at those sizes is a projection against a
system that was never executed there.

**Watch the model names.** zkLLM's "GPT-2" is GPT-2 XL, 1.5B parameters. Every other paper in this
collection means GPT-2 small, 124M. When [[zkgpt]] reports zkLLM's time on "GPT-2," it means the
124M model it re-ran itself. Two papers, one name, an order of magnitude apart.

**The bit width is not stated, and this is the paper that best explains why it matters.** zkLLM's
own framing, that fixed-point methods need large bit widths, which force large fields, is the
cleanest statement of the tradeoff in the literature. It then does not tell you its own bit width.
What it does tell you: the scaling factor for embeddings and parameters is 2^16, each `tlookup`
table holds 2^16 entries, and the field is BLS12-381 at roughly 2^255. So the *field* is the
largest of any system here, which is the cost zkLLM's own introduction warns about, and which
partly explains why a GPU is needed at all.

:::debate Is zkLLM actually exposed to the Fiat–Shamir attack?
`papers.yml` lists `zkllm` in the `affects_in_this_repo` set for the Fiat–Shamir/GKR attack. But
the paper never applies the Fiat–Shamir transform, it describes an interactive protocol with a
semi-honest verifier, and the string "Fiat-Shamir" appears nowhere in the text. On the paper's own
terms, zkLLM sits with [[safetynets]] on the *interactive* side of that line, and the attack cannot
reach it.

The catch is that an interactive, designated-verifier proof is not what anyone wants to deploy, and
the open-source implementation may well compile the interaction away. So the honest status is:
**unresolved, and worth resolving**, either zkLLM is non-interactive in practice (and inherits the
attack surface, and the paper omits its own compilation step), or it is genuinely interactive (and
its "publicly verifiable proof" framing is doing work the protocol does not support). It cannot be
both.
:::
