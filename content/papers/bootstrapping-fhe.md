---
title: Bootstrapping is All You Need
paper: bootstrapping-fhe
status: reviewed
---

## What is new

This is the one FHE paper in the privacy cluster, and the setting is genuinely different from the
2PC systems around it. The client encrypts under CKKS, the server evaluates the whole transformer on
ciphertext, and returns a ciphertext. **No interaction, no rounds, no client presence during
inference.** The authors call it NISTI, non-interactive secure transformer inference, and it is
the only entry in either column of this repo where the client can go offline.

Bootstrapping dominates that setting, so the paper's thesis is: stop treating bootstrapping as
overhead and start **fusing useful work into it**. Three pieces:

**A trigonometric minimax approximation for functional bootstrapping.** The prior state of the art
approximates the target function with a Fourier series, which is optimal under L2 but does not
minimize worst-case error, and worst-case error is what you care about when a single bad activation
can flip a classification. The classical Remez algorithm minimizes L∞ but only over a *polynomial*
basis, and functional bootstrapping needs a *trigonometric* one. The paper proves a trigonometric
minimax approximation exists and derives a trigonometric Remez algorithm to compute it. This is the
real contribution and it is a proper theorem.

**Functional S2C.** Bootstrapping already performs a slot-to-coefficient transform, which is a linear
map. A transformer's linear layers are also linear maps. So *fold the weight matrix into the S2C
transform* and the linear layers cost nothing separately. This is a lovely observation.

**Batch-S2C, interleaved packing, lazy key switching, hoisting**, engineering.

## What it actually proves

Nothing, no proof, and no integrity guarantee of any kind. What it computes, privately and
non-interactively, is **BERT-DyT**, not BERT.

:::quote{src="Bootstrapping is All You Need" sec="§6, Evaluation"}
For our framework, we replace LayerNorm with Dynamic Tanh (DyT). We distill BERT-DyT from the
original BERT, treating the latter as the teacher model.
:::

That substitution is not incidental. It is where most of the headline speedup comes from.

The other thing to be precise about: **both headline numbers are amortized over a batch of 256
inputs.** The runtime breakdown table says so in its caption; the communication figure says so in the
abstract. No single-query (batch-1) latency or bandwidth is reported anywhere. The README currently
sets this system's tiny communication figure against the 2PC systems' hundreds of gigabytes as
"the whole FHE trade", but those 2PC figures are *per inference*, and this one is per inference
*amortized over 256*. FHE still wins the communication axis, and by a lot, but not by the margin
that comparison implies, and a user sending one prompt cannot amortize over anything.

## What to distrust

**The headline speedup is largely a model substitution the baseline does not get, and the paper's own
table caption admits it.**

:::audit The caption gives it away, and the GELU row is never mentioned
Table 4's caption reads, in full: *"Runtime breakdown amortized over 256 inputs. **MOAI still uses
LayerNorm instead of Dynamic Tanh.**"*

So the comparison is between two different networks. Look at what that buys, in the paper's own
numbers:

| Operation | Ours | MOAI (baseline) |
|---|---|---|
| `X = α · tanh(β · (E · W₂ + b₂)) + γ` — *the DyT layer* | 76.4 s | **217.4 s** |
| `E = GELU(D · W₁ + b₁)` | **141.1 s** | 43.4 s |
| **Total** | **349.5 s** | **662.3 s** |

The single row corresponding to the operation they *replaced in the model* accounts for ~141 s of the
~313 s total saving, roughly 45% of the entire speedup, from the one change the baseline was not
allowed to make.

And in the same table, **their GELU is over three times slower than the baseline's**. That regression
is printed and never discussed anywhere in the text.
:::

The paper's three cryptographic contributions may well be sound and useful. But the experiment as
constructed cannot tell you what they are worth, because it never runs the new bootstrapping
machinery on a LayerNorm network, the one ablation that would separate the cryptography from the
architecture surgery. This is [[bolt]]'s word-elimination problem in a different key: a real
cryptographic contribution, and a headline number that quietly bundles a model change the baseline
never receives.

**"Virtually no additional accuracy loss" is not what the accuracy table shows.** The text says the
framework "introduces virtually no additional accuracy loss, achieving nearly identical accuracy to
BERT-DyT across all three datasets." The encrypted evaluation loses roughly a point on two GLUE tasks
and nearly two points on the third (RTE). That is the **largest accuracy loss in the privacy
cluster**, [[nimbus]] reports a fraction of a percent, [[iron]] under a third of a percent, [[bolt]]
around one percent, and it is described as negligible.

**The distilled model reports accuracy identical to its teacher, to two decimal places, on all three
datasets.** Across test sets of 277, 872 and 408 examples, replacing LayerNorm with Dynamic Tanh and
distilling from scratch is reported as changing the number of correct predictions by exactly zero,
three times. That is possible. It is also the kind of coincidence that deserves a sentence of
explanation, and gets none.

**Only three GLUE tasks**, all classification, all short-sequence. [[nimbus]] reports eight.

**Where the paper is strong:** the trigonometric minimax result is a genuine theorem with a real
motivation (L∞ is the right norm for this application and the prior work used the wrong one), the
functional-S2C insight is elegant, and the non-interactive setting is a materially different product
from everything else in this repo. If someone re-ran this on a LayerNorm network and the speedup
survived, it would be the most interesting paper in the privacy cluster. As published, that
experiment does not exist.
