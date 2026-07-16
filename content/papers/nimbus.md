---
title: Nimbus
paper: nimbus
status: reviewed
---

## What is new

Two ideas, and the second one is the interesting one for this SoK.

**The outer-product matmul encoding.** In 2PC transformer inference the server's weights are known
to the server *in the clear*, only the client's activations are secret. Nimbus exploits this by
restructuring the homomorphic matmul as a sum of outer products rather than inner products, which
lets the server encode weights row-wise into the plaintext slots and produce **compact output
ciphertexts** that cost less to send back. It also moves the weight encoding entirely into an
input-independent setup phase. This is a solid, incremental improvement on the [[iron]] → [[bolt]] →
BumbleBee packing lineage.

**Distribution-aware polynomial approximation** is the idea worth stealing, and it is a genuinely
different way to think about approximating a non-linearity:

:::quote{src="Nimbus" sec="§4, Non-linear layers"}
our insight for enabling simpler polynomials is to assign the approximation budget according to the
input distribution instead of treating all input values with equal importance
:::

Every prior approximation of GELU and Softmax, [[iron]]'s iterative protocols, [[bolt]]'s
high-degree polynomials, [[ciphergpt]]'s uniform splines, minimizes worst-case error over the input
*range*, implicitly assuming the input is uniformly distributed over it. It is not. Nimbus observes
that the GELU inputs at a given transformer layer are sharply peaked (around −3, with positive values
occurring under 10% of the time), and fits the piecewise polynomial by minimizing the
*probability-weighted* L2 error. Intervals with low input probability get a constant or a linear
piece; only the high-density, high-curvature region gets a cubic. Lower degree means fewer
multiplications *and* less sensitivity to fixed-point error, which in turn permits a smaller ring, 
a cascade of savings from one statistical observation.

The security argument is stated and correct: the fitted polynomial is fixed at setup and the client
never sees it, so it leaks nothing about any *particular* input.

## What it actually proves

Nothing, no proof. Privacy against a semi-honest counterparty, on BERT-base at a sequence length of
128, evaluated across eight GLUE tasks under both LAN and WAN settings. The accuracy accounting is
the tightest in this cluster: a small average loss, measured on all eight tasks rather than
[[iron]]'s one.

Note that the sequence length is described as "a mild average number", it is a choice, not a
constraint, and it is the same length [[bolt]] uses, which makes the two comparable. That is more
than can be said for the zkML column, where [[zkgpt]], [[deepprove]] and [[zkllm]] all benchmark at
different contexts and nobody normalizes.

## What to distrust

:::audit The paper reports two different end-to-end speedups
The abstract:

> Compared with the SOTA two-party inference, Nimbus improves the end-to-end performance of
> BERTbase inference by **2.7× ∼ 4.7×** across different network settings.

The contributions list, two pages later:

> Combining all the optimizations, we improve the end-to-end performance of secure two-party
> inference by **2.7× ∼ 5.9×** and reduce the communication cost by 60%.

Same quantity, same paper, two different upper bounds. `papers.yml` and the README currently carry
the abstract's 4.7×, which is the conservative one, but the discrepancy is unexplained and one of
the two numbers is wrong.
:::

**The approximation is calibrated on the training distribution, and its robustness is never tested.**
"We randomly sample sentences from the training dataset until the total token count reaches 512."
Five hundred and twelve tokens of calibration data determine the piecewise polynomial that every
subsequent inference will use for GELU and Softmax. The paper justifies the sample size by observing
that more tokens do not change the *observed* distribution, which establishes that the sample is
representative of the training set, and says nothing about whether a *client's* input will be.

This is the audit surface, and it is the exact mirror of the one this repo already names on the zkML
side. There, an activation outside the calibrated lookup-table range is *unprovable*, a loud
failure. Here, an activation outside the calibrated *distribution* falls in a region the fit
deliberately starved of approximation budget, and the result is simply **wrong, silently**. There is
no range check, no proof, and no signal to the client that anything went off-distribution. A
domain-shifted, adversarial, or out-of-language input degrades accuracy by an amount nobody has
measured, and the semi-honest threat model does not even ask the question.

The parallel is worth stating in full because it generalizes: **both columns of this repo have
replaced a mathematical function with a calibrated approximation of it, and in both columns the
calibration set is an unproven, unauthenticated input chosen by the party who benefits from getting
it wrong.** [[nimbus]] fits its polynomial to the training data; [[deepprove]] and [[zkpytorch]] pick
their quantization scales from a calibration set; [[jolt-atlas]] tunes τ per model. None of these
choices is verified by anything.

**The GELU input distribution is shown for one layer.** Figure 4 plots the distributions "at the 4th
encoder." A 12-layer BERT has twelve of them, and the whole premise of the method is that the
distribution has structure worth exploiting. Whether the fit is per-layer or global, and if global,
how much it costs at the layers whose distribution differs, is not addressed.

**Everything else here is clean, and that is worth saying.** Nimbus states its threat model, states
its sequence length, states its accuracy loss on eight datasets, reports both LAN and WAN, and does
not change the model to get its numbers, no fine-tuning, no token dropping, no architectural
substitution. Against [[bolt]] and [[bootstrapping-fhe]], which both buy part of their headline by
modifying the network, Nimbus's improvement is *entirely* cryptographic and statistical. The 2.7–4.7×
(or 5.9×) is a real protocol result on an unmodified model. That is rarer in this cluster than it
should be.
