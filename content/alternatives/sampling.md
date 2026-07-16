---
title: Sampling, trading soundness for milliseconds, on purpose
section: alternatives
order: 40
lede: >-
  Commit the execution trace, open a random sample of it. This is the only alternative
  with a knob: you can dial the soundness error. Which makes it the most interesting one,
  and also the one whose security argument is not a cryptographic argument at all.
papers: [lightweight-sampling-inference, proof-of-sampling, veriml, zkmlaas]
status: reviewed
---

Sampling sits *between* full zkML and the no-proof alternatives, and it is easy to
misfile in either direction. It does use cryptographic commitments, a Merkle-tree vector
commitment to the inference execution trace, so it is not a trust-me system. But it does
not prove the computation. It **opens a random sample of the trace** and checks that the
opened entries are consistent.

[[lightweight-sampling-inference]] is the first scheme to apply this to LLM and DNN
inference. The prover commits to the trace, then reveals only sampled entries along random
paths from the output back toward the input. No full proof is ever generated, which is why
its cost lands in the same order as running the model rather than orders of magnitude above
it, the headline claim, recorded in `papers.yml`, is a move from the order of *minutes* to
the order of *milliseconds*.

The line has ancestry inside this SoK already. [[veriml]] pre-commits to training
iterations and lets the verifier challenge a random subset. [[zkmlaas]] commits to the
intermediate updates and proves only the subset the verifier randomly challenges.
[[proof-of-sampling]] does not commit at all, it re-executes randomly under a
Nash-equilibrium incentive, making it the cheapest and weakest of the sampling family.
What is new is applying trace-sampling to *inference*, where the trace is enormous
and the query volume is high.

## The knob, and the arithmetic behind it

This is the only family in this SoK where the security parameter is something you choose
at deployment time rather than something the protocol hands you. So it is worth writing
down the model explicitly.

Suppose a dishonest prover has corrupted a fraction $\varepsilon$ of the committed trace,
and the verifier opens $k$ entries uniformly at random. The probability that every opened
entry happens to land in the honest part, that the cheat goes undetected, is

$$\Pr[\text{miss}] = (1-\varepsilon)^k$$

so detection probability is $1 - (1-\varepsilon)^k$, and the soundness error decays
*exponentially in the sample size* $k$. Open more of the trace, catch more cheats, pay more
milliseconds. That is a real, tunable, quantifiable guarantee, and no other alternative on
this site has one.

It is also, on its own, worth very little, and seeing why is the whole point of this page.

## The adversary picks ε, and that ruins everything

Read the formula again with an adversary in it. **The prover chooses $\varepsilon$.** They
are not obliged to corrupt a large fraction of the trace; they are obliged to corrupt
enough of it to change the answer. If a meaningful cheat can be executed by perturbing a
*small* fraction of the trace, swap one token's logits, skip one attention head, quantize
one layer more aggressively, then $\varepsilon$ is tiny, $(1-\varepsilon)^k \approx 1$,
and the detection probability collapses no matter how you set $k$.

So the sampling arithmetic is not the security argument. It is a *consequence* of the
security argument, and the actual argument is the premise the arithmetic needs:

> **A cheat that changes the output must perturb a large fraction of the trace.**

[[lightweight-sampling-inference]] names this and rests on it: security follows from
**trace separation between functionally dissimilar models**. If two models produce
different outputs, their execution traces must differ substantially, so the cheating
prover cannot be sparse, $\varepsilon$ is bounded below, and the exponential kicks in.

**This is a machine-learning claim, not a cryptographic one.** It is a statement about the
geometry of transformer activations under adversarial perturbation, and it is exactly as
true as the experiments that support it. The paper's evidence is real and serious, it
tests gradient-descent reconstruction, inverse transforms, and logit swapping against
ResNet-18 and Llama-2-7B, and none of them evaded detection, but adversarial ML has a
long, humbling history of defences that survived three attacks and fell to the fourth.

:::audit  This is where you attack it
Do not attack the Merkle commitment; it is fine. Attack the trace-separation premise.
Construct a modification to the model that (a) changes the output in a way the prover
profits from, and (b) leaves the overwhelming majority of trace entries bit-identical. The
natural candidates: perturb only the final logit layer; alter behaviour only on a narrow
input trigger (a backdoor, which is *by construction* a sparse trace perturbation);
exploit any part of the trace that is not sampled uniformly, and the sampling here is
along **random paths from output back to input**, which is not the same as uniform, and
therefore has a structure an adversary can study.

**What the bug looks like:** a model substitution that is cheaper to serve, produces the
attacker's preferred output on the inputs they care about, and differs from the honest
trace in a vanishing fraction of entries.
:::

To their credit, the authors are not naive about this, they include SNARK researchers,
and `papers.yml` records the framing as deliberate: the paper says outright that it
"trades soundness for efficiency." This is a design point, not an oversight. Our objection
is not that they made the trade. It is that the field has no vocabulary for stating what
the trade bought, so the number that gets quoted is the milliseconds.

## Two more assumptions to price

**The prover must be rational.** Detection is not punishment. The guarantee is that a
cheater is *caught* with some probability and *penalised* on detection, so the security
statement is about expected value: cheating must cost more than it earns. That requires a
penalty mechanism, a stake, and an adversary who is maximising money rather than, say,
causing a specific output on a specific input. An adversary willing to burn a bond to get
one answer through is outside the model entirely.

**The guarantee amortises over queries, not within one.** Detection probability amplifies
under *repeated* queries, which is a real and useful property, and it makes this the right
tool for auditing a high-volume MLaaS provider over time. It makes it the *wrong* tool for
a one-shot on-chain settlement, where there is no second query to amplify with, and the
adversary's payoff is concentrated in the single transaction you are trying to protect.

:::debate  Is a millisecond "proof" comparable to a twenty-second one?
No, and the comparison is made constantly, because both live in a column called "proving
time." A cryptographic proof catches a cheating prover with probability overwhelming in a
security parameter, on the first and only query, against an adversary of unbounded
strategy. A sampled trace catches one with a probability that depends on how sparsely they
cheated, amortised over queries, assuming they are economically rational. The right
comparison axis is $\text{cost} \times (\text{detection probability} \times
\text{penalty})$, not cost. Plotting them on the same throughput chart is a category
error, and this SoK does not do it.
:::

The paper does supply a formal soundness statement, it bounds other-model soundness by the
sum of a trace-separation error and a testing error, and gives algorithms for estimating
both empirically. What it does not do is turn the number of opened paths into a soundness
curve, and it says so itself:

:::quote{src="Lightweight Sampling Proofs of Inference" sec="§5.2, Security"}
Understanding the precise tradeoffs between the number of sampled paths, proof size, and
the resulting soundness guarantees is an important direction for future work.
:::

:::gap  The soundness-vs-sample-rate tradeoff is left to future work
The paper also notes that any single-path strategy has detection probability capped at
$1/N$ for maximum layer width $N$, and that full soundness, where the adversary is free to
construct the trace arbitrarily, remains open. Until the curve exists, the "tunable
guarantee" cannot actually be tuned by a deployer, because they have no way to convert a
chosen $k$ into a statement about risk. Producing that curve is the highest-value follow-up
on this page.
:::

---

The reason this scheme is the most interesting of the alternatives is not that it is the
best. It is that it is the only one that makes its weakness **legible**. Optimistic systems
hide their assumption inside the word "AnyTrust"; TEEs hide theirs inside a vendor's
signature. Sampling puts a dial on the front of the box and writes the units on it. That
the units turn out to be measured in an ML property rather than a cryptographic one is a
finding, but at least it is a finding you can go and check.
