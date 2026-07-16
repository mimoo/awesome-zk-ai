---
title: EIFFeL
paper: eiffel
status: reviewed
---

## What is new

EIFFeL names the tension that defines this whole cell, in one sentence: **secure aggregation masks
the updates, which is exactly what stops you checking the updates are well-formed.** Privacy and
integrity are, in federated learning, in direct opposition, the mask that protects an honest client
is the mask a poisoner hides behind.

The construction resolves it with **secret-shared non-interactive proofs**, in the SNIP lineage, and
its distinguishing move is *who does the verifying*. Prio, the ancestor of this cluster, needs
multiple non-colluding servers to check each client's proof. EIFFeL does not:

:::quote{src="EIFFeL" sec="§7, Verifying Data Integrity in Secure Aggregation"}
This is different from Prio [28] (the original SNIP deployment setting) that rely on multiple honest
servers to perform verification.
:::

Instead **the clients verify each other**, on Shamir shares of one another's proofs. There is one
server, it is untrusted, and it never sees an unmasked update or an unmasked proof. That is a
materially better deployment story than Prio's, and it is the reason EIFFeL exists.

The second contribution is generality. [[rofl]] proves *range* bounds; [[acorn]] proves L0/L2/L∞
bounds. EIFFeL enforces an **arbitrary public predicate** on each update, and, crucially, does not
merely *detect* a malformed update but **removes it from the aggregate** while completing the round.
A poisoned client is dropped, not allowed to abort the protocol.

## What it actually proves

Per client, per training round: **that a client's masked update satisfies a public validation
predicate**, verified collaboratively by the other clients on secret shares, with malformed updates
excluded from the sum.

Soundness rests on SNIP's error term, and the paper does the arithmetic rather than waving at it:
the rejection probability at its evaluated dimensions works out on the order of 10⁻¹², which is a
real number and an honest one.

What it does **not** prove is that the update is the result of honest local training. Same ceiling as
[[acorn]] and [[rofl]]: a predicate on the update is not a proof of the computation that produced it.
An adversary who satisfies the predicate still poisons. Only [[zkpot-garg]] and the
[zk-training](../../zk-training/) cell attempt the stronger claim, and they pay for it.

## What to distrust

**The headline number is real and it describes a model with a thousand parameters.**

The abstract's claim, MNIST, 100 clients, 10% poisoning, 2.4 s per iteration, matching non-poisoned
accuracy, is verbatim, and it checks out against Table 2. `papers.yml` recorded it faithfully. What
`papers.yml` did *not* record was `d`, the update dimensionality, and without `d` the figure is not
interpretable, because **cost is linear in it**.

:::audit The benchmark is n = 100, d = 1000, and the paper's own table shows the blow-up
End-to-end time per iteration (Table 2, `d = 1000`, `m = 10%` malicious), by client count:

| Clients (n) | 50 | 100 | 150 | 200 | 250 |
|---|---|---|---|---|---|
| End-to-end | 1,072 ms | **2,367 ms** | 4,326 ms | 6,996 ms | 10,389 ms |

That is **quadratic in n**, the complexity is `O(m·n·d)` and `m` is a fixed *fraction* of `n`, and
the table stops at 250 clients.

In `d` it is **linear**, and §6 states the slope directly: a client takes 1.3 s at `d = 1K` but
"around 11s when `d = 10K`".

So the famous 2.4 s is: **one hundred clients, and a one-thousand-parameter "MNIST classifier."**
Production federated learning runs thousands to millions of clients over models with 10⁵–10⁹
parameters. That is several orders of magnitude past the benchmark **on both axes at once**, with
cost quadratic in one and linear in the other.
:::

**And 2.4 s is not a proving time.** It is the **end-to-end** per-iteration wall clock, client
compute, server compute *and* network latency. The client's own share at that configuration is
roughly half of it. The previous `papers.yml` entry tagged it `proving_time_s`, which would have
made it look directly comparable to the proving times in the [zk-inference](../../zk-inference/)
tables. It is not that quantity. Both figures are now recorded separately.

**None of this is dishonest on the paper's part.** Table 2 *is* the scaling data; the paper publishes
the numbers that show its own ceiling, in the section right after the abstract's claim, and it never
suggests the configuration is representative. The failure was entirely downstream, ours, and the
field's. An abstract that says "2.4s per iteration" travels; the `d = 1000` that makes it true does
not travel with it. That is precisely the drift this SoK exists to catch, and it is the reason
`papers.yml` now refuses to carry the timing without the dimension.

:::gap Nobody has costed integrity-checked FL at deployment scale
[[rofl]], [[acorn]] and EIFFeL all benchmark in the hundreds of clients. Cross-device federated
learning, the setting all three cite as motivation, recruits clients in the millions and trains
models in the millions of parameters. Every protocol here is at least quadratic in the client count.

Not one of these papers reports a number at a scale anyone would deploy, and the SoK should not
pretend otherwise.
:::
