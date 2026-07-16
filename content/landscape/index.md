---
title: The landscape — who is building this
section: landscape
slug: index
order: 10
lede: >-
  The org-level cut of the same field the rest of this site covers paper-by-paper: which
  companies and research teams work each cell. A high-recall map, not a benchmark — it holds
  no performance numbers, and an org's presence here verifies nothing it ships.
status: reviewed
---

Three cautions before the tables. The genuinely focused, independent **"zkML company" set is
small** — probably under 15. Most of the apparent size comes from general-purpose ZK
infrastructure adding an ML path, FHE companies adding encrypted inference, MPC networks adding
"private AI," and decentralized-AI projects using "verifiable AI" as language. Appearing here does
**not** mean an org ships a cryptographic-inference product. And the boundary is porous — academic
prototypes appear continually and private companies operate without public materials, so "all" is
not claimable. Current as of **July 2026**.

:::note  Read the table as a map, not a leaderboard
The rows are not comparable to each other. They differ in *guarantee* (integrity vs. model-privacy
vs. input-privacy), in *what is proven* (one forward pass vs. a full multi-token generation), in
*bit width* (a free accuracy-for-speed knob most papers don't report), and in *hardware*. Every
benchmark number lives on the linked paper page, with its caveats attached — never in this table.
:::

:::intuition  The privacy column has three distinct meanings
Conflating them is the single most common error in this space. **Integrity** hides nothing — model,
input and output are all public, and you get only a proof the computation was honest. **Hides
model** is genuine zero-knowledge: the weights are secret from whoever runs inference (protecting a
model owner's IP). **Hides input** is client-side: the user's input is secret and the model is
public (protecting a user's biometric).

*Hides-model and hides-input are inverses, not degrees of one thing.* A system hiding the model
(zkLLM, zkGPT) and one hiding the input ([[bionetta]], World ID) live in opposite threat models,
and their costs are not comparable.
:::

{{ landscape }}

Two of these rows barely overlap in personnel with the others, and it mirrors the site's
[headline finding](graph): the hides-model line ([[zkllm]], [[zkgpt]], [[jolt-atlas]]) and the
hides-input line ([[bionetta]], World) are different companies solving inverse problems — the same
split the citation graph found between the proving and privacy literatures.

## FHE inference

The one dedicated player is **Zama** (Concrete ML / TFHE — scikit-learn, PyTorch and transformer
components compiled to run on encrypted inputs). Beyond it the category is *inference-capable PET
vendors*, *foundational libraries*, and *acceleration hardware* — mostly **not** FHE-ML products in
the Concrete ML sense:

- **Platforms / PET vendors:** Duality (hybrid FHE/MPC, OpenFHE), Inpher, CryptoLab (HEaaN/CKKS),
  Desilo.
- **Foundational research / libraries:** Microsoft Research (SEAL, CryptoNets — the ancestor of
  encrypted-NN inference, CHET/EVA), IBM (HElib), Google (FHE transpiler), OpenFHE consortium,
  OpenMined (TenSEAL).
- **Acceleration:** Intel (HERACLES), Niobium, Cornami, Optalysys (optical); AWS for encrypted
  SageMaker integration.
- **Broader PET, some ML:** Enveil, Cosmian, Fortanix, Decentriq, Roseman Labs, Secretarium,
  Galois, Samsung SDS, Ant Group / SecretFlow. TripleBlind and Privitar are uncertain-status.

## MPC / garbled-circuit inference

Where the academic systems on the [private inference](private-inference) page come from, plus a
thinner company layer:

- **Companies:** Nillion (AIVM / Fission — clearest MPC-private-inference effort; some nilAI is
  **TEE**, so distinguish per product), Arcium, Partisia, SecretFlow / Ant Group; Duality / Inpher /
  Roseman Labs / Decentriq on the hybrid side.
- **Research:** Meta (CrypTen), Microsoft Research (EzPC / CrypTFlow / SecureNN / SIRNN — the
  lineage the 2PC papers build on), Intel Labs (TinyGarble), AWS; RBC + Waterloo.
- **Academic groups:** UC Berkeley (Gazelle), CMU (Delphi), MSR India, UCSD, USC, Cornell
  (HummingBird), Waterloo, KU Leuven/COSIC, Aarhus, Bristol (MP-SPDZ), TU Darmstadt, ETH, EPFL,
  SNU/CryptoLab, Tokyo/NTT, CUHK/Tsinghua (MPCFormer). Systems from this ecosystem — many sharing
  author groups, so a name is *not* a distinct team: SecureML, MiniONN, Gazelle, SecureNN,
  Chameleon, ABY3, Delphi, CrypTFlow2, SIRNN, Cheetah, Falcon, MPCFormer, Iron, BumbleBee, PUMA,
  CipherGPT, Sigma, Mosformer.

## Adjacent — *not counted*

These use "verifiable" / "private" AI language but rely principally on incentives, replication,
consensus, optimistic verification, or TEEs — the [alternatives-to-ZK](alternatives) trust models,
not a ZK/MPC/FHE inference path: **Gensyn, Ritual** (TEE base layer, ZK/FHE opt-in), **Ora/opML,
Allora, Bittensor, Gonka, Prime Intellect, Golem, io.net, Akash, Phala, Marlin/Oyster, EigenLayer
AI AVSs, Hyperbolic, Lilypad, Aethir, Nosana.** Federated-learning-only, differential-privacy-only,
and ordinary confidential-computing vendors don't meet the bar unless they also expose an explicit
ZK/MPC/FHE path.

:::audit  Audit-firm read — who to watch
Specialized-ZK short list: **Lagrange, EZKL, the former Modulus team (now TFH), Giza, Mina,
Polyhedra, ICME, Bionetta/Distributed Lab, PSE**, with **RISC Zero** as enabling infra. Privacy
side: **Zama, Nillion, Duality, Inpher, Microsoft Research, Ant/SecretFlow, OpenMined, Partisia,
Arcium, CryptoLab**, plus the **Intel/Niobium/Cornami/Optalysys** acceleration layer. Strongest
clusters: general zkML compilers (ezkl, DeepProve, Orion, Mina zkML); specialized proof systems for
large models (Lagrange, former Modulus, Polyhedra, academic GKR/sumcheck); FHE-ML (overwhelmingly
Zama, then Duality + OpenFHE); MPC LLM inference (Nillion, the MSR-associated lines, SecretFlow,
several academic systems).
:::
