---
title: Optimistic verification — fraud proofs and challenge windows
section: alternatives
order: 20
lede: >-
  Do not prove anything. Assert the output, wait, and let anyone who disagrees prove you
  wrong. The assumption is not "one honest party" — it is one honest party who is
  watching, who can afford to re-execute, and who is paid enough to bother.
papers: [opml, opp-ai, zk-opml, optimistic-tee-rollups, safetynets]
status: draft
---

The optimistic construction is the oldest idea in verifiable computation and still the
cheapest: **do not generate a proof.** Publish the claimed output, open a challenge
window, and if anyone disputes it, fall back to an interactive protocol that adjudicates
who is right — a fraud proof, typically a bisection game that narrows the disagreement to
a single instruction, which a referee can then execute directly.

[[opml]] is the reference point, and it is the strongest argument against zkML as a
default. Because it never generates a proof unless challenged, the honest path costs
approximately what running the model costs. It runs a 7B-parameter LLaMA on a standard PC
with no GPU. There is no zkML system in this SoK within three orders of magnitude of that.

## What the security assumption actually is

The papers call it *AnyTrust*: **any single honest validator can force correct behaviour.**
That phrasing is accurate and it is also doing a lot of compression. Unpacked, an
optimistic system is safe only if all of the following hold:

1. **An honest challenger exists.** Not a majority. One. This part really is a weak
   assumption, and it is the whole appeal.
2. **The challenger is watching.** They must observe the claim inside the window. A
   validator who is offline during the challenge period is, for that claim, not a
   validator.
3. **The challenger can re-execute.** To know the output is wrong you must compute the
   right one, which means you need the weights. Optimistic verification is therefore
   **incompatible with model privacy** — someone must be able to run the model to police
   it. This is not a performance limitation that will be engineered away; it is
   structural.
4. **Challenging is worth it.** The bond, the gas, the compute, and the opportunity cost
   of the dispute must be less than the reward for winning it. A rational validator who
   spots a fraud whose bounty is smaller than the cost of proving it will do nothing.
5. **The dispute game itself terminates correctly** against an adversary who can grief it
   — spam challenges, delay responses, or censor the challenger's transaction inside the
   window.

Assumption 1 is the one the papers advertise. Assumptions 2 through 5 are where the
failures live, and they are not cryptographic failures. They are liveness, economics, and
censorship failures, which is to say: they are the failures that actually happen.

:::audit  The censorship attack is the one to model
Every optimistic system's safety collapses to a **liveness assumption on the challenger's
transaction**. If an adversary can keep the challenge out of the chain until the window
closes — by congestion, by bribing a sequencer, by being the sequencer — the fraudulent
output finalises and the honest challenger's correctness was irrelevant. This is a known
problem in optimistic rollups generally, and no ML-specific paper in this SoK analyses it
in the ML setting, where the challenge is far more expensive to produce than a rollup's.
:::

## What it costs you, stated plainly

**Latency to finality.** The output is not trustworthy until the window closes. For an
on-chain settlement that is a delay measured in whatever the window is; for an
interactive user-facing product it is fatal. [[optimistic-tee-rollups]] exists largely to
paper over exactly this, offering sub-second *provisional* finality backed by hardware
and deferring the real guarantee to the fraud-proof path.

**Verifiability only for the watchers.** A ZK proof convinces a party who shows up two
years later with no context. An unchallenged optimistic claim convinces you only if you
believe someone competent was watching at the time. Those are different epistemic
objects, and the second one does not compose across time or across trust boundaries.

**Privacy.** See assumption 3. You cannot have a challenger who can re-execute and a model
that is secret.

## The inversion

The most useful thing [[opml]] says is not about cost, it is about *ordering*. A challenge
window is a **constant**. A zkML proving time is a **function of model size** that grows
faster than the model does. Past some crossover point, the ZK proof takes longer to
produce than the optimistic system takes to finalise — at which point the optimistic
system is both cheaper *and* faster, and the only thing ZK is still selling is the
strength of the assumption.

Nobody in this SoK has located that crossover point empirically. It is a genuinely
answerable question: it needs one proving-time curve and one challenge-window constant.

:::gap  Where is the crossover?
The claim "for large enough models, opML finalises before zkML proves" appears in the
optimistic literature as an argument. It has never been plotted. Doing so would need a
proving-time-vs-parameters curve (which [the inference section](/zk-inference/) has the
data for, with caveats) against a stated challenge window (which the optimistic papers
give). Nobody has drawn the two lines on the same axes.
:::

## The hybrids

Two systems here refuse the binary, and both are more interesting than either pure design.

[[opp-ai]] splits **by privacy need**: prove the privacy-sensitive submodel in ZK, run the
rest optimistically. This is a direct response to assumption 3 above — it carves out the
part of the model that cannot be exposed to a challenger and pays ZK's price only there.
Whether the split leaks anything about the boundary between the two halves is not
something the paper addresses.

[[zk-opml]] splits **by operator**: decompose inference to the ONNX operator level, verify
optimistically, and generate ZK proofs only for isolated operators where they are needed.
This is the same instinct as [the operator atlas](/zk-inference/) — that not all operators
are equally hard or equally dangerous — applied to trust rather than to cost.

[[optimistic-tee-rollups]] splits **by role**: hardware for throughput, fraud proofs for
finality, and stochastic ZK spot-checks to bound the probability that the hardware was
compromised. It is the most sophisticated construction on this page and the one with the
most assumptions to compose. See [TEEs](/alternatives/tees/).

---

One historical note worth keeping. [[safetynets]] — the 2017 ancestor of the entire
sum-check zkML lineage — is *itself interactive*: the verifier sends live challenges and
the prover responds. In a sense the whole field started somewhere between these two
worlds, and both branches are attempts to remove the interaction: ZK by compiling the
verifier away with Fiat–Shamir (which is what the Fiat–Shamir
result attacks), and optimistic systems by making the interaction
rare rather than removing it. The optimistic branch never took on that attack surface,
because it never took that step.
