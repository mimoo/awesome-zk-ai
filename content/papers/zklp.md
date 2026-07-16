---
title: ZKLP, Accurate Floating-Point SNARKs
paper: zklp
status: reviewed
---

## What is new

Ignore the title. The location-privacy protocol is the paper's stated contribution and the
floating-point circuits are framed as the means to it, but for this SoK the ranking is inverted:
**this is the first set of SNARK circuits fully compliant with IEEE 754, and it is the single
strongest refutation of the premise the entire zkML literature rests on.**

The premise being that native floating point is infeasible in a circuit. Every quantization decision
catalogued in [the inference section](/zk-inference/quantization/) is downstream of it, and it is
sourced, when it is sourced at all, to the cost of *naively* transliterating a software float
routine into gates.

ZKLP's move is to stop transliterating. The parts of IEEE-754 that are hostile to a circuit are
hostile for one reason: they are **integer operations in $\mathbb{Z}_{2^k}$**, comparison, shifting,
normalization, being emulated inside $\mathbb{F}_p$. So push them into **lookups** (LogUp, in gnark)
rather than gates, and share the tables across every operation in the circuit. The cost then
*amortizes*: the more float operations you prove, the cheaper each one gets.

The second contribution, and the one that makes the first tractable, is **nondeterministic
programming used systematically**. The prover computes the hard part outside the circuit and hands
it in as an untrusted hint; the circuit only *verifies* it. Square root is the clean example: rather
than running Newton's method in-circuit, the prover supplies $n$, and the circuit enforces
$n^2 \le (m_\alpha \ll (M{+}4{+}b)) < (n+1)^2$ with two range checks, which pins $n$ as *the* integer
square root and nothing else. Division, normalization and the exponent's least-significant bit are
handled the same way.

This is worth dwelling on, because it is the same pattern as the *result-as-witness* paradigm that
every zkML system uses for its non-linearities, and it is the pattern I flagged as the highest-value
audit surface in this SoK. ZKLP is a worked example of that pattern applied to a computation with an
**exact** referent, where the verification predicate uniquely determines the hint. It is the case
where the pattern is done right, which makes it a useful control.

## What it actually proves

**Bit-exact IEEE-754. Not a faithful-rounding relaxation, not an interval bound.** The output is
constrained to be *the* correctly-rounded result, the same bits the hardware would produce. This is
the distinction that separates ZKLP from [[garg-fp]] and from [[zip]], and it is the whole reason the
paper is in this collection.

The claim is backed the way such a claim should be: not by a theorem alone but by **conformance
testing against the Berkeley TestFloat suite**, including the edge cases everyone skips, signed
zeros, subnormals, $\pm\infty$, NaN. Subnormals in particular are where partial-compliance
implementations quietly give up (ZKLP notes that the closest 2PC work drops them), and they are
exactly the regime a low-magnitude activation lands in.

The efficiency claim is an **amortized** one, and the distinction matters when reading it:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§1, Introduction"}
The extensive use of lookups leads to amortization — 21 single precision floating point
(FP32) multiplications require 209 constraints, whereas 215
FP32 multiplications require 64 constraints per operation.
:::

(The exponents render as superscripts in the PDF: $2^1$ and $2^{15}$ multiplications.) So the marginal
cost falls as the circuit grows, which is the right shape for ML, where you are proving a great many
identical operations, and the wrong shape for a single scalar computation.

The inversion is the finding. ZKLP benchmarks its float circuits not against other float circuits but
against **fixed point**, and fixed point loses, because reaching comparable accuracy over the
dynamic range the application needs demands so many fixed-point bits that the "cheap" representation
stops being cheap. In an application that genuinely needs dynamic range, floating point is **the
cheaper circuit.** The founding trade of zkML, give up range, buy cheap arithmetic, is a bet, and
this is a worked example of it losing.

And the paper makes the soundness case explicitly, which is rare:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§1, Introduction"}
with randomly generated test cases, fixed-point representation fails some tests whereas
floating-point passes all. Even worse, this inconsistency can be exploited by adversaries
to generate valid proofs for maliciously crafted statements,
thereby breaking the soundness of ZKLP.
:::

That is not a precision complaint dressed up. It is: **the mismatch between the circuit's arithmetic
and the reference implementation's arithmetic is itself an exploitable soundness gap**, a statement
about *completeness-turned-soundness* that applies verbatim to any zkML system whose quantized circuit
disagrees with the float model it claims to be proving.

## What to distrust

**The headline comparison is against a baseline the authors built and call unoptimized.** The
constraint-count advantage over fixed point is measured against `ΠBase`, their own fixed-point
implementation, which approximates $\sin$ by Taylor series and $\arctan$ by Remez *in-circuit*, and
which needs 62-bit and 121-bit fixed-point types to hold the intermediates. That is a genuinely hard
workload for fixed point, a geolocation pipeline with trigonometry and a large dynamic range, and
the authors chose it because it is their application, not to be unfair. But it is not a transformer.
Do not carry the ratio across.

**The regime is wrong for matmuls, and the paper does not claim otherwise.** Sixty-four constraints
per multiply is extraordinary next to the thousands that naive emulation costs. It is still terrible
next to sum-check, which proves an entire matrix product for close to nothing. **Floating point does
not threaten integer sum-check for an LLM's linear algebra**, and any reading of this paper that
concludes otherwise is a misreading.

Where the result plausibly *does* bite is the non-linear operators and the precision-critical rescale
seams, which is exactly where zkML's cost actually lives, and exactly the place nobody has tried it.

**The amortization is not free, it is conditional.** The per-operation cost falls only because lookup
tables are shared across many operations. That is a claim about a circuit with many float ops of the
same kind. Whether a transformer's operator mix, matmul in integers, a handful of float-critical
non-linearities at the seams, amortizes the tables well, or whether you pay for a lookup table to
prove a few thousand GeLUs, is unknown. It is a real question and it cuts against the optimistic
reading.

**Nobody in zkML has cited this paper.** ZKLP's own conclusion proposes the application, it says its
methods can enable "efficient, precise training and inference proofs," citing Kang et al., and in the
two years since, no zkML system in this collection has taken it up. That is not a criticism of ZKLP.
It is the finding: this is a third literature, adjacent to zkML and to the SNARK-vulnerability
literature, and read by neither. See [the citation graph](/graph/).

:::audit  What a reviewer should take from this paper
The reason ZKLP belongs in a soundness section rather than only a numerics one is that it is the
clean demonstration of a pattern the rest of this SoK sees done *badly*.

Every float operation here is a **nondeterministic hint plus a verification predicate**, and the
soundness of the whole IEEE-754 claim reduces to those predicates uniquely determining the hint. The
square-root check is the model: $n^2 \le x < (n+1)^2$, two range checks, and $n$ is pinned. Note also
the field-wraparound reasoning the paper is careful about, its LSB check works precisely because a
dishonest $b$ would push $e$ "close to $(p-1)/2$" where it cannot fit in $E-1$ bits. That is a
constraint whose soundness depends on an argument about $\mathbb{F}_p$'s modulus, written down.

**What to grep for, in any system:** for each nondeterministic hint, the predicate that verifies it.
Then ask the only question that matters, *does this predicate admit exactly one hint, or a set of
them?* ZKLP's admit one. [[garg-fp]]'s relative-error relation admits a ball. [[zip]] inherits the
ball and widens it. Three papers, one pattern, three very different security properties, and the
difference is invisible unless you go and read the predicate.
:::
