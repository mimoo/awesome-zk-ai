---
title: TEEs — the assumption that is actually deployed
section: alternatives
order: 30
lede: >-
  Confidential-computing GPUs run real models in production today at a throughput penalty
  ZK cannot approach. The side-channel literature against TEEs is also extensive. Both
  facts are load-bearing, and the honest position is uncomfortable.
papers: [tee-confidential-llm, optimistic-tee-rollups]
status: reviewed
paradigm: tee
---

A trusted execution environment runs the model on hardware that attests, cryptographically,
to what it ran. The verifier checks a signature chain rooted in a manufacturer's key and
concludes: this binary, on genuine hardware, produced this output.

It is worth being blunt about the position TEEs occupy in this SoK, because the ZK
literature has a habit of dismissing them in a subordinate clause and moving on. Of every
approach catalogued on this site, **TEEs are the one being used, right now, by people
paying money for verifiable and confidential inference.** [[tee-confidential-llm]]
benchmarks confidential LLM inference across CPU and GPU TEEs. On a single device, running
a model that fits on it, the overhead is a rounding error next to ZK's:

{{ table:alternatives_to_zk cols=platform,overhead_percent,overhead_metric }}

It is not a general constant, and the paper is candid about that. Confidential H100
instances lose RDMA and GPUdirect, so every byte crosses the CPU and multi-GPU serving —
which is to say, serving anything that does not fit on one card — falls off a cliff. The
H100's HBM is left unencrypted, where the CPU TEEs it is measured against do encrypt
memory, and the authors expect the successor part that closes the gap to cost more. And
the network protection they say is required on top of both CPU and GPU TEEs costs far more
than the headline. The engineering conversation is over for the single-GPU case and open
above it. Vendors advertise the same thing in production — Phala's GPU TEEs are offered
for inference on OpenRouter — though that is their claim, not this paper's. There is no
zkML deployment of comparable scale, and there will not be one soon.

So the case for zkML cannot be that TEEs are impractical. They are the practical option.
The case has to be made on the assumption, and it has to be made honestly.

## What you are assuming

Trusting a TEE means trusting, at minimum:

1. **The hardware vendor's key infrastructure.** The attestation is a signature. Someone
   holds that signing key, and that someone can attest to anything.
2. **The silicon's isolation guarantees**, as implemented — not as specified. The paper
   cited above documents a live instance of the gap: the confidential H100 leaves its HBM
   unencrypted, which the CPU TEEs it is compared against do not.
3. **The attestation chain and its revocation infrastructure**, including the vendor's
   ability and willingness to revoke a compromised part.
4. **The measured binary being the thing you think it is** — attestation proves *what*
   ran, not that what ran was correct or honest. A TEE will faithfully attest to a
   backdoored model.

Point 4 is routinely elided and it is the important one for this SoK's purposes. A TEE
tells you the provider ran *the binary whose hash is X*. Whether the weights inside that
binary are the weights they advertised is a question about what got measured, and it is
exactly the model-substitution question that verifiable inference exists to answer. A TEE
can answer it — if the attestation covers the weights. Whether it does, or whether the
measurement stops at the container that loads them, is a deployment choice — and it is the
choice that decides whether the TEE answers that question at all.

## The side-channel literature is not a talking point

It is also not a refutation, and both overstatements are common.

The academic record against production TEEs is long and it is real: a decade of
microarchitectural, speculative-execution, power, and interface attacks have repeatedly
extracted secrets from enclaves that were specified to protect them. Any security engineer
who tells you a TEE is a black box has not been reading. The pattern is that TEEs get
broken, get patched, and get broken again, and the assumption you are making is not "this
hardware is secure" but "**this hardware is secure enough, for now, against the adversary
I have, and I will get told when it isn't.**"

That is a defensible assumption for a great many threat models. It is a completely
untenable one for a few:

- **An adversary with physical access to the machine.** In decentralised inference — the
  setting most of this literature is written for — the node operator *is* the adversary
  and *does* have physical access. This is close to the worst case for a TEE and it is
  precisely the deployment being proposed.
- **A verifier who must not trust a single US corporation.** A regulator, a foreign
  government, a competitor.
- **A guarantee that must survive the hardware.** An attestation is worth what the signing
  key is worth on the day you check it. A ZK proof verified today is still verified in ten
  years; an attestation from a vendor whose key has since leaked is worth nothing,
  retroactively.

That last one is, to us, the sharpest distinction and the least discussed. **ZK proofs are
durable and attestations are perishable.** For an on-chain settlement or a compliance
artefact that must hold up in a dispute years later, that difference is the entire ball
game — and it has nothing to do with throughput.

:::debate  Does the side-channel record actually change the deployment decision?
The ZK partisan's argument: TEEs are broken on a schedule, and building a trust
infrastructure on them is building on sand. The TEE partisan's reply: every TEE break has
been patched, none has produced a mass compromise of confidential-computing workloads in
the wild, and meanwhile zkML has produced no deployments at all — a perfect security record
that nobody is relying on is not a security record. Both are right. The disagreement is not
really about side channels; it is about whether a probabilistic, patchable, vendor-mediated
guarantee is *the same kind of thing* as a cryptographic one. It is not, and that is the
whole point — but "not the same kind of thing" does not automatically mean "worse for your
threat model."
:::

## The synthesis is where the interesting work is

[[optimistic-tee-rollups]] is the most thoughtful construction in this section precisely
because it does not treat the question as a binary. It uses H100 confidential computing
for throughput, optimistic fraud proofs for finality, and — the good idea — **stochastic ZK
spot-checks** whose sole purpose is to bound the risk that the hardware was compromised.

Read that as a design pattern rather than a paper: ZK is used *not* as the verification
mechanism but as an **auditor of the verification mechanism**, sampled at a rate you can
afford. You are no longer paying ZK's overhead on every inference; you are paying it on a
random few, and what you buy is a probabilistic guarantee that the TEE is not lying to
you. That converts an unbounded hardware-trust assumption into a quantified one.

It is the same structural move as [sampling-based verification](/alternatives/sampling/),
one level up: **you do not need to prove everything to make cheating irrational.**

:::gap  Nobody has stated the composed guarantee
[[optimistic-tee-rollups]] combines hardware attestation, an economic challenge game, and
a sampled cryptographic check. What is the resulting soundness statement? What must an
adversary corrupt, and with what probability do they succeed? The paper describes the
architecture; it does not state the theorem. Neither does any other hybrid in this SoK.
:::

## The honest summary

If your verifier will accept an NVIDIA attestation, zero knowledge is an extraordinarily
expensive way to buy a confidence you already had — and the overhead table above is not
close, even once every caveat above it is paid. The reason to reach for ZK is not that TEEs
don't work. It is that **some verifiers cannot make that assumption**, and no amount of
engineering will make them able to. That is a small set of deployments. It is not an empty
one, and it contains most of the ones people write papers about.
