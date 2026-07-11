---
title: The bridge nobody crosses
section: numerics
order: 20
lede: >-
  The two columns of the 2x2 still cite each other zero times. But they are not two
  islands -- they rest on the same seabed. Three papers are cited by both, and all three
  are MPC numerics primitives. The traffic runs one way, and it does not pass through
  the middle of either literature.
papers: [garg-fp, zklp, archer-ieee, secfloat, prob-truncation, hao-et-al, zkpot-garg, range-arithmetic, deepprove, zkgpt, zkllm, zkpytorch, jolt-atlas, zip, iron, bolt, ciphergpt, nimbus, bootstrapping-fhe]
status: draft
---

The headline finding of this SoK's citation graph has survived every enlargement of the corpus:
**no paper in the verifiability column cites any paper in the privacy column, or the reverse.**
Not once. Two literatures, working the two halves of the same 2x2, on the same models, fighting
the same three operators, publishing at the same venues, with no edge between them.

That is still true. But it was never the whole shape, and the numerics section is what makes the
rest of it visible.

{{ chart:citations }}

## Three nodes are cited by both columns

Rebuild the graph and ask a different question — not "does A cite B", but "is there any node that
*both* columns point at?" There are exactly three, and they are all from the MPC world:

| Shared node | What it is | Cited by (privacy) | Cited by (verifiability) |
|---|---|---|---|
| **SIRNN** (S&P '21) | an OT-based math library for secure inference: digit decomposition, exponential, reciprocal, reciprocal square root | [[iron]], [[bolt]], [[ciphergpt]], [[nimbus]] | [[hao-et-al]], [[zkpot-garg]] |
| **Cheetah** (USENIX '22) | the lean 2PC matmul that the whole private-inference line improves on | [[iron]], [[bolt]], [[ciphergpt]], [[nimbus]], [[bootstrapping-fhe]] | [[hao-et-al]] |
| **[[secfloat]]** (S&P '22) | accurate IEEE-754 floating point under 2PC | [[bolt]] | [[zkpot-garg]], [[zklp]] |

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

{{ table:numerics_primitives }}

## What "crossing" actually looks like

These are not incidental bibliography entries. In the papers that cross, the MPC primitive is
load-bearing.

**[[hao-et-al]] (USENIX Security '24) is a zero-knowledge paper built on an MPC math library.** It
proves softmax, GELU, division and reciprocal square root in ZK — the exact operator set the rest
of this repo is fighting. Its digit-decomposition protocol, its exponential strategy, and its
Goldschmidt iteration all come from SIRNN, and it says so:

:::quote{src="Hao et al." sec="§4, footnote 3 — reference [47] is SIRNN"}
This function is currently explored in secure multi-party computation (MPC) works [47]. In their
protocol, the input x is decomposed into several digits x0 , . . . , xk−1 , and the Msnzb is
computed on each xi of these digits.
:::

It inherits SIRNN's *hyperparameters* too, which is about as deep as borrowing goes:

:::quote{src="Hao et al." sec="§7.2, Results of mathematical functions"}
In our protocols, we set the parameters following prior work [47], i.e., the number of iterations
I = 0 for division and I = 1 for reciprocal square root, and the lookup bitlength m = 5 for
division and m = 6 for reciprocal square root.
:::

**[[zkpot-garg]] (CCS '23) crosses because its proof system *is* an MPC protocol.** It is
MPC-in-the-head, so it needs a fixed-point MPC protocol as its engine, and it takes one — the
Catrina–Saxena secure-truncation construction. The consequence lands in the place this section
cares about most: the numerics substrate *chooses its field*.

:::quote{src="zkPoT (Garg et al.)" sec="§6, Implementation"}
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

:::quote{src="ZKLP (Ernstberger et al.)" sec="§2, Related Work"}
In [25], Rathee et. al construct standard compliant functionalities for 2PC with dedicated
optimizations. While providing better efficiency, they can only achieve partial compliance with
IEEE 754, but subnormal values and NaNs are not considered. Another line of research focuses on
proving floating-point computations using ZKPs.
:::

And it states the asymmetry outright, without seeming to notice it is stating it:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§1, Introduction — reference [25] is SecFloat"}
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
| [[hao-et-al]] | proves *operators*, not models | SIRNN (body, load-bearing) |
| [[zkpot-garg]] | uses MPC as its engine | SecFloat, SIRNN (body) |
| [[zklp]] | *is about* floating point | SecFloat, Archer (body) |
| [[garg-fp]] | *is about* floating point | Archer (body) |

The four that cross are the four that sit at the *edge* of the ZK column: two are about arithmetic
itself, one proves operators rather than models, and one is a ZK system whose engine is literally
an MPC protocol. **Every paper at the centre of the verifiability column — the ones that actually
prove transformers — reaches into nothing.** They rediscover digit decomposition, piecewise
approximation and range-checked truncation from first principles, in a field where a math library
for exactly those operations has existed since 2021.

## Is the one-way traffic real, or an artifact of our corpus?

This is the question the finding lives or dies on, and it deserves a hostile reading. Our graph
holds twenty-one verifiability papers against five privacy papers. A four-to-one imbalance will
manufacture a directional result from pure chance: more ZK papers means more chances for a ZK→MPC
edge, and fewer MPC papers means fewer chances for the reverse. **Counting edges cannot settle
this.**

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
What survives that objection is the recent end: [[bolt]] (S&P '24), [[nimbus]] (NeurIPS '24) and
[[bootstrapping-fhe]] (2026) are contemporaneous with or later than [[zkllm]], [[zkgpt]] and
[[deepprove]], and cite none of them. And [[prob-truncation]] (AAAI '25) is an analysis of
*truncation* — the shared problem, at the shared layer, published late — and it does not contain
the word "zero-knowledge".

**Selection explains part of it.** All five of our privacy papers are private *transformer
inference* systems. That is a genre with no reason to cite a prover. An MPC paper on verifiable or
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
   and reciprocal-square-root in ZK using SIRNN's decomposition. [[nimbus]] approximates exactly
   those functions in 2PC using a distribution-aware fit. Neither has looked at the other's error
   analysis, and they are approximating the same curves on the same models.
2. **Ask whether [[zklp]]'s result changes the 2PC picture too.** ZKLP shows that lookup arguments
   make bit-exact IEEE floats affordable *in a circuit*, and finds fixed point losing to floats on
   its workload. The 2PC line quantizes for the same reason zkML does — fixed point is what the
   primitives support. If the "floats are infeasible" premise is retired on one side of the table,
   somebody should check whether it survives on the other.
:::
