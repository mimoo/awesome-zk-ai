---
title: Range-Arithmetic
paper: range-arithmetic
status: reviewed
---

## What is new

A third answer to the numerics question, sitting between [[garg-fp]] (relax the float semantics) and
[[zklp]] (keep IEEE, optimise the circuit): **keep fixed point, and prove the rounding
arithmetically.**

The idea lives in Theorem A.1 and it is genuinely clean. To prove that `a'` is the correctly rounded
value of a fixed-point `a` with `s` fractional bits, the prover supplies `a'` together with a
remainder `e`, and shows

$$a \equiv e + 2^{s} \cdot a' \pmod p$$

with two range proofs pinning `e` and `a'` to their intervals. Given a wide enough field, those three
conditions **force** `a'` to be the rounded value, no other assignment satisfies them. Rounding, and
therefore ReLU, reduces to sum-check plus concatenated range proofs, with **no Boolean encoding, no
high-degree polynomial, and no lookup table.**

That last clause is what makes the paper worth reading. Every other system in the proving-inference
table pays for its non-linearities with a table whose size grows exponentially in the bit width, the
cliff [[zkgpt]] documents explicitly and [[jolt-atlas]] spends its entire design budget dodging.
Range-Arithmetic simply declines to build the table. I checked the math; it works.

## What it actually proves

**One forward pass of a four-layer, roughly ten-thousand-parameter fully-connected network on MNIST,
at 6 integer and 8 fractional bits, interactively, with integrity but not privacy.**

This is a [[safetynets]]-shaped system, not a SNARK: the verifier sends live challenges, and
"incorporating privacy-preserving features" is listed in §6 as future work. It is not
zero-knowledge, which also means, like SafetyNets, it sits outside the reach of
the Fiat–Shamir/GKR attack, because there is no Fiat–Shamir transform to attack.

Note the scale. Ten thousand parameters is smaller than SafetyNets' 2017 MNIST network, and roughly
four orders of magnitude below GPT-2. There is no transformer, no softmax, no attention. And there is
no floating-point accuracy baseline, so what the quantization cost in model quality is unknown, the
paper reports the quantized model's MNIST accuracy and nothing to compare it against.

## What to distrust

**The verifier is not succinct, and on the only model evaluated it is nearly as expensive as the
prover.** This is the finding, and the paper walks straight past it. §I names the three metrics for a
verifiable-computing scheme, proof size, *verifier cost*, and prover effort, and says the verifier
must be able to check the result "without re-executing the computation."

:::audit The verifier does two-thirds of the prover's work
From §V-A, the MNIST case study, stated in prose:

> The prover's runtime is approximately **230 milliseconds**, and the verifier's runtime is
> approximately **154 milliseconds**.

The verifier costs about **two-thirds of the prover**, on a network with roughly ten thousand
parameters, a model that plain inference evaluates in microseconds. Verification is therefore
*orders of magnitude more expensive than simply re-running the computation*, which is the one thing
a verifiable-computing scheme exists to avoid, and which §I explicitly names as the goal.

Compare the rest of the corpus: [[zkgpt]] verifies GPT-2 in a fraction of a second, [[deepprove]] in
a few seconds, both on models four orders of magnitude larger. The paper never puts its prover and
verifier figures side by side, and never remarks on their ratio.
:::

This also **corrects `papers.yml`**, which currently records every timing field as `null` with the
note that the paper reports runtimes "only as log-scale plots... with no absolute figure stated
anywhere in prose or in a table." That is not right: §V-A states both figures in prose, and states
the bit width (6 integer, 8 fractional). The figures exist. They are simply not flattering.

**Python, on a laptop.** The implementation is Python, benchmarked on a consumer Asus laptop. Nothing
here is comparable to any other row in this corpus, in either direction, and the paper does not claim
otherwise.

**The bibliography does not survive checking, and that disqualifies the paper as a source for anyone
else's results.** Reference [25] attributes *Jolt Atlas* to Bagad, Domb and Thaler and cites it as
`https://eprint.iacr.org/2026/xxx`, **an unsubstituted placeholder URL**, and the wrong authors
([[jolt-atlas]] is Benno, Centelles, Douchet and Gibran). Reference [24] attributes [[zip]] to
"Y. Zhang et al."; ZIP is Riasi, Wang, Behnia, Vo and Hoang. References [23] ("zkReLU", IEEE TIFS
vol. 20, pp. 1200–1215) and [27] ("ValidCNN", IEEE TIFS vol. 20, pp. 2218–2233) appear fabricated, 
zkReLU is a component of [[zkdl]] rather than a standalone TIFS paper, and [27]'s page range is
*identical* to that of [[pvcnn]], a different paper in the same list. Several entries carry trailing
editorial annotations that read as machine-generated.

The theorem is correct and the technique is real, I checked the math, not the citations. But the
paper's characterisations of other systems (including its comparison figure against [[zip]] and
[[jolt-atlas]]) rest on a reference list containing a placeholder URL and at least two apparently
invented entries, and should not be quoted.

:::gap Nobody has tried this at transformer scale
Range-Arithmetic's pitch is that fixed-point rounding and ReLU are available without lookup tables.
If it holds up, it attacks the dominant cost of every lookup-centric zkML prover head-on, and
[[deepprove]]'s own breakdown says requantization is its single largest line item.

The evaluation is matrix multiplication and a ten-thousand-parameter MLP. Nobody, including the
authors, has run it on a model with a softmax in it. The technique deserves a serious re-implementation
by someone with a working bibliography.
:::
