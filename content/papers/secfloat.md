---
title: SecFloat
paper: secfloat
status: reviewed
---

## What is new

The insight is a *refusal*. Everyone before SecFloat got floating point into a secure computation by
one of two routes: compile an IEEE-754 Boolean circuit and run it under generic 2PC (ABY-F, and see
[[archer-ieee]] for what that costs), or hand-write imprecise custom functionalities (MP-SPDZ).
SecFloat rejects both framings and builds each float operation, add, multiply, divide, compare, and
each math function, `exp`, `log`, `sin`, `cos`, `tan`, out of **integer 2PC building blocks chosen
for their communication cost**, rather than out of gates.

The design constraint it names generalizes well beyond MPC, and is worth stealing: the standard math
libraries are *precise but not crypto-friendly*, because they lean on operations that are cheap on a
CPU and ruinous under 2PC (high-bitwidth intermediates, above all). The existing cryptographic
libraries are *crypto-friendly but imprecise*. SecFloat's functionalities are built to be both, each
with a proven precision guarantee, and the library is validated against a real math library rather
than against itself.

It is not a ZK system and not an ML system. It is here because of what it *measures*.

## What it actually proves

Nothing. **SecFloat produces no proof.** It is a semi-honest two-party library over secret shares; a
malicious server can compute the wrong function and nobody will know. Malicious security is
explicitly future work.

What it *establishes*, and what earns it a place in this corpus, is a counterexample:

:::quote{src="SecFloat" sec="Abstract"}
All prior works on secure inference of deep neural networks rely on ad hoc float-to-fixed converters.
We evaluate a model where the fixed-point approximations used in privacy-preserving machine learning
completely fail and floating-point is necessary.
:::

The model is real: an industrial ad-relevance network, a fully-connected net taking an
874-dimensional input through three hidden layers to a four-class softmax. Its weights span roughly
eight orders of magnitude, and its intermediate activations span more. The authors ran it through
CrypTFlow, which **enumerates fixed-point models at every possible scale and picks the most accurate
one**, and *none* of them worked. The large values overflow the integers; the small ones underflow
to zero; in the paper's words, "the fixed-point model output is garbage."

That is an **exhaustively searched** negative result on a production model, and it is the strongest
evidence in this corpus against the premise, universal in the zkML column, that a good quantization
scale always exists if you look hard enough for it.

## What to distrust

**It is an existence proof, and must not be read as a distributional one.** SecFloat shows there
*exists* a real deployed model on which every fixed-point scale fails. It does not show that fixed
point generally fails, and this corpus contains a lot of evidence that it usually does not:
[[zkgpt]] holds GPT-2's perplexity to within half a point at 16 bits, [[deepprove]] to within a
fraction of a percent at 12, [[zkpytorch]] loses almost nothing on CIFAR-10. The model SecFloat chose
was chosen *because* it breaks, that is what a counterexample is for, and it breaks for a specific,
diagnosable reason (extreme weight dynamic range) that transformers do not obviously share.

The correct reading is narrower and still important: **"quantize, it will be fine" is an empirical
bet about the workload, not a theorem, and it has a published counterexample that the zkML literature
has never cited or answered.**

**"No good scale exists" is relative to CrypTFlow's quantizer, which is not the state of the art.**
CrypTFlow searches over *uniform, per-tensor* fixed-point scales. It does not do per-channel
quantization, and it does not do outlier smoothing. Outlier smoothing by orthonormal rotation is
precisely the technique [[deepprove]] uses to rescue Gemma 3, whose activations exhibit *the same
pathology* that kills SecFloat's relevance model, a few enormous outlier channels swamping the
quantization grid. A modern quantizer might well find a scale CrypTFlow's search could not. Nobody
has tried, and SecFloat could not have: the technique postdates it.

**The precision headline is measured against baselines that are imprecise by construction.** The
"six orders of magnitude more precise" figure is against ABY-F and MP-SPDZ, whose math functions are
*known* to be imprecise, that is SecFloat's entire complaint about them. Against the one genuinely
precise baseline the paper builds (Berkeley SoftFloat's primitives, reimplemented on SecFloat's own
building blocks), the communication advantage collapses to a small single-digit factor. That is the
honest apples-to-apples number, and the paper prints it in the body, unprompted. Credit for that.

**Floats are affordable here only at toy scale.** Secure inference of that relevance model, a few
hundred thousand parameters, no attention, no convolution, costs communication measured in gigabytes
for a single input, and hundreds of gigabytes at a small batch. SecFloat does not make float
inference cheap. It makes it *possible*. The scaling wall is the same one that caps [[iron]],
[[bolt]] and [[nimbus]].

**And the cost model does not transfer to ZK.** SecFloat's currency is communication and rounds; a
zkML prover's is field operations and commitment openings. A 2PC communication figure is evidence
about *arithmetic difficulty*, not about proving time. Nothing here belongs on a chart in this SoK.

:::debate SecFloat is the paper ZIP needed and did not cite
[[zip]]'s case for abandoning fixed point rests on a fixed-point baseline it never specifies, which
mysteriously fails to converge. SecFloat's rests on an exhaustive scale search over a real production
model, with the failure mechanism diagnosed and named.

**ZIP is in the ZK column. SecFloat is in the MPC column. ZIP does not cite it.** That is not an
oversight so much as a structural fact about this field, and it is the same fact the citation graph
reports: when the verifiability column needs an argument about real numbers, it re-derives one rather
than reading the column that has been arguing about real numbers for a decade.
:::

:::gap SecFloat is a bridge node, and it is the only kind we have
SecFloat is cited by [[bolt]] (privacy column) *and* by [[zkpot-garg]] (verifiability column), the
citations are in both bibliographies; we checked. [[archer-ieee]] is likewise cited by [[zip]]
(verifiability) and by SecFloat itself (privacy).

This does **not** break the corpus's headline finding. No edge runs *directly* between the
proving-inference and the private-inference literatures. But both columns reach for the *same
numerics primitives* when they have to reason about real numbers. They share a foundation and not a
conversation.
:::
