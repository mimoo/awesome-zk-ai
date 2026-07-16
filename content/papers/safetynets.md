---
title: SafetyNets
paper: safetynets
status: reviewed
---

## What is new

In 2017: the entire idea. Represent the network as an arithmetic circuit over 𝔽ₚ and prove it with
sum-check instead of a general-purpose SNARK. Everything downstream, [[zkcnn]], [[zkllm]],
[[zkgpt]], [[zkpytorch]], [[deepprove]], is a descendant of that move.

The technical contribution is narrower than the idea. Thaler's time-optimal interactive proof
already handled matrix multiplication; SafetyNets adds a **specialized sum-check for the quadratic
activation layer** and, crucially, *composes* the two so that the assertion about layer `i`'s output
reduces directly to an assertion about layer `i−1`'s input, all the way back to the network's
input. The naive alternative, verify each layer independently against a committed intermediate, 
would have meant sending every intermediate tensor. Composition is what makes the bandwidth
negligible, and the paper is explicit that this is the point.

## What it actually proves

**A batch of forward passes of a quadratic-activation network, against weights the verifier already
holds, interactively, with a soundness error the paper states as 2⁻³⁰.**

Every clause here is worth pausing on, because this paper is read today as a *floor* on proving
cost, and three of its four assumptions are what buy that floor.

- **Not zero-knowledge**, and the paper says so, future work. Fine, and honestly stated.
- **The verifier holds the weights.** This is the one that dissolves the paper's own motivation.
  The assertion about layer `i`'s weight matrix "is checked by the verifier locally since the
  weights are known to both the prover and verifier." So the client must possess the model. That
  answers the *lazy cloud* threat (the server saved compute by running a smaller net) and cannot
  answer the *proprietary model* threat, which is the threat every descendant of this paper exists
  to address.
- **The verifier is therefore not succinct in the model.** Checking the weight assertions costs
  work proportional to the weight matrices. That is why the verifier's advantage over local
  execution is a modest factor rather than the millisecond-scale verification of a modern SNARK,
  and why the advantage *grows with batch size*, it is an amortization result, not a succinctness
  result.
- **Interactive.** No Fiat–Shamir, therefore the Fiat–Shamir/GKR attack cannot reach it. It is
  correctly excluded from that paper's target list, and the reason is the point: the vulnerability
  was introduced by the very step that made the lineage practical.
- **Quadratic activations only.** No ReLU, no sigmoid, no softmax except at the output; sum pooling,
  not max pooling. And the constraint is worse than it looks, squaring at every layer compounds
  magnitude, so the field must be large enough to hold the growth, which is what rules out the
  larger scaling factors in Table 1 and forces a 127-bit prime for TIMIT.

## What to distrust

**The +5% prover overhead is measured against the wrong baseline, and this changes what the number
means.** Figure 3's caption is precise about it: the baseline is "the arithmetic circuit
representation of FcNN-Quad-3." The comparison is against executing the network *in modular
arithmetic over a 61- or 127-bit Mersenne prime*, not against floating-point inference. Field
arithmetic over a 127-bit prime is itself far slower than the float execution a real deployment
would perform. So "+5% over unverified execution" means +5% over an already heavily penalized
execution, and the true overhead over a *normal* inference is unstated and much larger.

This is the single most important correction to make, because the README currently reads that +5%
as "the most useful floor in the file." It is a floor on *proving overhead relative to field
execution*, which is a real and interesting quantity, but it is not a floor on the cost of
verifiable inference, and it is not comparable to any other row in the table.

:::audit The soundness error is 2⁻³⁰, not 2⁻¹³⁰
`papers.yml` records `soundness_error: 2^-130`. The paper says otherwise, twice:

> In practice, with p = 2⁶¹ − 1 the soundness error < 1/2³⁰ for practical network parameters and
> batch sizes. *(§3.3)*

> In all settings, the soundness error ϵ, i.e., the chance that the verifier fails to detect
> incorrect computations by the server is less than 1/2³⁰, a negligible value. *(§4.3)*

The superscript is lost by `pdftotext`, which renders `1/2³⁰` as the string `2130`, almost certainly
where the 2⁻¹³⁰ came from. The paper's own Lemma 3.1 confirms 2⁻³⁰ is the right order: with
ε = 3b·Σnᵢ/p and p = 2⁶¹−1, no configuration can reach 2⁻¹³⁰, it is below `1/p`, so it is not merely
wrong, it is *unreachable* for the prime SafetyNets uses.

This is not pedantry. 2⁻³⁰ is a statistical soundness a modern reviewer would reject out of hand;
2⁻¹⁰⁰ is the norm elsewhere in this repo. SafetyNets gets away with it because it is *interactive*, 
the verifier can simply repeat, but the number as printed is a weak guarantee, and the repo is
currently crediting it with a strong one.
:::

**The abstract's TIMIT accuracy does not match the body.** The abstract claims 75.22% accuracy on
TIMIT; §4.2 reports a test error of 25.7%, i.e. 74.3%. Nobody explains the gap.

**The CryptoNets comparison, and the conclusion drawn from it.** The paper compares its verifier's
runtime against CryptoNets' *client encryption* time and concludes: "From this rough comparison, it
appears that integrity is a more practically achievable security goal than privacy." It concedes
one sentence earlier that "a direct comparison is not entirely meaningful," and then draws the
conclusion anyway. Read from 2026, alongside [[iron]], [[bolt]], [[nimbus]] and
[[bootstrapping-fhe]], the sentence has aged into something worth arguing with, private inference
on a real transformer is now measured in hundreds of gigabytes, but so is a DeepProve proof
measured in tens of megabytes and a ZIP verification in tens of minutes. Neither column is
"practically achievable" yet. The 2017 verdict was premature in both directions.

**Table 1 is non-monotone in accuracy**, in the same quiet way [[deepprove]]'s Table 4 is:
increasing the weight scaling factor at fixed input scale sometimes *increases* validation error.
Small, unremarked, and a reminder that quantization curves in this literature are noisy and
under-sampled.
