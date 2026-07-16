---
title: The hybrid cell
section: federated
order: 10
lede: >-
  Verifiable federated learning buys some verifiability and some privacy at once, which is why
  it looks like the cell that solved the 2x2. It is not. It proves a narrower claim -- that an
  update is well-formed -- to a weaker verifier, against a weaker adversary, and the distance
  between "well-formed" and "honestly trained" is where every attack lives.
papers: [rofl, acorn, eiffel, prio, zkfl, risefl, byzsfl, provefl, trusted-model-aggregation, kaizen, zkdl, artemis, optimum-vicinity, prift]
status: reviewed
---

Federated learning is the one place in this SoK where privacy and verifiability are pursued in the
same protocol, by the same people, in the same paper. That makes it the most interesting cell and
the easiest one to overread.

{{ table:verifiable_federated_learning }}

The setting: many clients each hold private data, each computes a model update locally, and a
server aggregates the updates into a new global model. Secure aggregation hides the individual
updates from the server, the server learns only the sum. That is the privacy half, and it is real.

The verifiability half exists because secure aggregation creates the problem it solves. **If the
server cannot see an update, it cannot check that the update is sane.** A malicious client can
submit anything, an enormous vector that swamps the aggregate, a crafted vector that installs a
backdoor, and the very masking that protects honest clients protects the attacker too.
[[eiffel]] states this tension exactly: secure aggregation masks updates, which is precisely what
stops you checking they are well-formed. Every system in this cell is an answer to that sentence.

## What is actually proven

Read the *what is proven* field of each paper in this cell slowly, because the titles oversell and
the fields do not. The claims come in exactly two shapes:

**Police the clients.** [[prio]] (the ancestor, not ML-specific), [[eiffel]], [[rofl]], [[acorn]],
[[risefl]] all prove something about each client's *submitted vector*: that it is in range, that it
satisfies an L0/L2/L∞ norm bound, that it satisfies some public predicate. The proof is
zero-knowledge, so the property is checked without the update ever being seen, but *who* checks
differs: the server in [[rofl]] and [[acorn]], multiple servers in [[prio]], and the other clients,
under the server's supervision, in [[eiffel]], which is precisely how EIFFeL drops Prio's
honest-server assumption.

**Police the aggregator.** [[zkfl]] and [[trusted-model-aggregation]] invert the question: the
clients (or peers) get a proof that the *server* combined the updates honestly. [[provefl]] targets
the same goal by a non-ZK route, servers checking each other's arithmetic under multi-key FHE, sound
as long as at least one server is honest.

([[byzsfl]] is unread, from its abstract it proves the *aggregation-weight computation* was done
correctly, which is a third shape, and we cannot place it more precisely than that.)

Both halves are worth having. Neither is a proof of training. **Nobody in this cell proves that a
client ran gradient descent on real data.** A norm bound bounds the *magnitude* of an update; it
says nothing about its *direction*, and nothing whatsoever about where it came from. A client that
fabricates data, or fabricates the update directly, and then scales it to fit inside the declared
ball, satisfies every constraint in every system above and produces a perfectly valid proof.

:::debate  Is verifiable FL a weaker zkPoT, or a different thing?
The generous reading is that these systems attack a different problem, robustness against
Byzantine clients, not integrity of a training run, and it is unfair to grade them against
[[kaizen]]. That is true, and it is how the papers position themselves ("attestable robustness",
in RoFL's phrase, attestable, not correct).

The uncharitable reading, which we think is the one an auditor has to hold, is that a buyer
reading "verifiable federated learning" hears "the training was verified", and what they get is
"each contribution was inside a box". The systems are honest in their abstracts. The category name
is not.
:::

## Three guarantees that get conflated

|  | Hides the data? | Proves the computation? | Who can verify? |
|---|---|---|---|
| **zkPoT** ([[kaizen]], [[zkdl]]) | yes | yes — the whole training run | anyone |
| **Verifiable FL** ([[rofl]], [[acorn]], [[eiffel]]) | yes | only *properties* of updates | the server, or the peers |
| **Private training** ([[prift]]) | yes | nothing | nobody |

The third column is the one that decays down the table, and the fourth is the one that quietly
disappears. Almost nothing in this cell is *publicly* verifiable in the sense the inference cell
means it: the verifier is the server, or the other clients, or a peer server, and the proof is not
a succinct artifact you can hand to a stranger a year later. [[provefl]] is the clearest case: its
verifiability is a bilateral check between servers, sound only if at least one of them is honest, 
neither succinct nor publicly verifiable. It is the paper whose design makes that legible, not the
paper that is unusual for having the limitation.

## Costs live in a different currency

Do not compare a runtime from any paper in this cell against a zkPoT proving time. A zkPoT's proving
time answers "how long to produce a succinct proof a stranger can check"; the runtimes these papers
report answer "how long does one round of masked aggregation with validation take", across many
clients, over a network.

The recurring price of putting a zero-knowledge proof on top of secure aggregation is a commitment
per vector entry, [[rofl]] pays it, and it makes both the proof and the message linear in the model
dimension. That linearity is a compute cost as much as a bandwidth cost: [[acorn]]'s ZK validation
buys its cheap communication with heavy client proving, and [[risefl]] (which we have not read; this
is from its abstract) targets the *proof generation and verification* cost that linearity imposes.
Either way the currency is not a zkPoT's, and plotting the two on one axis would be a category error.

## The people are the same people

Worth noticing, because it explains why secure aggregation and verifiable ML keep converging:
[[rofl]] shares its authors with [[artemis]] in the inference cell (Lycklama, Viand, Küchler,
Hithnawi), and [[acorn]] shares Gascón, Meiklejohn and Raykova with [[optimum-vicinity]] in the
training cell. One group works the secure-aggregation side and the *proving-inference* side; the
other works the secure-aggregation side and the *zkPoT* side. They know these are different
guarantees. The literature that cites them frequently does not.
