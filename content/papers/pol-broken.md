---
title: Proof-of-Learning is Currently More Broken Than You Think
paper: pol-broken
status: reviewed
---

The second break of [[pol]] — and look at the author list. Fang, **Jia**, Thudi, **Yaghini**,
**Choquette-Choo**, **Dullerud**, **Chandrasekaran**, **Papernot**.

That is largely the original Proof-of-Learning team, breaking their own scheme. It is the most honest
thing in this corpus.

## The attacks

Two, both cheaper and far more robust than [[pol-adversarial]]'s.

**The infinitesimal update attack.** Linearly interpolate the checkpoints between the initialization
and the stolen final model. Then log a **learning rate of approximately zero**, so that every update
is smaller than the verification threshold $\delta$. The logged update is negligible; the verifier's
replayed update is negligible; their difference is therefore negligible; verification passes.

The cost is the punchline: **no training at all.** One floating-point operation per parameter per
step — upper-bounded by a *single forward pass* — against the previous break's ~31 gradient
computations per step.

**The blindfold top-Q attack** kills the other half of the scheme. [[pol]] verifies the $Q$ largest
updates per epoch. So: make exactly $Q$ genuinely-valid updates with a large learning rate, so they
have the largest magnitudes by construction, and interpolate everything else. The verifier's top-$Q$
heuristic lands on precisely the $Q$ real updates, every time, and never inspects the fakes.

## What it establishes

The two implicit assumptions under [[pol]] — that training is *reproducible* within $\delta$, and that
the largest updates are *representative* of the run — are both false, and neither was ever stated.

It also corrects the first break, which matters if you were about to cite it: [[pol-adversarial]]'s
Attack 1 is "not reproducible" (neither team could make it work), and its Attack 2 assumed the
attacker sets $k$ and $\delta$, which are the verifier's to choose. So the earlier attacks are "easily
thwarted by changing hyperparameters of the verification." These are not.

## The conclusion, which is why the paper is here

:::quote{src="Fang et al." sec="Abstract"}
We conclude that one cannot develop a provably robust PoL verification mechanism without further
understanding of optimization in deep learning.
:::

And the way out, in their own words:

> *"One possible solution to circumvent these fundamental limits in ML theory and our understanding of
> optimization, is to rely more on cryptography."*

Both attack papers arrive at the same door, from opposite directions. [The zkPoT
cell](/zk-training/) is what is behind it.

## What to distrust — in the good sense

The paper is careful about what it has *not* shown, and the care is worth inheriting. It does **not**
show that PoL's precedence guarantee is broken: empirically, data-ordering attacks and synthesized
adversarial data both *fail* to reach the target weights from an independent initialization, so
knowledge of the final weights appears genuinely essential to a spoofing adversary.

It shows that PoL's guarantee is **unproven**, not that it is **false**. That is a distinction the
citing literature routinely loses, and it is the same distinction this SoK keeps making about
soundness-versus-statement everywhere else.
