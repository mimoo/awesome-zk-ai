---
title: SIRNN
paper: sirnn
status: reviewed
---

For as long as this SoK has existed, its headline finding has rested on three papers: *the only three
nodes cited by both columns are SIRNN, Cheetah and SecFloat, and all three are MPC numerics.*

We held SecFloat. **SIRNN and [[cheetah]] were names in a graph.** We had never read either. This
page is the overdue half of that.

## What it is

Specialized 2PC protocols for the math functions a network actually needs, exponential, sigmoid,
tanh, reciprocal, and reciprocal square root, all built on one paradigm:

> Use a **lookup table** for a good initial approximation, then refine with **Goldschmidt's
> iterations.**

Supporting that are two ideas that carry the whole paper. **Digit decomposition** splits an $\ell$-bit
value into $\ell/d$ digits so you can index several small tables instead of one enormous one, about
5× cheaper than a garbled circuit. And **mixed bit-widths**: do not force every variable to 64 bits
just because one operation needs it.

Now read that paragraph again, and then read the zkML papers.

Digit decomposition into small lookup tables, refined by an iterative approximation, with bit-widths
chosen per operator. That is [[hao-et-al]]'s exponential protocol and its reciprocal-square-root
protocol, it cites SIRNN **five times in its body** and inherits its iteration counts and lookup
bit-lengths outright. It is also, in different vocabulary, what [[deepprove]] and [[zkgpt]]
rediscovered from first principles four years later, and what [[bionetta]] derived from scratch in an
appendix in December 2025.

## The sentence that should have been in our numerics page three years ago

:::quote{src="SIRNN" sec="§II, Motivation"}
the requirement of a high bitwidth even in one operation, coupled with the requirement of uniform
bitwidths, raises the bitwidths of all variables and operations throughout an inference task,
resulting in a communication blowup
:::

Replace *communication blowup* with *field size* and you have [[zkpytorch]]'s causal chain, the one
[the numerics page](/numerics/) opens with, stated in 2021, in MPC vocabulary, by people who then
went and solved it.

## The fact that settles an argument

[The numerics page](/numerics/) argues that ZK cannot borrow MPC's cheap **probabilistic
truncation**, because a failure that is rare on random data is not rare at all when the prover
chooses the input, and it closes by insisting that probabilistic truncation is *the exception that
has been mistaken for the rule.*

SIRNN is the primary source for that, and we were making the argument without it.

**SIRNN's truncation is exact.** All four flavours, logical shift, arithmetic shift,
truncate-and-reduce, and C-style division by a power of two, compute the wrap and borrow terms
*exactly*. There is no "fails with small probability" anywhere in the paper. And the exact one is
**cheap**: truncate-and-reduce costs about $\lambda(s+1)$ bits, roughly **4.5× less than a garbled
circuit**.

So the MPC world did not merely have the cheap-but-probabilistic truncation that ZK must refuse. It
also had the exact one, and the exact one is the one that is fast. That is precisely the technique the
ZK papers borrowed, and precisely the reason the borrowing was possible at all.

## What to distrust

Very little, which is unusual for this collection. The precision claims are not asserted, they are
**formally verified**: exhaustively tested at bit-width 16 against GNU MPFR, reporting worst-case ULP
error (exponential 3, sigmoid 3, tanh 4, reciprocal square root 4). The paper's own benchmark is that
"Intel's SVML also provides math implementations with 4 ULP error."

The one thing to carry forward is its foil, because it is the sharpest measurement in the corpus of
what cheap non-linearities cost a model. **SecureML and ABY2.0's three-piece linear spline sigmoid
carries 1547 ULPs of error, and drops Google-30 keyword-spotting accuracy from 84.4% to 60.95%.**

Approximating the activation is how you destroy the network. Both columns keep learning this
separately.
