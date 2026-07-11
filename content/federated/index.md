---
title: The hybrid cell
section: federated
order: 10
lede: >-
  Verifiable federated learning buys some verifiability and some privacy at once, which is why
  it looks like the cell that solved the 2x2. It is not. It proves a narrower claim -- that an
  update is well-formed -- to a weaker verifier, against a weaker adversary, and the distance
  between "well-formed" and "honestly trained" is where every attack lives.
papers: [rofl, acorn, eiffel, prio, zkfl, risefl, byzsfl, provefl, trusted-model-aggregation, kaizen, artemis, optimum-vicinity]
status: draft
---

Federated learning is the one place in this SoK where privacy and verifiability are pursued in the
same protocol, by the same people, in the same paper. That makes it the most interesting cell and
the easiest one to overread.

{{ table:verifiable_federated_learning }}

The setting: many clients each hold private data, each computes a model update locally, and a
server aggregates the updates into a new global model. Secure aggregation hides the individual
updates from the server — the server learns only the sum. That is the privacy half, and it is real.

The verifiability half exists because secure aggregation creates the problem it solves. **If the
server cannot see an update, it cannot check that the update is sane.** A malicious client can
submit anything — an enormous vector that swamps the aggregate, a crafted vector that installs a
backdoor — and the very masking that protects honest clients protects the attacker too.
[[eiffel]] states this tension exactly: secure aggregation masks updates, which is precisely what
stops you checking they are well-formed. Every system in this cell is an answer to that sentence.

## What is actually proven

Read the "what is proven" column of the table slowly, because the titles oversell and the fields
do not. The claims come in exactly two shapes:

**Police the clients.** [[prio]] (the ancestor, not ML-specific), [[eiffel]], [[rofl]], [[acorn]],
[[risefl]], [[byzsfl]] all prove something about each client's *submitted vector*: that it is in
range, that it satisfies an L0/L2/L∞ norm bound, that it satisfies some public predicate. The
proof is zero-knowledge, so the server checks the property without seeing the update.

**Police the aggregator.** [[zkfl]] and [[trusted-model-aggregation]] invert the question: the
clients (or peers) get a proof that the *server* combined the updates honestly. [[provefl]] targets
the same goal by a non-ZK route — servers checking each other's arithmetic under multi-key FHE, sound
as long as at least one server is honest.

Both halves are worth having. Neither is a proof of training. **Nobody in this cell proves that a
client ran gradient descent on real data.** A norm bound bounds the *magnitude* of an update; it
says nothing about its *direction*, and nothing whatsoever about where it came from. A client that
fabricates data, or fabricates the update directly, and then scales it to fit inside the declared
ball, satisfies every constraint in every system above and produces a perfectly valid proof.

:::debate  Is verifiable FL a weaker zkPoT, or a different thing?
The generous reading is that these systems attack a different problem — robustness against
Byzantine clients, not integrity of a training run — and it is unfair to grade them against
[[kaizen]]. That is true, and it is how the papers position themselves ("attestable robustness",
in RoFL's phrase — attestable, not correct).

The uncharitable reading, which we think is the one an auditor has to hold, is that a buyer
reading "verifiable federated learning" hears "the training was verified", and what they get is
"each contribution was inside a box". The systems are honest in their abstracts. The category name
is not.
:::

## Three guarantees that get conflated

|  | Hides the data? | Proves the computation? | Who can verify? |
|---|---|---|---|
| **zkPoT** (Kaizen, zkDL) | yes | yes — the whole training run | anyone |
| **Verifiable FL** (RoFL, ACORN, EIFFeL) | yes | only *properties* of updates | the server, or the peers |
| **Private training** (PriFT) | yes | nothing | nobody |

The third column is the one that decays down the table, and the fourth is the one that quietly
disappears. Almost nothing in this cell is *publicly* verifiable in the sense the inference cell
means it: the verifier is the server, or the other clients, or a peer server, and the proof is not
a succinct artifact you can hand to a stranger a year later. [[provefl]] is explicit about this —
its verifiability is neither succinct nor publicly verifiable — and it is the paper that says so
out loud, not the one that is unusual for being that way.

## Costs live in a different currency

Do not compare anything in this table against a zkPoT proving time. A zkPoT's proving time answers
"how long to produce a succinct proof a stranger can check"; the runtimes here answer "how long
does one round of masked aggregation with validation take", across many clients, over a network.
The dominant cost in this cell is usually **communication**, not prover compute — [[rofl]] needs a
commitment per vector entry, which is the recurring price of putting a zero-knowledge proof on top
of secure aggregation, and [[risefl]] exists specifically to attack that cost. Plotting the two on
one axis would be a category error.

## The people are the same people

Worth noticing, because it explains why the two sides of verifiable training keep converging:
[[rofl]] shares its authors with [[artemis]] in the inference cell (Lycklama, Viand, Küchler,
Hithnawi), and [[acorn]] shares Gascón, Meiklejohn and Raykova with [[optimum-vicinity]] in the
training cell. The same two groups are working the zkPoT side and the secure-aggregation side.
They know these are different guarantees. The literature that cites them frequently does not.
