---
title: Threat models -- who learns what
section: private-inference
order: 20
lede: >-
  All five systems assume a semi-honest counterparty, all of them make the model
  architecture public, and none of them hide the output. The FHE one is not even
  playing the same game as the other four. Read the assumptions before the numbers.
papers: [iron, ciphergpt, bolt, nimbus, bootstrapping-fhe]
status: draft
---

## The parties

Two parties. The **server** holds a fine-tuned model and does not want to ship the weights. The
**client** holds an input -- a sentence, a medical record, a prompt -- and does not want the
server to see it. They run a protocol whose ideal functionality is: the client learns
$M(w, x)$, and neither party learns anything else. [[iron]], [[bolt]], [[ciphergpt]] and
[[nimbus]] all implement some version of this. [[bootstrapping-fhe]] implements something
adjacent, which we get to below.

## Assumption 1: the adversary is semi-honest

Every system in this section is proved secure against a **semi-honest** (honest-but-curious)
adversary. This is the single most load-bearing sentence on the page.

:::quote{src="Iron" sec="§2.1, Threat Model"}
Same as prior works [14, 17], we consider an honest-but-curious adversary that passively corrupts
either the server or the client, but not both. Such an adversary follows the protocol
specification exactly, but may try to learn more information than allowed (e.g., the model's
weights or inference inputs) via analyzing the data it receives.
:::

[[nimbus]] and [[bolt]] state the same assumption, and [[bolt]] is unusually candid about *why*:
the client has to trust the server somewhat because the server is providing the service, and
semi-honest protocols are the only ones that are fast enough. Both halves of that are honest, and
both are worth taking seriously rather than dismissing. But the consequence is unambiguous. **A
server that deviates from the protocol is outside the model.** It can compute a different
function, return garbage, return a competitor's cheaper model's answer, or run a backdoored set
of weights, and the protocol has no opinion. The client's privacy still holds. Its answer does not.

Note the asymmetry that this creates in practice: the party with the incentive to cheat (the
server, which is paid per query and wants to serve a smaller model) is the party the threat model
declines to constrain.

## Assumption 2: the architecture is public

The weights are secret. The *shape* of the model is not.

:::quote{src="Nimbus" sec="§2.1, Threat Model"}
As in all prior two-party inference protocols, the client is only allowed to learn the model's
architecture and inference result while the server gains no information about the client's input.
:::

[[bolt]] spells out how far this goes -- both parties know the parameter scales and the dimensions
of every layer, and in its BERT setting the tokenizer is frozen and public as well:

:::quote{src="BOLT" sec="§3, Threat Model"}
BOLT assumes that the model architecture is known to both parties. As is standard in all secure
computation protocols, we also do not aim to hide leakage of the inference result.
:::

This has two consequences that matter for an SoK.

First, the *protocol itself* is a function of the architecture. Layer dimensions determine the
packing, the ciphertext parameters, and the communication pattern. "Hiding the architecture" is
not a knob you can turn later.

Second -- and this is the interesting one -- **the privacy column makes the architecture public
while hiding the weights, which is exactly the configuration the verifiability column needs to
defend against the Fiat--Shamir attack on GKR** (see the Fiat–Shamir/GKR attack; the mitigation
is to pin the circuit rather than only the weights, which is what zkAudit does). The two columns
have converged on the same public/private split from opposite directions, and neither cites the
other for it.

## Assumption 3: the output leaks, by construction

Both [[bolt]] and [[iron]] state that they do not attempt to hide what can be inferred from the
inference result itself, and both point at differential privacy as the orthogonal tool for that.
This is correct and unavoidable -- the result has to be useful to somebody -- but it means model
extraction and membership inference against the served model are *entirely* out of scope. A client
who queries a private-inference service a few hundred thousand times learns roughly what a client
querying a plaintext API learns. 2PC protects the individual query, not the model.

## Assumption 4: the "client" is not a phone

The word "client" imports an intuition (a laptop, a browser, a handset) that does not survive
contact with these protocols. [[nimbus]] states the real deployment requirement outright, in the
course of arguing that its own design is not making things worse:

:::quote{src="Nimbus" sec="§3.3, Memory Impact of the COP Protocol"}
Due to the symmetric-computation characteristic of MPC as well as the expensive NTT cost brought
about by homomorphic encryption and decryption, existing secure-inference frameworks, e.g.,
[17, 14, 5, 26, 29, 42], require the client to be equipped with similar resources as the server,
including a powerful CPU (e.g., 64 vCPUs) and a large memory (e.g., 128 GB) [42, 26, 29].
:::

[[nimbus]] additionally has the server ship the *encrypted weights* to the client during a setup
phase, so the client must also store an encrypted copy of the entire model on disk and stream it
in as the layers are consumed. Whatever else this is, it is not an edge deployment. The realistic
picture of 2PC private inference is two datacenter machines that distrust each other, connected by
a network the paper gets to choose -- which is where the cost model page picks the story up.

## The FHE row is a different game

[[bootstrapping-fhe]] does not fit any of the above, and benchmarking it head-to-head against the
2PC systems is a category error. It calls its setting **NISTI** -- Non-Interactive Secure
Transformer Inference. The client encrypts its input under CKKS, sends it, and *leaves*. The
server evaluates the whole transformer homomorphically on ciphertext it can never read, and returns
a ciphertext the client decrypts.

|  | 2PC (Iron, BOLT, CipherGPT, Nimbus) | FHE / NISTI (Bootstrapping is All You Need) |
|---|---|---|
| Parties online during inference | both, for the whole run | client encrypts, then goes offline |
| Model weights | secret-shared / encrypted, jointly evaluated | **plaintext on the server**, applied to ciphertext |
| Client cost | peer-of-the-server compute, per inference | one encryption, one decryption |
| What the server sees | secret shares | ciphertext only |
| Dominant cost | communication and rounds | homomorphic compute (bootstrapping) |
| Adversary handled | semi-honest counterparty | a server that cannot decrypt |

The last row is the one people get wrong. FHE does not make the server *honest*; it makes it
*blind*. A NISTI server can return an encryption of anything it likes, and the client will decrypt
it and believe it. The correctness gap is exactly as wide as in the 2PC systems -- arguably wider,
because there is no interaction in which anything could be checked. [[bootstrapping-fhe]]'s own
framing of the interactive alternatives is about cost, not trust:

:::quote{src="Bootstrapping is All You Need" sec="§7, Related Work"}
In general, these interactive approaches suffer from high communication overhead and require
continuous client presence during inference.
:::

:::gap  What CKKS's approximate decryption implies here has not been analysed
CKKS is an *approximate* scheme: decryption returns the plaintext plus noise. In other settings
that has security consequences (the IND-CPA-D line of work), because a decryption result handed
back to an adversary carries information about the noise. Whether that matters for a NISTI service
where the client is the only decryptor -- and what happens when the client is the adversary --
is not discussed in [[bootstrapping-fhe]], and we have not found it treated anywhere else in the
private-transformer literature. Flagging it as unexamined rather than as a problem.
:::

## Summary

| | Iron | BOLT | CipherGPT | Nimbus | Bootstrapping-FHE |
|---|---|---|---|---|---|
| Setting | 2PC | 2PC | 2PC | 2PC | FHE, non-interactive |
| Adversary | semi-honest | semi-honest | semi-honest | semi-honest | server cannot decrypt |
| Model architecture | public | public | public | public | public |
| Model weights | hidden from client | hidden from client | hidden from client | hidden (encrypted, held by client) | never leave the server |
| Client input | hidden from server | hidden from server | hidden from server | hidden from server | hidden from server |
| Output correctness | **not guaranteed** | **not guaranteed** | **not guaranteed** | **not guaranteed** | **not guaranteed** |

The last row is the same in every column, and it is the row this section exists to make visible.
