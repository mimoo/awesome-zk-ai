# zkAI: Verifiable and Private AI

A systematization of knowledge on making AI **trustworthy**, from
[zkSecurity](https://zksecurity.xyz). The "zk" is historical: zero-knowledge proofs are one
technique here, not the scope.

The **[full SoK is a generated site](https://mimoo.github.io/awesome-zk-ai/)**, one page per
approach and one per paper, with every number rendered from the data and carrying its provenance.

## The map

The field is a **2×2**: *what phase* of the model's life you protect, and *what property* you want.
Each cell is served by several cryptographic (and non-cryptographic) approaches.

|  | **Verifiability** (*prove it was done right*) | **Privacy** (*hide the data/model during compute*) |
|---|---|---|
| **Inference** | [**Proving inference**](https://mimoo.github.io/awesome-zk-ai/zk-inference/): zkML. DeepProve, Jolt Atlas, zkPyTorch, zkGPT, zkLLM. | [**Private inference**](https://mimoo.github.io/awesome-zk-ai/private-inference/): 2PC/MPC/FHE. Iron, BOLT, CipherGPT, Nimbus. |
| **Training** | [**Proving training**](https://mimoo.github.io/awesome-zk-ai/zk-training/): zkPoT. Kaizen, zkDL, Optimum Vicinity, ZKBoost. | [**Private training**](https://mimoo.github.io/awesome-zk-ai/private-training/): MPC/HE. PriFT, and verifiable-FL hybrids. |

**The technique is not the axis.** A cell can be filled by ZK proofs, MPC, FHE, trusted hardware
(TEEs), optimistic fraud proofs, or trace **sampling**, at very different cost/trust trade-offs.
Verifiability buys *correctness* (a third party can trust the result) at ~1000× compute. Privacy
buys *confidentiality from a counterparty* (usually only a semi-honest one) at the price of heavy
communication or homomorphic compute. **They are different guarantees, and most systems give one,
not both.**

Within the verifiability column, the [ZKP-VML survey](https://arxiv.org/abs/2502.18535) splits
*what is being proven* three ways, and we add a fourth.

| Objective | Claim being proven | Cost |
|---|---|---|
| [**Inference**](https://mimoo.github.io/awesome-zk-ai/zk-inference/) | "This model produced this output on this input." | Cheapest |
| [**Testing**](https://mimoo.github.io/awesome-zk-ai/zk-testing/) | "This model achieves this accuracy on this dataset." | Middle |
| [**Training**](https://mimoo.github.io/awesome-zk-ai/zk-training/) | "This model is the result of correctly training on this data." | Hardest |
| [**Properties**](https://mimoo.github.io/awesome-zk-ai/properties/) | "This model is fair / uncensored / trained on licensed data." | Varies |

Properties (fairness, provenance, licensing) prove a claim about a *model*, not a *computation*, so
they do not fit the other three.

## The landscape: who is building this

The org-level cut of the same field, which companies and research teams work each cell, lives on the
site as **[The landscape](https://mimoo.github.io/awesome-zk-ai/landscape/)**. The genuinely focused,
independent **"zkML company" set is small** (under ~15). The rest of the field is general-purpose ZK
infrastructure adding an ML path, FHE companies adding encrypted inference, MPC networks adding
"private AI," and decentralized-AI projects using "verifiable AI" as language. The clusters worth
watching:

- **Specialized ZK inference:** Lagrange (DeepProve), EZKL, ICME (Jolt Atlas), Polyhedra (zkPyTorch),
  Distributed Lab/Rarimo (Bionetta), the former Modulus team (now Tools for Humanity), Giza, Mina,
  PSE. RISC Zero as enabling infrastructure.
- **FHE inference:** overwhelmingly Zama (Concrete ML), then Duality and the OpenFHE ecosystem.
  Microsoft Research (SEAL/CryptoNets) as the foundational lineage. Intel/Niobium/Cornami/Optalysys
  on acceleration.
- **MPC / 2PC inference:** Nillion, Arcium, Partisia, Ant/SecretFlow on the company side. The
  Microsoft-Research lines (EzPC/CrypTFlow/SIRNN) and a large academic ecosystem behind the systems.
- **Adjacent, *not* counted:** Gensyn, Ritual, Ora/opML, Bittensor, Phala, and other decentralized-AI
  projects relying on incentives, TEEs, or optimistic verification rather than a ZK/MPC/FHE inference
  path.

See the [site page](https://mimoo.github.io/awesome-zk-ai/landscape/) for the full org tables, the
privacy legend, and the audit-firm "who to watch" read.
