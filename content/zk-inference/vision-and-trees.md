---
title: Vision and trees
section: zk-inference
order: 50
lede: >-
  Before transformers, the field proved convolutional nets and decision trees. Its
  techniques survived into the LLM era. Its assumptions mostly did not -- and it is worth
  knowing which ones broke.
papers: [safetynets, zkcnn, vcnn, zen, mystique, hao-et-al, zkpytorch, zkdt, remainder, pvcnn, deepprove, jolt-atlas, spagkr]
status: draft
---

The LLM systems did not appear from nowhere. Between 2017 and 2021 a small literature
worked out how to prove a neural network at all, on models that fit in a laptop's memory
and had no attention mechanism. Sum-check and GKR, two of the backbones of the
[proof systems page](./proof-systems/), were put to work on neural networks here. So were
the assumptions that the LLM papers spent the next four years breaking.

## The root: SafetyNets

[[safetynets]] (NeurIPS 2017) is the oldest system in this section and the ancestor of the
entire GKR-for-ML lineage: SafetyNets → [[zkcnn]] → [[zkllm]] / [[spagkr]] / [[zkgpt]] /
[[zkpytorch]] → [[deepprove]]. Its move was the one everything since has copied, represent
the network as an arithmetic circuit and prove it with sum-check, rather than shoving it
into a general-purpose SNARK. It composes Thaler's time-optimal interactive proof for
regular arithmetic circuits (a refinement of GKR) over the matmul layers with a *new*
specialized sum-check for the activation layers.

And then it pays for that, in the model class:

:::quote{src="SafetyNets" sec="§2.2, Quadratic Activations"}
The activation functions in SafetyNets must be polynomials with integer coefficients (or,
more precisely, coefficients in the field Fp ). The simplest of these is the element-wise
quadratic activation function whose output is simply the square of its input. Other commonly
used activation functions such as ReLU, sigmoid or softmax activations are precluded, except
in the final output layer.
:::

No ReLU. No sigmoid. No softmax except at the very end. Sum pooling, not max pooling. And a
second-order consequence that is easy to miss: quadratic activations *square the magnitude
at every layer*, so the values compound, and the field has to be large enough to hold them, 
which is why SafetyNets picks its prime by task, and why its scaling factors are bounded
from above by field growth rather than by accuracy.

**Essentially the entire subsequent literature is the story of removing this one
restriction.** Lookup arguments, `tlookup`, `zkAttn`, digit decomposition,
result-as-witness, every one of them exists so that a network can have a real
non-linearity. Read that way, [[hao-et-al]] (which proves individual non-linear operators, 
ReLU, Softmax, GELU, normalization, and never an end-to-end model) is not a niche paper; it
is the field working directly on the thing SafetyNets could not do.

Two more properties make SafetyNets structurally unlike its descendants, and both are the
point of reading it.

It is **genuinely interactive**, live verifier challenges, no Fiat–Shamir, so
the Fiat–Shamir/GKR attack, which hangs over every FS-compiled GKR system in this section,
*cannot reach it*. The vulnerability was introduced by the very step that made the lineage
practical.

And it is **not zero-knowledge.** It buys integrity only; the weights and the input are not
hidden, and the paper says so. Which is why its prover overhead, reported as a percentage
over plain unverified execution rather than in absolute seconds, is not a data point you
can put in the same column as anything else in the table. It is the **floor**: the price of
proving when you drop ZK, drop commitments, and let the model be restricted. No other system
here even reports its cost as a multiple of unverified execution, which is itself the
finding. That distance *is* the cost of everything the field has added since.

## The convolutional generation

The three systems that followed disagreed about which backend to use, and their proof sizes
tell you exactly what they chose.

**[[zkcnn]]** (CCS '21) is the one that mattered. Its result is genuinely surprising and
still underappreciated: a **linear-prover-time sum-check for 2D convolution, asymptotically
faster than computing the convolution directly**, plus a linear-time sum-check for FFT,
beating the conventional $O(N \log N)$. It is the reason GKR won this field. Every GKR-based
LLM system in the table either descends from it or reuses its primitives outright, 
[[zkpytorch]] explicitly imports zkCNN's convolution rather than inventing its own. The
lookup-argument line ([[jolt-atlas]]) is the exception: it descends from Jolt/Lasso, not
from zkCNN.

zkCNN also does something the LLM systems dropped: it **proves accuracy on a public
dataset**, not just a single prediction. It straddles inference and [testing](../zk-testing/),
and the testing objective largely dies with the vision generation.

**[[vcnn]]** used zk-SNARKs with quadratic polynomial programs for convolution. The proving
time we carry for its VGG16 is a survey figure measured on a consumer quad-core i5, against
[[zkcnn]]'s server-class EPYC, and we have not read the vCNN paper, so read the gap in the
table as directional, not as a controlled comparison. It is here to show the trajectory: in
this field, changing the protocol has bought more than tuning the implementation ever did.

**[[zen]]** went the R1CS/Groth16 route, and got what Groth16 gives you: the smallest proof
in the inference table by a wide margin, constant size, at the price of a trusted setup and
a very small model. Its thesis is worth restating because the LLM papers have half-forgotten
it: **quantization choice, not protocol choice, is where the constraint count goes.** But
read its measurement with the caveat in [[zen]]'s deep-dive: the reported saving divides the
*network* constraints only and leaves the in-circuit model commitment out of the ratio, and
on the smallest model the commitment dominates, so the end-to-end saving is far smaller than
the headline. It is still one of the few direct measurements of what quantization actually
buys. [[spagkr]]'s ternary speedup is another, and [[deepprove]], inside the LLM literature,
reports a third: it measures what raising the bit width costs its prover, and finds it close
to nothing. See [Quantization](./quantization/).

**[[mystique]]** (USENIX Sec '21) is the VOLE entry, and what it exchanges is not a proof
object at all: it is interactive, designated-verifier communication, bound to one verifier's
key, and it runs to the gigabyte scale. The figure usually quoted is its *public-model*
configuration, where the weights are revealed; hiding the model costs substantially more (see
[[mystique]]). That is not a bug, it is what a non-succinct interactive protocol costs, and
it bought a fast prover on the largest CNN anyone had proven at the time. It is also the
most-cited paper in the graph: nearly everything in the verifiability column points at it,
from [[deepprove]] and [[zkgpt]] down to the training and numerics clusters, though nothing
in the privacy column does.

## Trees

[[zkdt]] (CCS '20) proves decision trees, and its central insight is one the neural network
papers never got to use: **test samples share nodes.** So rather than proving each sample's
inference path separately, it validates all the inference paths across the whole test set in
one step, with circuit size linear in path length and feature count rather than in tree size
times sample count.

The tree line then had a second life that has no analogue on the neural side. Later work
revisits zkDT through **matrix lookup arguments** (cq+, zkcq+, cq++), encoding the tree as a
committed matrix and proving that the reached leaf's row belongs to it, which removes the
prover's dependence on tree size *entirely*. That is a strictly stronger result than
anything the CNN literature achieved, and it is a reminder that "zkML" is not one problem:
tree inference is a lookup problem, and it was solved by treating it as one.

[[remainder]] (Modulus Labs, 2024) is the tree line's other branch: it scales zkDT's
structured-circuit idea up to **gradient-boosted forests**, proving each tree path by
data-parallel sum-check rather than a matrix-subset argument, and it shipped for a real
on-chain price oracle. It earns a place here for a reason that has nothing to do with trees,
though: the same GKR engine was carried into Worldcoin (which acquired Modulus) and pointed
at iris recognition, where it **inverts the threat model** from hide-the-model (the forest's
weights are IP) to hide-the-input (the user's biometric is the secret, the model is public).
One engine, both ends of the [privacy switch](../../landscape/); read its
[deep-dive](../../papers/remainder/) for why the paper's numbers and the deployed workload are
not the same claim.

[[pvcnn]] sits between the two worlds, homomorphic encryption plus collaborative inference
plus zk-SNARKs, splitting the model into private and public components to prove *testing*
accuracy. Its proof sizes are enormous and its lineage is mostly dead, but it is the one
system here that buys privacy with homomorphic encryption rather than with zero-knowledge
alone, and it tried to buy verifiability and privacy at the same time, the question the
whole [2×2](../) is organised around.

## What the vision generation assumed, and what broke

Five assumptions. Four of them are gone.

| Assumption | Status in the LLM era |
|---|---|
| **One input, one output, one pass.** | **Broken.** Generation is autoregressive; the interesting claim spans many tokens. This is what [What is proven](./what-is-proven/) is about. |
| **Activations are the hard part; matmul is free.** | **Held.** Still true, and still where every technical contribution lands. Softmax/GeLU/LayerNorm replaced ReLU as the enemy. |
| **The architecture is static and known in advance.** | **Held, and load-bearing.** Fixed shapes are why preprocessing works — and, per the Fiat–Shamir/GKR attack, pinning the architecture may also be a *security* requirement, not just an engineering convenience. |
| **Accuracy on a dataset is a thing you prove.** | **Abandoned.** [[zkcnn]] and [[zen]] both prove accuracy on a public dataset. Not one LLM system in the table does. |
| **The model is small enough that the prover's memory is not the constraint.** | **Broken.** Memory is now the binding constraint — it is why [[jolt-atlas]] designs for a laptop's RAM and why [[deepprove]] distributes the prover across machines. |

The abandoned one is the most interesting. The vision generation could prove *"this model
gets this accuracy on this dataset"*, and did. The LLM generation cannot, and does not try.
Yet "the provider swapped in a weaker model", the threat every LLM paper opens with, is
fundamentally an *accuracy* claim, not an execution claim. Proving that some forward pass ran
correctly does not tell you the model was any good; it tells you the arithmetic was right.

:::gap  Verifiable testing did not survive the jump to LLMs
No LLM system in the inference table proves a benchmark score. The [testing](../zk-testing/)
objective, which [[zkcnn]], [[zen]] and [[pvcnn]] all took seriously, has no LLM-scale
member at all. Given that the field's motivating threat is model substitution, and that the
cleanest defence against model substitution is a proof of benchmark performance on a
committed model, this is the largest structurally-shaped hole in the section.
:::
