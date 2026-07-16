---
title: zkPyTorch
paper: zkpytorch
status: reviewed
---

## What is new

Of the three modules the paper advertises, one is a real contribution, one is honest re-use, and
one is an engineering note.

**The real one is model-level batching.** A proof does not *compute* the output, it *verifies* a
claimed output. So the autoregressive dependency that forces a plaintext LLM to generate token by
token simply does not bind the prover: all tokens can be proven in a single batched circuit, and
the weight matrix's sum-check bookkeeping table is built once instead of once per token. This is
the same insight [[deepprove]] later turns into its certification algorithm, arriving a year
earlier and stated more abstractly. It is the paper's best idea and it gets one figure.

**The honest re-use** is stated so plainly it deserves quoting, because it is exactly the kind of
thing papers usually bury:

:::quote{src="zkPyTorch" sec="§3.4, Hierarchical ZKP circuit optimizer"}
Therefore, rather than introducing new optimization approaches, ZKPyTorch integrates existing
techniques for primitive operations to enhance efficiency, ensuring compatibility with
state-of-the-art methods while maintaining scalability for large-scale machine learning models.
:::

The convolution protocol is [[zkcnn]]'s. The non-linear lookups are [[zkllm]]'s. zkPyTorch is a
*compiler*, and it says so. Read it as a pipeline paper, ONNX DAG in, Expander circuit out, and
it is a useful one. Read it as a source of per-operator arguments and there is nothing there.

**The engineering note** is the DAG. Prior compilers (ZENO) modelled a network as a
one-dimensional list of layers, which cannot express a residual connection. A DAG can. This is
true and necessary and not very interesting.

## What it actually proves

**Two numbers.** That is the entire empirical content of this paper: a per-image proving time for a
CIFAR-sized VGG-16, and a per-token proving time for Llama-3 8B. Both on a single CPU core. No
proof size, no verification time, no memory figure, no baseline comparison against any other zkML
system, no ablation of the three modules the paper is built from, and no statement of which CPU.

More precisely, what the LLM row proves is undefined, because the amortization window is never
given. The model-level batching optimization *is* the contribution, and its benefit scales with the
number of tokens batched into the circuit. A "seconds per token" figure is therefore meaningless
without the token count it is amortized over, at one token the batching buys nothing, at a hundred
it buys most of the paper. The paper does not say. Neither the sequence length nor the generation
length appears anywhere.

There is also no security analysis. No theorem, no soundness argument, no mention of Fiat–Shamir.
Everything is delegated to Expander, so whatever is true of Expander's GKR-plus-Fiat–Shamir stack
is true here, including the Fiat–Shamir/GKR attack.

## What to distrust

**The 4-bit quantization is not a stated experimental setting.** `papers.yml` records
`quantization.bits: 4`, sourced from Figure 4d. Figure 4d is a *schematic*, a 2×2 toy matrix
illustrating the difference between dynamic, fixed-point and static quantization. The body text
never states the bit width used for VGG-16 or for Llama-3. It says the scheme is "symmetric
per-tensor static quantization," that a calibration phase picks the scale, and that transformers
additionally need "temporary bit-width adjustments", i.e. it is mixed precision, of unstated
width. The 4-bit figure should be treated as an illustration, not a measurement.

This matters more than a footnote, because a 4-bit Llama-3 retaining 99.32% cosine similarity would
be a remarkable result on its own terms, W4A4 quantization of an 8B model is not a solved problem
in the ML literature, and it sits in direct tension with [[deepprove]]'s finding that Gemma 3
collapses to near-zero cosine similarity at 8 bits and needs 12 to survive. Two papers, two
transformer families, opposite conclusions about how far you can push the bit width. Somebody's
number is not what it looks like, and the SoK cannot resolve it because zkPyTorch does not say what
its number *is*.

**Cosine similarity is the weakest accuracy metric in this collection.** [[zkgpt]] and [[zkllm]]
report perplexity deltas against a floating-point baseline. zkPyTorch reports cosine similarity of
the output logits, which can stay above 99% while the argmax flips on a meaningful fraction of
tokens, and argmax is what a user sees. The paper concedes the transformer accuracy is the weaker
half: transformers "have more complex non-linear operations and thus require further optimization."

**The "verifiable model valuation" use case is not evaluated.** §4 presents proving VGG-16's
CIFAR-10 *accuracy* as a headline application. What was measured is per-image inference proving.
Proving accuracy over a dataset is a different objective (see [[zkcnn]], [[zen]]) and no experiment
in this paper touches it.

**Nothing here is dishonest, it is just thin.** There is no straw baseline because there is no
baseline. There is no misleading comparison because there is no comparison. The failure mode of
this paper is not overclaiming; it is that eight pages of architecture are supported by a
two-row table with no error bars, no competitors, and no hardware. Treat every number in
`papers.yml` sourced from it as a single unreplicated data point from an unspecified machine.
