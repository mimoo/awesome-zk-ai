---
title: Garg, Jain, Jin & Zhang, Succinct ZK for Floating Point
paper: garg-fp
status: reviewed
---

## What is new

Three contributions, and the field has absorbed only the first.

**The relative-error model.** The observation is that you do not need to prove the IEEE rounding
*procedure*, you need to prove the result is *accurate*. So rather than arithmetising
round-to-nearest, prove a per-gate bound

$$|c - g(a,b)| \le \delta\,|g(a,b)|$$

where $g$ is the **exact** sum or product over the reals and $\delta$ is a relative-error budget
that can be set to machine epsilon, "the relative error bound in the IEEE standard." Zeros,
infinities and NaN are peeled off as corner cases. The move is borrowed, explicitly, from the line
of work that made FHE practical for floats by the same deviation, and it is inspired by numerical
analysis, where bounding per-step relative error and then propagating it is the standard way to
reason about an algorithm's accuracy.

**A generic compiler.** Any public-coin *commit-and-prove* ZK proof of knowledge becomes a succinct
ZK proof system for floating-point computation. The headline asymptotic is the point: for $w$-bit
precision the prover pays only $\log(w)$ overhead, against the $\mathrm{poly}(w)$ that binary-circuit
emulation of IEEE-754 costs. Communication is nearly preserved (up to a factor of two), verification
is sub-linear, and Fiat–Shamir makes it non-interactive.

**A batch range proof without bit decomposition**, and this is the contribution that should
interest a zkML auditor most, because it is the one nobody has picked up. Each gate's error bound is
rearranged into a positivity claim $z > 0$, and positivity is proven via **Legendre's three-square
theorem**: $z > 0 \iff 4z-3$ is expressible as a sum of three squares. No bits, no decomposition, in
standard prime-order groups. Range checks are the dominant soundness surface in every quantized zkML
system we catalogue; a range proof whose cost
does not scale in the bit width is directly relevant to them, and it is sitting unused in a paper
about floats.

## What it actually proves

**Not bit-exact IEEE-754. Not faithful rounding either. An interval bound.** This distinction is the
entire security content of the paper and it is the one a reader skimming for "floating point in ZK"
will get wrong.

The relation certified is that each output wire lies in a **relative ball around the exact
real-arithmetic result**. It is *not* certified that the output is the correctly-rounded IEEE value,
and the paper says so without being asked:

:::quote{src="Garg et al., CCS '22" sec="§2, Our Model"}
our model does not guarantee that the value in the output wire of a step of the computation is
rounded to the nearest number (as is done in the IEEE standard). Instead, our model allows a
larger (by a factor of 2 in some cases) absolute error.
:::

So the relation is **not uniquely satisfying.** For a given $(a,b)$ there are many values of $c$ that
pass. An honest prover puts the correctly-rounded double in the ball; a malicious prover may put
anything in it. That is not a bug, it is the definition of the model, honestly stated, and the
soundness theorem is proved with respect to it.

What makes the model *defensible* rather than merely cheap is an argument the paper makes in §2 and
which deserves to be read slowly, because it is subtle and it is the paper's real intellectual core:
the gap between the relative-error model and exact IEEE **shrinks to nothing in the adversarial
setting**. In a ZK proof the floating-point values are hidden from the verifier, so a malicious
prover may choose inputs that provoke the worst-case rounding error that IEEE *itself* permits, and
IEEE's own worst-case relative error is $\delta$. Against an adversary who picks the numbers,
proving "you rounded correctly" and proving "you landed within $\delta$" certify the same set of
outcomes.

That argument is correct. It is also, I think, load-bearing in a way that does not survive the trip
into zkML, see below.

## What to distrust

**The efficiency numbers are estimates, not measurements.** Table 1 is an analytical R1CS-size
comparison ("We estimate Prover Efficiency based on the total number of non-zero entries"), computed
at $\log_2 p = 384$, a notably large group. The famous "∼57× faster for 32-bit … 236× for 64-bit"
figures are derived from that table, against a *naive binary-circuit* baseline. There is no
implementation. [[zklp]], which did build one, says so directly:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§6, Related Works"}
However, their approach only supports addition and multiplication, whilst not providing a
concrete implementation and only theoretical performance estimates. Also, the verifier time in [23] is linear.
:::

**Addition and multiplication only.** No division, no square root, no transcendentals. For a
transformer that is disqualifying on its face: Softmax needs $\exp$ and a reciprocal, LayerNorm needs
a reciprocal square root, GeLU needs $\tanh$ or $\mathrm{erf}$. These are precisely the operators
where [the cost of zkML actually lives](/zk-inference/numerics/). The paper's technique covers the
part of the network that sum-check already proves almost for free, and omits the part that is
expensive.

**And the adversarial-equivalence argument does not obviously transfer to zkML.** This is my
observation, not the paper's, and it is an open question rather than a break, but it is the reason
this paper is filed under soundness and not merely under numerics.

Garg's defence of the relative-error model rests on the floating-point values being **hidden and
freely chosen by the prover**, so that a worst-case-rounding IEEE execution is indistinguishable from
a $\delta$-deviating one. In a zkML deployment that premise weakens sharply. The **weights are
committed**, and in many threat models the input is public. Against a pinned model and a pinned
input, the correctly-rounded IEEE forward pass is a *deterministic function* with a unique answer, 
and the relative-error relation still admits a ball of them. The freedom the model grants is no
longer freedom the adversary already had by choosing inputs; it is *new* freedom, granted per gate,
per layer, compounding with depth.

Whether that is exploitable, whether an adversary can steer a classification or a next-token argmax
by nudging each value within its ball, and whether the perturbations compound or cancel across a
transformer's depth, **is not analysed here, and is not analysed anywhere.** [[zklp]]'s authors
clearly believe it is exploitable, and say so about machine learning specifically:

:::quote{src="ZKLP (Ernstberger et al.)" sec="§6, Related Works"}
Further, the relative error model in [23] is not suitable for many applications. For instance, it is observed in [18] that for machine learning, even the minor rounding errors due to non-determinism in
GPUs can result in very different predictions. Consequently, an adversary may leverage this fact to generate valid proofs for arithmetic circuits that do not produce the expected
results as in IEEE 754 compliant computer hardware.
:::

That is a *claim in a related-work section*, not a demonstrated attack, and it should be read as one.
But it is a published, adversarially-minded objection to this exact model in this exact application,
raised by people who built the competing construction.

:::audit  Where this lands in the zkML stack
Garg's relative-error relation is not a curiosity, it is **the machinery [[zip]] runs on**, applied
one level up. ZIP does not bind an activation to its true IEEE-754 value; it binds it to a
$\delta$-relative ball around a certified piecewise-polynomial approximation, using exactly this
relation. The two papers differ in one parameter, and the difference is enormous:

- **Garg sets $\delta$ = machine epsilon**, as tight as the model admits. The slack is the slack
  IEEE itself has.
- **ZIP sets $\delta$ = 9e-2 for GeLU** (its own §5.2; 9e-4 for SeLU and ELU). That is a 9%
  per-activation relative-error budget available to a malicious prover, on the flagship activation of
  a paper headlined as double-precision. For scale, bfloat16's machine epsilon is roughly 7.8e-3, an
  order of magnitude *tighter* than the slack ZIP's GeLU proof permits.

**What to grep for:** in any system that proves a non-linearity by an error bound rather than by an
exact table lookup, find $\delta$ and find where it is set. Then ask whether the security argument
was inherited from a paper that set it to machine epsilon.
:::

**A note on what this paper is not.** It is not a zkML paper, it does not claim to be, and it is
cited by no zkML system in this collection. Treating it as a refutation of "floats are infeasible" is
half right: it refutes the *cost* premise for add and multiply, on paper. The construction that
actually refutes the premise end-to-end, with an implementation and full IEEE semantics, is
[[zklp]].
