---
title: What each system actually proves
section: federated
order: 20
lede: >-
  Nine systems, two claims. Either a client's update is well-formed, or the aggregator
  aggregated honestly. Read one by one, the pattern is unmissable -- and so is the gap: not
  one of them binds an update to the data it was supposedly computed from.
papers: [prio, eiffel, rofl, acorn, risefl, byzsfl, zkfl, trusted-model-aggregation, provefl, kaizen, optimum-vicinity]
status: reviewed
---

{{ papers:verifiable_federated_learning }}

## Policing the clients

**[[prio]]**, the ancestor of the whole cluster, and not an ML system at all. Prio's SNIPs
(secret-shared non-interactive proofs) let a client submit a value to a set of servers together
with a zero-knowledge proof that the value is well-formed and in range, so the servers can compute
an aggregate over inputs none of them can see. Every "prove your update is in range" scheme below
is a descendant. Prio+ replaces the SNIPs with Boolean shares.

**[[eiffel]]**, the generalization to a *public predicate*. Instead of a fixed range check, the
protocol validates an arbitrary declared predicate on each update, and malformed updates are
removed from the aggregate rather than merely detected. The clients act as verifiers, using
SNIP-style proofs plus Shamir secret sharing. This is the system that best states the problem the
cell exists to solve, and it is the most flexible answer to it, but note carefully that the
predicate is a *free parameter*. EIFFeL will faithfully enforce whatever predicate you can write.
It does not tell you which predicate makes your model safe, and no such predicate is known. The
flexibility is not free. Client and server computation are both quadratic in the client count and
linear in the update dimension, and the evaluation stops well short of federated-learning scale on
both axes, read any headline timing for this system together with the model size it was measured
at.

**[[rofl]]**, zero-knowledge range proofs enforcing L2 / L∞ norm bounds on client updates, over
commitments to the encrypted updates. The paper's own phrase is *attestable robustness*, which is
precisely the right level of claim: you get an attestation that a constraint held, and the
constraint is a robustness heuristic, not a correctness statement. The cost is a commitment per
vector entry, which is why this cell has a communication problem.

**[[acorn]]**, input validation for secure aggregation, proving L0 / L2 / L∞ bounds on client
inputs. It is really three protocols and they must be kept apart: the base secure-aggregation
protocol (RLWE-SecAgg) is where the client-computation speedup over the prior Bell et al. protocol
comes from, and it involves no zero knowledge at all. The ZK input-validation layer bolted on top
is cheap in *bytes*, the paper's gain over prior ZK validation such as RoFL is in client
communication, at comparable computation cost. Same claim shape as RoFL, far better communication
constants, from the Google group that also produced [[optimum-vicinity]].

**[[risefl]]**, targets exactly the cost that makes RoFL expensive: the ZK overhead of
per-entry commitments. We have not read it, so we cannot say what it gives up to get there, and
that is the question to ask of it.

**[[byzsfl]]**, Byzantine-robust secure FL with zero-knowledge proofs. We have not read it. It is
listed so it is not silently missing.

:::gap  Two of the nine are unread
[[risefl]] and [[byzsfl]] are indexed from their abstracts only, and [[zkfl]]'s numbers have not
been extracted. Any claim on this page about *those three* is a claim about their abstracts.
:::

## Policing the aggregator

**[[zkfl]]**, the dual. Instead of the server checking the clients, the clients get a
zero-knowledge proof that the *aggregator* combined their gradients honestly. This closes a real
hole, in vanilla secure aggregation the server is trusted to actually do the sum, and it is a
completely different threat model from RoFL's. A deployment that wants both needs both.

**[[trusted-model-aggregation]]**, aggregation integrity under Byzantine adversaries, with ZK
proofs shared over an overlay network. Same family as zkFL.

**[[provefl]]**, the outlier, and it is important to file it correctly. It reaches the same goal
(the aggregation was done right) by an entirely non-ZK route: multi-key FHE plus discrete-log
commitments, with peer servers checking each other's aggregation arithmetic through bilinear
pairwise checks, sound as long as at least one server is honest. We verified this directly: the
strings "zero-knowledge", "ZKP" and "SNARK" do not appear anywhere in the paper. Its verifiability
is neither succinct nor publicly verifiable, and its reported runtimes are *per-round aggregation
costs, not proving times*. It belongs in this cell; it does not belong in any comparison with a
zkPoT.

## The pattern, and the gap where the attacks live

Every system above proves a property of a *submitted vector*, or a property of an *arithmetic
combination of submitted vectors*. Not one of them proves anything about the relationship between
a submitted vector and the data it was supposedly computed from.

That gap is not a technicality. It is where the entire poisoning literature operates.

- **A norm bound bounds magnitude, not direction.** The set of updates inside an L2 ball is
  enormous, and it contains backdoor-installing updates. Constraining the norm makes an attacker
  work harder, they must spread the attack over more rounds, or accept a weaker backdoor, but it
  does not exclude them. The papers know this; they claim robustness, and robustness is a
  quantitative property with a threshold, not a proof.
- **The bound is a tuning parameter with a real cost.** Tighten it and you clip the updates of
  honest clients with unusual (but legitimate) data, which in federated learning is the *normal*
  case, since client distributions are heterogeneous by construction. Loosen it and the attacker's
  ball grows. There is no setting that is safe and free, and the trade-off is a modelling decision
  dressed as a security parameter.
- **Nothing binds the update to real data.** A client can fabricate its dataset entirely, run
  honest gradient descent on the fabrication, and produce a well-formed, norm-bounded, perfectly
  provable update. Every check in every system above passes. This is the residual that a reader
  who hears "verifiable federated learning" would never guess at, and it is not fixable by a better
  predicate, proving "I computed this from data" requires committing to the data, which is what a
  zkPoT does and what nobody in this cell does.
- **A well-formed update from a Sybil is still well-formed.** Identity and rate-limiting are
  outside the proof, in the deployment. They are load-bearing.

:::audit  What to ask a verifiable-FL deployment
Who is the verifier, the server, the peers, or the public? Is the proof succinct and retainable,
or is verification a live protocol that leaves no artifact? What predicate is enforced, who chose
its threshold, and what is the measured clipping rate on honest clients? Is the aggregator itself
proven honest, or only the clients, and if only the clients, who checks the sum? And, finally:
what stops a well-behaved client from submitting a well-formed update computed from data it made
up?
:::

The right way to hold this cell is that it makes a *specific class of attack* (unbounded or
malformed contributions) impossible, and a *second class* (bounded, well-formed, malicious
contributions) merely harder. That is real progress and it is worth deploying. It is not the claim
that [[kaizen]] makes, and the two should never be tabulated together.
