# zkAI — Verifiable *and* Private AI

A systematization of knowledge on making AI **trustworthy**, from
[zkSecurity](https://zksecurity.xyz). The "zk" is historical: zero-knowledge proofs are one
technique here, not the scope.

**This README is the summary. The [full SoK is a generated site](https://mimoo.github.io/awesome-zk-ai/)** —
one page per approach and one per paper, with every number rendered live from the data and
carrying its provenance. The numbers, benchmark tables, and per-system deep-dives live there,
not here — a figure typed into this file is a figure that silently drifts.

## The map

The field is a **2×2** — *what phase* of the model's life you protect, and *what property* you
want. Each cell is served by several different cryptographic (and non-cryptographic) approaches.

|  | **Verifiability** — *prove it was done right* | **Privacy** — *hide the data/model during compute* |
|---|---|---|
| **Inference** | [**Proving inference**](https://mimoo.github.io/awesome-zk-ai/zk-inference/) — zkML: DeepProve, Jolt Atlas, zkPyTorch, zkGPT, zkLLM | [**Private inference**](https://mimoo.github.io/awesome-zk-ai/private-inference/) — 2PC/MPC/FHE: Iron, BOLT, CipherGPT, Nimbus |
| **Training** | [**Proving training**](https://mimoo.github.io/awesome-zk-ai/zk-training/) — zkPoT: Kaizen, zkDL, Optimum Vicinity, ZKBoost | [**Private training**](https://mimoo.github.io/awesome-zk-ai/private-training/) — MPC/HE: PriFT; and verifiable-FL hybrids |

**The technique is not the axis.** A cell can be filled by ZK proofs, MPC, FHE, trusted hardware
(TEEs), optimistic fraud proofs, or trace **sampling** — very different cost/trust trade-offs.
Verifiability buys *correctness* (a third party can trust the result) at ~1000× compute; privacy
buys *confidentiality from a counterparty* (usually only a semi-honest one) at the price of heavy
communication or homomorphic compute. **They are different guarantees — most systems give one,
not both.**

Within the verifiability column, the [ZKP-VML survey](https://arxiv.org/abs/2502.18535) splits
*what is being proven* three ways; we add a fourth.

| Objective | Claim being proven | Cost |
|---|---|---|
| [**Inference**](https://mimoo.github.io/awesome-zk-ai/zk-inference/) | "This model produced this output on this input." | Cheapest |
| [**Testing**](https://mimoo.github.io/awesome-zk-ai/zk-testing/) | "This model achieves this accuracy on this dataset." | Middle |
| [**Training**](https://mimoo.github.io/awesome-zk-ai/zk-training/) | "This model is the result of correctly training on this data." | Hardest |
| [**Properties**](https://mimoo.github.io/awesome-zk-ai/properties/) | "This model is fair / uncensored / trained on licensed data." | Varies |

The fourth is ours, not the survey's — fairness and audit proofs are a claim about a *model*, not
a *computation*, so they don't fit the other three.

The site is navigable two ways: the **left menu by cell** (the 2×2 above), and a **top menu by
cryptographic machinery** — Foundations · ZK · Secure Compute · TEE · Optimistic & Sampling — the
same corpus cut by technique instead of by guarantee.

## The headline finding

A citation graph built by `pdftotext`-ing every PDF
([`references/citation-graph.svg`](./references/citation-graph.svg), data in the
[`.yml`](./references/citation-graph.yml)) shows the two columns are **citation-disconnected**:
the zkML papers cite each other plus GKR/Lasso/zkCNN/Jolt; the MPC/FHE papers cite each other plus
Cheetah/SIRNN/THE-X — with essentially **zero edges crossing between them**. Two research
communities working the two columns of the same table, largely unaware of each other. The
[cross-paradigm parallel](https://mimoo.github.io/awesome-zk-ai/private-inference/) worth carrying:
the hard operators are *the same on both sides* — Softmax, GELU, LayerNorm are the expensive
non-linears everywhere, while matmul is "easy."

## The repository

```
papers.yml                    structured data. SOURCE OF TRUTH for every number.
operators.yml                 every operator in an LLM forward pass × how each scheme proves it.
references/<cell>/*.pdf        the PDFs we have actually read.
references/citation-graph.yml  edge A → B = "A's text cites B".
content/**/*.md                the prose. This is what you write.
site/sections.yml              the left-menu sections (cell) and top-menu paradigms.
site/build.py                  joins them → docs/
site/validate.py               fails the build when data and prose drift apart.
docs/                          GENERATED and GITIGNORED. Never hand-edit it.

make site     # build docs/ locally
make check    # integrity checks
make serve    # build + http://localhost:8000
```

`.github/workflows/site.yml` runs `make site && make check` on every push and deploys to Pages
from `main`. **The checks gate the deploy** — a SoK whose prose contradicts its data does not get
published.

**Two rules carry the whole design:**

- **Numbers live in `papers.yml`, never in prose.** Every figure on the site is rendered from the
  YAML at build time with a provenance dot. Markdown that hardcodes a benchmark is rejected by
  `make check`. (Quoting a paper's *own* claim to dispute it is exempt — that is the job.)
- **`null` is an answer.** A paper that doesn't state its bit width gets `bits: null` and a note.
  Never guess a null.

**Contributing:** read [`AGENTS.md`](./AGENTS.md) for the end-to-end procedure (find a paper's
code, clone it, run a workflow to learn how it *actually* works, then record it across
`papers.yml` + `references/` + the citation graph + a `content/papers/<id>.md` note), and
[`site/CONTENT.md`](./site/CONTENT.md) for the house prose style and the four-files-per-paper
contract. Prose is **dry and direct**; educative or expanding material goes in
callouts (`:::gap` / `:::debate` / `:::audit` / `:::intuition` / `:::quote`), not the body.

---

## The landscape — who is building this

The org-level cut of the same field: which companies and research teams work each cell. It now
lives on the site as **[The landscape](https://mimoo.github.io/awesome-zk-ai/landscape/)**, rendered
from [`orgs.yml`](./orgs.yml) — the ZK-core companies are structured rows whose `project` links to
the paper this repo has read, and whose `privacy` column distinguishes the three meanings that get
flattened in vendor decks (integrity / hides-model / hides-input).

The short version. The genuinely focused, independent **"zkML company" set is small** (under ~15);
the rest of the field is general-purpose ZK infra adding an ML path, FHE companies adding encrypted
inference, MPC networks adding "private AI," and decentralized-AI projects using "verifiable AI" as
language. The clusters worth watching:

- **Specialized ZK inference:** Lagrange (DeepProve), EZKL, ICME (Jolt Atlas), Polyhedra
  (zkPyTorch), Distributed Lab/Rarimo (Bionetta), the former Modulus team (now Tools for Humanity),
  Giza, Mina, PSE; RISC Zero as enabling infra.
- **FHE inference:** overwhelmingly Zama (Concrete ML), then Duality and the OpenFHE ecosystem;
  Microsoft Research (SEAL/CryptoNets) as the foundational lineage; Intel/Niobium/Cornami/Optalysys
  on acceleration.
- **MPC / 2PC inference:** Nillion, Arcium, Partisia, Ant/SecretFlow on the company side; the
  Microsoft-Research lines (EzPC/CrypTFlow/SIRNN) and a large academic ecosystem behind the systems.
- **Adjacent — *not* counted:** Gensyn, Ritual, Ora/opML, Bittensor, Phala, and other
  decentralized-AI projects relying on incentives / TEEs / optimistic verification rather than a
  ZK/MPC/FHE inference path.

See the [site page](https://mimoo.github.io/awesome-zk-ai/landscape/) for the full org tables, the
privacy legend, and the audit-firm "who to watch" read.
