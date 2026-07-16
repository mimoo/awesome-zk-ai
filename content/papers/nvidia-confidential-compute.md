---
title: NVIDIA Confidential Computing (Hopper H100)
paper: nvidia-confidential-compute
status: reviewed
---

## What is new

This is the **vendor's own spec for the hardware every other paper in this section runs on**. The
corpus already had two *third-party* views of H100 confidential computing, a benchmark study
([[tee-confidential-llm]]) and a rollup design that uses it as a component
([[optimistic-tee-rollups]]), but not the primary source describing the mechanism. This entry is
that source.

The H100 is the **first GPU with a trusted execution environment**. The whitepaper's claim is
narrow and mechanical: the GPU boots in a "CC-On" mode behind an on-die hardware **root of trust**,
runs only NVIDIA-signed firmware (secure + measured boot), and pairs with a CPU **confidential VM**
(AMD SEV-SNP or Intel TDX) over an encrypted, authenticated SPDM channel. Application data crosses
the PCIe boundary through an encrypted **bounce buffer**, the CPU VM encrypts it, the GPU copies it
inside its package, decrypts, computes, and re-encrypts on the way out. The output of the boot is an
**attestation report**: a cryptographically signed set of measurements of the GPU's identity and
firmware, checked against NVIDIA's Remote Attestation Service and a Reference Integrity Manifest.

## What it actually proves

An attestation proves **what ran, on genuine NVIDIA silicon**, a specific measured firmware/GPU
identity, signed by a key rooted in NVIDIA. That is all it proves. It says nothing about whether the
computation was *correct*, whether the operator was *honest*, or whether the weights inside the
attested binary are the ones advertised. This is the distinction that matters for this SoK, and it
is [threat-model point 4 on the TEEs page](../../alternatives/tees/): a TEE will faithfully attest to
a backdoored model. Whether the attestation even *covers* the weights, rather than stopping at the
container that loads them, is a deployment choice, and it is exactly the model-substitution question
verifiable inference exists to answer.

So it belongs in [Alternatives to ZK](../../alternatives/): it delivers **confidentiality plus
hardware-attested integrity**, at a throughput cost ZK cannot approach, in exchange for a trust
assumption ZK does not make.

## What to distrust

Two gaps, both load-bearing, and one of them the whitepaper concedes itself.

:::audit  The GPU side of the boundary is the weaker one
Independent measurement ([[tee-confidential-llm]], ETH Zurich) found the H100 leaves its **HBM
unencrypted**, where the CPU TEEs it interoperates with encrypt main memory. So the confidential-GPU
boundary is not uniformly as strong as the CPU boundary it extends, and NVIDIA expects the successor
part that closes the gap to cost more, memory encryption was a significant overhead on the CPU side.
The vendor spec asserts "confidentiality and integrity of code and data"; the independent number
qualifies where that holds.
:::

**Side channels are explicitly out of scope**, a documented exclusion in the whitepaper's own
threat model, not an oversight. That is precisely the attack class the academic TEE-breaking
literature has spent a decade demonstrating against CPU enclaves, and the honest reading is the one
on the [TEEs page](../../alternatives/tees/): the assumption is not "this hardware is secure" but
"secure enough, for now, against the adversary I have, and I will get told when it isn't."

The sharpest structural caveat has nothing to do with side channels. **An attestation is
perishable.** It is worth what NVIDIA's signing key is worth *on the day you check it*; if the key
later leaks or the part is later broken, past attestations are retroactively worthless. A ZK proof
verified today is still verified in ten years. For an on-chain settlement or a compliance artifact
that must survive a dispute years later, that difference is the whole argument, and it is
independent of the throughput numbers that dominate the discussion. See
[TEEs, the assumption that is actually deployed](../../alternatives/tees/) for where this lands.
