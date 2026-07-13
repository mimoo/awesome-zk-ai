---
title: The bridge nobody crosses
section: numerics
order: 20
lede: >-
  The two columns of the 2x2 still cite each other zero times. But they are not two
  islands -- they rest on the same seabed. Three papers are cited by both, and all three
  are MPC numerics primitives. The traffic runs one way, and it does not pass through
  the middle of either literature.
papers: [garg-fp, zklp, archer-ieee, secfloat, prob-truncation, hao-et-al, zkpot-garg, deepprove, zkgpt, zkllm, zkpytorch, jolt-atlas, zip, bionetta, iron, bolt, ciphergpt, nimbus, bootstrapping-fhe]
status: reviewed
---

For most of this SoK's life the headline finding was stated as an absolute: **no paper in the
verifiability column cites any paper in the privacy column, or the reverse. Not once.**

**On 2026-07-13 that stopped being true, and the way it stopped being true is better than the
finding it replaced.**

We finally read the two papers the finding had always rested on — [[sirnn]] and [[cheetah]] — which
had been sitting in the graph as `external:` stubs, unread, for the entire life of the project. (That
is its own indictment and it is dealt with below.) Promoting them to real papers created exactly
**two** crossing edges, and the validator's tripwire fired, as it was built to.

Neither edge is a cryptographic citation. Both are about **numerics** — which is what this page has
been arguing all along, and now it is arguing it with evidence instead of with an absence.

| Crossing edge | Direction | What it actually is |
|---|---|---|
| [[hao-et-al]] → [[cheetah]] | verify → privacy | **Bibliography only.** Cheetah is reference [30] and appears **zero** times in hao-et-al's body. (Contrast [[sirnn]], reference [47]: **five** body citations, load-bearing.) And hao-et-al is the one verifiability paper that proves *operators* rather than models — already flagged here as an edge case. |
| [[delphi]] → [[safetynets]] | **privacy → verify** | The interesting one. A privacy paper citing a verifiability paper — **twice, in the body** — and **not for verifiability.** It cites SafetyNets as prior evidence about whether *quadratic activations train well*. Delphi's body contains **zero** occurrences of "verifiable", "integrity", "zero-knowledge" or "proof of correctness". |

Read that second row again. **Delphi does not know it is citing a verifiability paper.** It is citing
an ML result about activation functions, and the fact that the result happens to live inside a zkML
paper is invisible to it.

So the finding does not die. It sharpens, into something you can actually defend:

> **The two literatures do not read each other as cryptography.** Where they touch — and they do
> touch — they touch at the **numerics**, and they touch *without noticing*.

{{ chart:citations }}

## Three nodes are cited by both columns

Rebuild the graph and ask a different question — not "does A cite B", but "is there any node that
*both* columns point at?" There are exactly three, and they are all from the MPC world:

| Shared node | What it is | Cited by (privacy) | Cited by (verifiability) |
|---|---|---|---|
| **[[sirnn]]** (S&P '21) | an OT-based math library for secure inference: digit decomposition, exponential, reciprocal, reciprocal square root | [[iron]], [[bolt]], [[ciphergpt]], [[nimbus]] | [[hao-et-al]], [[zkpot-garg]] |
| **[[cheetah]]** (USENIX '22) | the lean 2PC matmul that the whole private-inference line improves on | [[iron]], [[bolt]], [[ciphergpt]], [[nimbus]], [[bootstrapping-fhe]] | [[hao-et-al]] |
| **[[secfloat]]** (S&P '22) | accurate IEEE-754 floating point under 2PC | [[bolt]] | [[zkpot-garg]], [[zklp]] |

:::gap  We argued from three papers for a year and had read one of them
Until July 2026, [[sirnn]] and [[cheetah]] were `external:` nodes — names in a YAML file, with no
PDF, no entry, and no page. The single most-quoted claim in this repo rested on three papers, and we
had read exactly one of them ([[secfloat]]).

It is worth being blunt about what that means. The finding turned out to be *right*, and reading the
papers made it sharper rather than weaker. But it was right by luck, and the `external:` mechanism —
which exists so you can name a building block without studying it — had quietly become a way of
holding load-bearing evidence at arm's length. **A node your headline depends on is not a building
block.** It is a paper you owe a reading.
:::

Add the fourth-order case and the picture completes: [[garg-fp]] — a *zero-knowledge* paper, CCS
'22 — takes its floating-point cost baseline from [[archer-ieee]], which is an *MPC* paper, and
uses it in the body, not the bibliography. [[zklp]] does the same thing, from the same source.

So the real shape is not "two communities that never talk." It is:

> **They never read each other's systems. They both reach down to the same numerics substrate.
> And the reaching is one-directional.**

Both columns have to turn a real number into a finite-field element, multiply, and then squeeze a
wide accumulator back down. Both have to do it without a division. The MPC world solved a large
part of that problem first — [[secfloat]], SIRNN and the Catrina–Saxena fixed-point line go back to
2010 — and the ZK world has been quietly drawing on it while ignoring everything the same authors
built on top.

{{ papers:numerics_primitives }}

## What "crossing" actually looks like

These are not incidental bibliography entries. In the papers that cross, the MPC primitive is
load-bearing.

**[[hao-et-al]] (USENIX Security '24) is a zero-knowledge paper built on an MPC math library.** It
proves softmax, GELU, division and reciprocal square root in ZK — the exact operator set the rest
of this repo is fighting. Its exponential protocol is inspired by SIRNN's digit-decomposition idea,
its reciprocal-square-root initial approximation cites SIRNN, and it inherits SIRNN's
hyperparameters — but the digit-decomposition building block is its own, and it explicitly rejects
SIRNN's Msnzb construction as too costly before re-deriving one. (The Goldschmidt iteration it uses
is attributed to Goldschmidt's 1964 thesis and to the MPC line generally, not to SIRNN.) The
borrowing is real but selective, and the paper says so:

:::quote{src="Hao et al." sec="§2.2, Novel table lookup-based protocols — reference [47] is SIRNN"}
This function is currently explored in secure multi-party computation (MPC) works [47]. In their
protocol, the input x is decomposed into several digits x0 , . . . , xk−1 , and the Msnzb is
computed on each xi of these digits. Finally, the output corresponds to y = Msnzb(xi ) + i · d if xi
≠ 0 and x j > 0 for all j > i, where d is the bitlength of each digit. Although this method can be
directly migrated to the ZK-based evaluation, utilizing our digital decomposition and table lookup
protocols, the cost is significantly high due to the requirement of multiple Msnzb, comparison, and
multiplication operations.
:::

The *hyperparameter* inheritance is the most literal part of it:

:::quote{src="Hao et al." sec="§7.2, Results of mathematical functions"}
In our protocols, we set the parameters following prior work [47], i.e., the number of iterations
I = 0 for division and I = 1 for reciprocal square root, and the lookup bitlength m = 5 for
division and m = 6 for reciprocal square root.
:::

**[[zkpot-garg]] (CCS '23) crosses because its proof system *is* an MPC protocol.** It is
MPC-in-the-head, so it needs a fixed-point MPC protocol as its engine, and it takes one — the
Catrina–Saxena secure-truncation construction. The consequence lands in the place this section
cares about most: the numerics substrate *chooses its field*.

:::quote{src="zkPoT (Garg et al.)" sec="§7, Implementation and Evaluation"}
All arithmetic is implemented over a 128-bit ($p = 2^{128} − 45 * 2^{40} + 1$) prime field. The
larger field size is required by the secure truncation protocol for fixed-point arithmetic (see
Section 2.4). We expect that finding a way to avoid this and instead using a 64-bit field would
further speed up the protocol and reduce proof size.
:::

That is the same causal chain the index page draws for zkML — *numeric format → field size → prover
cost* — arriving in a ZK paper by way of an MPC truncation protocol. And the bridge here is not
even a citation. It is a person:

:::quote{src="zkPoT (Garg et al.)" sec="Acknowledgements"}
We thank Deevashwer Rathee for useful discussions on fixed point arithmetic.
:::

Deevashwer Rathee is the first author of both SIRNN and [[secfloat]]. The one place the two
literatures genuinely touch, they touch through the acknowledgements section.

**[[zklp]] is the only paper in this repo that reads *both* float literatures on purpose.** Its
related work walks the MPC line — Aliasgari, Kamm, [[archer-ieee]], Pullonen–Siim, [[secfloat]] —
and then turns to the ZK one, treating them as two lines on one problem:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§6, Related Works — Floating-Point Secure Computing"}
In [25], Rathee et. al construct standard compliant functionalities for 2PC with dedicated
optimizations. While providing better efficiency, they can only achieve partial compliance with
IEEE 754, but subnormal values and NaNs are not considered. Another line of research focuses on
proving floating-point computations using ZKPs.
:::

And it states the asymmetry outright, without seeming to notice it is stating it:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§4, Zero Knowledge Location Privacy — Representing the Transformation as Constraints; reference [25] is SecFloat"}
Efficient algorithms for emulating accurate trigonometric functions are known for
Two-Party-Computation [25]. However, we are not aware of any optimizations that lead to accurate
and efficient in-circuit trigonometric approximations for SNARKs.
:::

*MPC has this; SNARKs do not.* That sentence is the entire finding of this page, written by
someone who was looking at both shelves at once — and it appears in a paper about **location
privacy**, which is why nobody in zkML has read it.

## The bridge does not pass through the middle of either column

Here is the part that matters most, and it corrects the tempting version of this story.

It is *not* true that "the ZK side reaches into the MPC toolbox." Four papers do. None of them is
a mainstream zkML prover. I checked every flagship system in the verifiability column for any
mention — body or bibliography — of the three shared nodes:

| Paper | What it is | Mentions Cheetah / SIRNN / SecFloat |
|---|---|---|
| [[deepprove]] | GPT-2 / Gemma prover | **none** |
| [[zkgpt]] | GPT-2 prover | **none** |
| [[zkllm]] | LLaMA-2 prover | **none** |
| [[zkpytorch]] | compiler, Llama-3 | **none** |
| [[jolt-atlas]] | ONNX prover | **none** |
| [[zip]] | high-precision inference | **none** |
| [[bionetta]] | client-side CNN prover | **none** |
| [[hao-et-al]] | proves *operators*, not models | SIRNN (body, load-bearing) |
| [[zkpot-garg]] | uses MPC as its engine | SecFloat, SIRNN (body) |
| [[zklp]] | *is about* floating point | SecFloat, Archer (body) |
| [[garg-fp]] | *is about* floating point | Archer (body) |

The four that cross are the four that sit at the *edge* of the ZK column: two are about arithmetic
itself, one proves operators rather than models, and one is a ZK system whose engine is literally
an MPC protocol. **Every paper at the centre of the verifiability column reaches into nothing.**
They rediscover digit decomposition, piecewise approximation and range-checked truncation from
first principles, in a field where a math library for exactly those operations has existed since
2021.

[[bionetta]] is the newest entry in that table and the cleanest demonstration of the pattern,
because it does not merely fail to cite the numerics literature — **it redoes it.** Appendix C of a
December 2025 technical report derives, from scratch, the error bound for multiplying two
fixed-point numbers:

$$\varepsilon_\rho := \left|D_{2\rho}\big(\hat{x}\hat{y}\big) - xy\right| \;\le\; 2^{-\rho}\beta + 2^{-2\rho}$$

That is a foundational result in the [[secfloat]] / [[prob-truncation]] line. The paper contains
zero occurrences of "MPC", "homomorphic", "SIRNN", "Cheetah" or "SecFloat". Four years after a
library shipped that does exactly this, a team building a **deployed** system proved it again by
hand — and, on the evidence of the bibliography, did not know there was anything to look up.

## Is the one-way traffic real, or an artifact of our corpus?

This is the question the finding lives or dies on, and it deserves a hostile reading. Our graph
holds several times more verifiability papers than privacy papers (the live counts are on the
citation-graph page). An imbalance that large will manufacture a directional result from pure
chance: more ZK papers means more chances for a ZK→MPC edge, and fewer MPC papers means fewer
chances for the reverse. **Counting edges cannot settle this.**

So I did not count edges. I ran a test that is immune to corpus size, because it is a property of
each document on its own: **does this paper contain the word "zero-knowledge" — or "SNARK", or
"GKR", or "sum-check" — anywhere at all, body or bibliography?**

| MPC-side paper | Any ZK vocabulary, anywhere |
|---|---|
| [[iron]] | **none** |
| [[nimbus]] | **none** |
| [[bootstrapping-fhe]] | **none** |
| [[secfloat]] | **none** |
| [[prob-truncation]] | **none** |
| [[archer-ieee]] | **none** |
| [[ciphergpt]] | twice, in passing |
| [[bolt]] | once ("zero-knowledge proofs for HE", about MUSE) |

Six of the eight MPC-side PDFs we hold never use the word. Not in the related work, not in the
references, not once. That is not something a small sample can fake — it is eight independent
documents, and six of them are silent. The asymmetry is real *for these papers*.

:::gap  What the asymmetry does not establish
Three caveats, and I would not want the finding cited without them.

**Chronology explains part of it.** SIRNN (2021), [[archer-ieee]] (2021), Cheetah (2022) and
[[secfloat]] (2022) mostly predate the zkML transformer systems. [[iron]] (2022) *could not* have
cited [[deepprove]] (2026). A "recent ZK cites older MPC" pattern is partly just the arrow of time.
What survives that objection is the recent end: [[bolt]] (S&P '24) and [[nimbus]] (NeurIPS '24) are
contemporaneous with [[zkllm]] (CCS '24) and do not cite it, and [[bootstrapping-fhe]] (2026) is
contemporaneous with [[deepprove]] and cites nothing in the zkML line. And [[prob-truncation]]
(AAAI '25) is an analysis of *truncation* — the shared problem, at the shared layer, published
late — and it does not contain the word "zero-knowledge".

**Selection explains part of it.** All five privacy papers that appear in the graph are private
*transformer inference* systems — we hold no PDF for the private-training entries, so they
contribute no edges. That is a genre with no reason to cite a prover. An MPC paper on verifiable or
maliciously-secure computation would plausibly cite ZK work heavily, and we hold none. The honest
scope of the claim is therefore narrow: *private-transformer-inference papers do not read zkML*.
It is **not** "MPC does not read ZK", and we have no evidence for the broader statement.

**The proxy is coarse.** An edge in this graph means "A's text mentions B" — body or reference
list. Two of the edges the graph draws turn out to be bibliography-only on inspection
([[hao-et-al]] lists Cheetah but never uses it), and one real edge is *missing* — [[zklp]] cites
[[archer-ieee]] as its reference [21], in the body, and the extractor does not catch it. Every
edge this page leans on has been checked by hand against the PDF; the graph itself has not.
:::

## Why it matters that they share a substrate and not a literature

If the two columns were solving unrelated problems, the disconnection would be unremarkable. They
are not. Strip away the cryptography and both are doing the same thing: representing a real number
in a domain that has no reals, multiplying, and then rescaling a wide accumulator back down without
a division. Both answer it with *piecewise approximation selected by a lookup on the high bits*.
Both discover that the cost is not the arithmetic but the rounding. Both find that the calibrated
range is where the soundness or the accuracy actually lives.

And where a technique genuinely *cannot* transfer, the reason is the threat model, not ignorance —
which is worth stating precisely, because it is the one place the disconnection is justified.
MPC's probabilistic truncation is cheap because it accepts a small per-operation failure
probability, and when it fails it fails with a large error. On a random input that is an accuracy
cost you can bound. In ZK the prover chooses the input, so a rare failure is not rare at all, and
an accuracy cost becomes a **soundness** hole. [[prob-truncation]] is the analysis of that failure
mode; it is an MPC paper; and no ZK paper cites it.

That is the correct summary of this whole section. **The two columns can share the numerics, and
they do — but they cannot share the *guarantees* built on top of it, and they have never sat down
together to work out which is which.** Nobody is doing that work. The shared seabed is
uninhabited.

:::debate  What would settle it
Two experiments, neither expensive:

1. **Point [[hao-et-al]] at the private-inference operators.** It proves exponential, reciprocal
   and reciprocal-square-root in ZK using digit decomposition and table lookups. [[nimbus]]
   approximates exactly
   those functions in 2PC using a distribution-aware fit. Neither has looked at the other's error
   analysis, and they are approximating the same curves on the same models.
2. **Ask whether [[zklp]]'s result changes the 2PC picture too.** ZKLP shows that lookup arguments
   make bit-exact IEEE floats affordable *in a circuit*, and finds fixed point losing to floats on
   its workload. The 2PC line quantizes for the same reason zkML does — fixed point is what the
   primitives support. If the "floats are infeasible" premise is retired on one side of the table,
   somebody should check whether it survives on the other.
:::
