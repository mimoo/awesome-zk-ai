# zkAI — Zero-Knowledge Proofs for AI

A running index of papers and results on proving AI computation in zero knowledge, organized
by **what is being proven**. Following the taxonomy in the
[ZKP-VML survey](https://arxiv.org/abs/2502.18535), that splits three ways:

| Objective | Claim being proven | Cost |
|---|---|---|
| **[Inference](#inference)** | "This model produced this output on this input." | Cheapest |
| **[Testing](#testing)** | "This model achieves this accuracy on this dataset." | Middle |
| **[Training](#training)** | "This model is the result of correctly training on this data." | Hardest |
| **[Properties](#proving-properties-not-computation)** | "This model is fair / uncensored / trained on licensed data." | Varies |

The fourth is ours, not the survey's — fairness and audit proofs are a claim about a *model*,
not about a *computation*, and they don't fit the other three.

Three more sections cover the context those results sit in:

- **[Soundness & attacks](#soundness--attacks)** — what breaks, what's merely unanalyzed. Start here if you're auditing.
- **[Alternatives to ZK](#alternatives-to-zero-knowledge)** — opML, TEEs, and when 1000× overhead isn't worth paying.
- **[Sampling-based verification](#sampling-based--statistical-verification)** — commit the trace, open a random sample; trade soundness for milliseconds.
- **[Adjacent trust models](#training-without-zk-proofs-adjacent-trust-models)** — verifiable federated learning and private (MPC/HE) training.

Structured benchmark data lives in [`papers.yml`](./papers.yml) so it can be plotted. The
tables below are a human-readable view of the same data.

> **Provenance matters here.** Every number is tagged in the YAML with `numbers_source:
> primary` (read from the paper) or `numbers_source: survey` (taken secondhand from the
> survey's Tables IV–VI). Author lists carry `authors_verified`. Where the survey and the
> primary paper disagree, both numbers are recorded and the conflict is flagged — there are
> [three such conflicts](#known-conflicts) so far.
>
> **[Quantization is a confounder](#quantization-the-hidden-variable), not a footnote.** Most
> of these systems do not state their bit width. Throughput numbers across different bit
> widths are not comparable.

---

## Inference

Proving that a forward pass — or, increasingly, a full multi-token generation — was executed
correctly against a committed model.

### LLMs

| System | Venue / Date | Model | Params | Context | Proving | Proof size | Verify | HW |
|---|---|---|---|---|---|---|---|---|
| [DeepProve](https://eprint.iacr.org/2026/1112) | ePrint · May 2026 | GPT-2 | 124M | 512 | **174 tok/min** | 7–27 MB | 1.2 s | Ryzen 9 7950X3D, 16c |
| [DeepProve](https://eprint.iacr.org/2026/1112) | ePrint · May 2026 | Gemma 3 | 270M | 512 | **86 tok/min** | 16–54 MB | 3.7 s | Ryzen 9 7950X3D, 16c |
| [DeepProve](https://eprint.iacr.org/2026/1112) *(distributed)* | ePrint · May 2026 | GPT-2 | 124M | 512 | **1855 tok/min** | — | — | 17× Ryzen 9 7950X3D |
| [Jolt Atlas](https://arxiv.org/abs/2602.17452) | arXiv · Feb 2026 | nanoGPT | 0.25M | — | 14 s/proof (≈4.3 tok/min\*) | — | 0.52 s | M3 laptop |
| [Jolt Atlas](https://arxiv.org/abs/2602.17452) | arXiv · Feb 2026 | GPT-2 | 125M | **?** | 38 s/proof (tok/min **not derivable**) | — | — | M3 laptop |
| [zkGPT](https://eprint.iacr.org/2025/1184) | USENIX Sec '25 | GPT-2 | 124M | 32 | 21.8 s/pass (≈2.8 tok/min\*) | **101 KB** | 0.35 s | 16-core CPU |
| [zkPyTorch](https://eprint.iacr.org/2025/535) | ePrint · Mar 2025 | Llama-3 8B | **8B** | — | 150 s/token (0.4 tok/min) | — | — | 1 CPU core |
| [zkLLM](https://arxiv.org/abs/2404.16109) | CCS '24 | LLaMA-2 13B | **13B** | — | <15 min (full inference) | <200 KB† | <3 s | A100 |
| [Artemis](https://arxiv.org/abs/2409.12055) | arXiv · Sep 2024 | GPT-2 | 124M | — | 200–240 min | 15 KB | **14 ms** | 128 vCPU |
| [Lu et al.](https://eprint.iacr.org/2024/1057) | 2024 | GPT-2 | 117M | — | 287 s‡ | 4.5 GB | 63 s | 8-core CPU |
| [ZKML](https://ddkang.github.io/papers/2024/zkml-eurosys.pdf) | EuroSys '24 | GPT-2 | 124M | — | 3652 s‡ | 28 KB | 18.7 s | 128 vCPU |
| [NANOZK](https://arxiv.org/abs/2603.18046) ⚠️ | arXiv · Mar 2026 | Transformer block (d=128) | — | — | 43 s/block | 5.5 KB/layer | 24 ms | ? |

\* **Derived, not reported** — `60 / (single-proof seconds)`. A forward-pass proving time is
not the same quantity as sustained decode throughput. See [caveats](#open-questions-for-the-graph).
† zkLLM's paper says <200 KB; the survey says <10 KB. ‡ Conflicts with zkGPT's own
measurements. ⚠️ NANOZK is an unreviewed single-author preprint whose abstract contains an
unsubstituted `METHOD` placeholder — treat with suspicion.

### Vision, trees, and operators

| System | Venue / Date | Model | Params | Proving | Proof size | Verify |
|---|---|---|---|---|---|---|
| [zkPyTorch](https://eprint.iacr.org/2025/535) | ePrint · Mar 2025 | VGG-16 (CIFAR-10) | 15.2M | 2.2 s/image | — | — |
| [zkCNN](https://eprint.iacr.org/2021/673) | CCS '21 | VGG16 | 15M | 88.3 s | 341 KB | 59.3 ms |
| [Mystique](https://eprint.iacr.org/2021/730) | USENIX Sec '21 | ResNet-101 | 42.5M | 262 s | 0.99 GB | — |
| [vCNN](https://eprint.iacr.org/2020/584) | 2020 | VGG16 | — | 8 hours | — | 19.4 s |
| [ZEN](https://eprint.iacr.org/2021/087) | 2021 | ShallowNet / LeNet | — | 147–4710 s | **192 bytes** | 0.02–0.47 s |
| [Hao et al.](https://www.usenix.org/conference/usenixsecurity24/presentation/hao) | USENIX Sec '24 | ReLU / Softmax *(operators)* | — | 2.1 s / 87 s | 30 MB / 816 MB | — |
| [ZKTorch](https://arxiv.org/abs/2507.07031) | arXiv · Jul 2025 | *(compiler)* | — | up to 6× faster than ZKML | ≥3× smaller | — |
| [SpaGKR](https://eprint.iacr.org/2024/1018) | ePrint · Jun 2024 | Sparse / ternary nets | — | 45× (sparsity) × ~5× (ternary) | — | — |
| [ezkl](https://github.com/zkonduit/ezkl) | *(no paper)* | ONNX graphs | — | 237 s on nanoGPT | — | 0.34 s |

### Notes per system

**[DeepProve](https://eprint.iacr.org/2026/1112)** — Gailly, Hishon-Rezaizadeh, T. Liu,
Mainardi, Papadopoulos, Papamanthou, Pappas, Srinivasan, Youell, Y. Zhang (Lagrange Labs,
HKUST, Yale, UIUC). Sum-check plus lookup arguments over HyperKZG and BaseFold. The claim to
care about is *end-to-end*: it proves all generated tokens of a prompt, not one forward pass,
which is what makes its tok/min figure directly meaningful. Covers multi-head attention and
LayerNorm for GPT-2, and grouped-query attention, RMSNorm and RoPE for Gemma 3. 20–60× faster
than prior work. GPT-2 varies by machine and commitment: 174 TPM (BaseFold, secondary),
146 TPM (HyperKZG, same machine), 127 TPM (primary). Open source:
[`Lagrange-Labs/deep-prove`](https://github.com/Lagrange-Labs/deep-prove).

**[Jolt Atlas](https://arxiv.org/abs/2602.17452)** — Benno, Centelles, Douchet, Gibran (ICME
Labs). Extends Jolt's lookup-centric approach but applies it directly to ONNX tensor
operations instead of emulating CPU instructions, so there is no RISC-V trace. ZK via the
BlindFold technique; neural teleportation shrinks lookup tables. The selling point is *where*
it proves: everything runs on a MacBook Pro (M3, 16 GB), targeting on-device verification.
Against ezkl on nanoGPT: 14 s vs 237 s proving (~17×), before ezkl's >400 s of key generation.
§6.2 ("GPT-2, 125M parameters") *does* carry measurements — Table 3, floated onto p.19 past the
§7 heading: ~38 s end-to-end (sum-check ~16 s, witness gen ~7.5 s, reduction opening ~7 s,
commitment ~3.5 s, HyperKZG ~3 s). But it reports no sequence length, token count, proof size,
verifier time, or accuracy, so that 38 s is **not comparable** to any tok/min figure above.

**[zkGPT](https://eprint.iacr.org/2025/1184)** — Qu, Sun, X. Liu, Lu, Guo, Chen, J. Zhang (NUS,
HKUST). USENIX Security 2025. GKR + sum-check made non-interactive via Fiat–Shamir, Hyrax
commitments over BN254. Two ideas carry the speedup: *constraint fusion* (merging rounding
constraints across adjacent operators — ~30% fewer in attention, ~50% in GeLU) and *circuit
squeeze* (breaking GKR's layer-wise dependency to flatten the circuit into a wider, shallower
shape). Result-as-witness for Softmax, LayerNorm, GeLU. 185× faster than ZKML and 5.1× faster
than Lu et al. with 23,000× less communication — **all on CPU only**. The 101 KB proof is the
smallest of any GPT-2 system here.

**[zkPyTorch](https://eprint.iacr.org/2025/535)** — Xie, Lu, Fang, Wang, Z. Zhang, Jia, Song,
J. Zhang (Polyhedra, UC Berkeley, NUS). A **compiler, not a protocol** — and worth reading as
such: its three contributions are the ONNX-**DAG** preprocessor (handles residuals, and inserts
auxiliary witnesses — division as quotient + a `remainder < divisor` proof, softmax/sqrt as
lookup tables), **ZKP-friendly static integer quantization** (4-bit weights/activations, 8-bit
intermediates, sized to fit **M61** instead of BN254), and a three-level circuit optimizer whose
model level *batches* inference (a proof only verifies the output, so the autoregressive token
dependency is decoupled and all tokens prove in one circuit). Crucially, at the primitive level
it **reuses zkCNN's convolution and zkLLM's non-linear lookups rather than inventing new
per-operator arguments** — so it is not a source of novel protocols, and the Fiat–Shamir/GKR
caveat that applies to Expander applies here. The headline numbers are **single-CPU-core**:
VGG-16 (15.2M, a CIFAR-sized variant — not standard 138M) at 2.2 s/image, Llama-3 8B at
150 s/token; multi-core CPU/GPU is a separate circuit-level optimization. Accuracy: <0.03%
CIFAR-10 loss on VGG/ResNet; 99.32% cosine similarity on Llama-3 (a weaker claim than perplexity).

**[zkLLM](https://arxiv.org/abs/2404.16109)** — Sun, Li, H. Zhang (Waterloo). CCS 2024. The GPU
baseline everyone compares against, and still the largest model proven end-to-end (LLaMA-2 13B
in under 15 minutes). Contributes *tlookup*, a parallelized lookup argument for non-arithmetic
tensor ops with no asymptotic overhead, and *zkAttn*, a bespoke argument for attention.
Fully-parallelized CUDA. Note the proof-size conflict flagged above.

**[ZKML](https://ddkang.github.io/papers/2024/zkml-eurosys.pdf)** (Chen, Waiwitlikhit, Stoica,
Kang; EuroSys '24) and its successor **[ZKTorch](https://arxiv.org/abs/2507.07031)** (Chen,
Tang, Kang) — optimizing compilers from model graphs to halo2 / accumulated basic blocks.
ZKML is the standard non-interactive GPT-2 baseline that zkGPT beats by 185×. ZKTorch
generalizes to "basic blocks" proved by specialized protocols and accumulated via a parallel
extension of Mira.

**[Artemis / Apollo](https://arxiv.org/abs/2409.12055)** — Lycklama, Viand, Avramov, Küchler,
Hithnawi. Attacks a *different* bottleneck than everyone else: the consistency checks on
committed model parameters and input data, which can dominate cost on large models. Cuts
commitment-verification overhead on VGG from 11.5× to 1.1×. Apollo is the KZG/white-box
variant; Artemis is generic over homomorphic polynomial commitments (black-box), so it works
in transparent Halo2/IPA settings with no trusted setup.

**[zkCNN](https://eprint.iacr.org/2021/673)** — T. Liu, Xie, Y. Zhang. CCS 2021. The
foundational sumcheck-for-convolution result: linear prover time for 2D convolution
(asymptotically faster than computing the convolution directly) and an O(N) sumcheck for FFT,
beating the conventional O(N log N). 1264× faster than prior schemes. Also proves accuracy on
a public dataset, so it straddles inference and testing.

**[Mystique](https://eprint.iacr.org/2021/730)**, **[vCNN](https://eprint.iacr.org/2020/584)**,
**[ZEN](https://eprint.iacr.org/2021/087)** — the 2020–21 generation. Worth including mostly to
show the trajectory: vCNN needed 8 hours for VGG16 where zkCNN needs 88 seconds. Mystique's
~1 GB proofs are the price of a VOLE-based interactive protocol; ZEN's 192-byte proofs are the
price of Groth16's trusted setup and a much smaller model.

---

## Testing

Proving that a committed model achieves a *claimed accuracy* on a dataset — a claim about the
model's quality rather than about one output. This is the category most often forgotten, and
it is the one that matters for benchmark integrity and model-marketplace claims.

| System | Venue / Date | Model | Proving | Proof size | Verify |
|---|---|---|---|---|---|
| [zkDT](https://dl.acm.org/doi/10.1145/3372297.3417278) | CCS '20 | Decision tree (1029 nodes, 5000 samples) | 250 s | 287 KB | 15.6 s |
| [pvCNN](https://arxiv.org/abs/2201.09186) | 2023 | LeNet-5 (MNIST) | 1448.8 s | 351 MB | 54 s |
| [ZEN](https://eprint.iacr.org/2021/087) (`ZENacc`) | 2021 | ShallowNet / LeNet | 147–4710 s | 192 bytes | 0.02–0.47 s |
| [zkCNN](https://eprint.iacr.org/2021/673) | CCS '21 | VGG16, 20 images | 88.3 s | 341 KB | 59.3 ms |
| [Artemis](https://arxiv.org/abs/2409.12055) | 2024 | GPT-2 | 200–240 min | 15 KB | 14 ms |

**[zkDT](https://dl.acm.org/doi/10.1145/3372297.3417278)** — the key insight is that test
samples share nodes on a decision tree, so all inference paths across the whole test set can
be validated in one step rather than per-sample. Circuit size is O(d + h) in path length and
feature count. Later revisited through **matrix lookup arguments** (cq+, zkcq+, cq++), which
encode the tree as a committed matrix and prove the reached leaf's row belongs to it —
removing the prover's dependence on tree size entirely.

**[pvCNN](https://arxiv.org/abs/2201.09186)** — hybrid of homomorphic encryption, collaborative
inference and zk-SNARKs, using Quadratic Matrix Programs to encode convolution and aggregate
proofs across test instances. Splits the model into private and public components.

---

## Training

Proving a model is the honest result of running a training procedure on committed data —
strictly harder than inference, since every backward pass and weight update must also be
proven.

| System | Venue / Date | Model | Params | Proving | Proof size | Verify | HW |
|---|---|---|---|---|---|---|---|
| [zkDL](https://arxiv.org/abs/2307.16273) | TIFS '24 | 8-layer DNN | 10M | **0.86 s/batch** (bs 64) | 33 bytes⚠️ | 0.19 s | A100 |
| [Kaizen](https://eprint.iacr.org/2024/162) | CCS '24 | VGG-11 | 10M | 15 min/iteration (bs 16) | 1.63 MB | 130 ms | 8× Xeon |
| [VeriLoRA](https://arxiv.org/abs/2508.21393) | NDSS '26 | LLaMA-2 | **13B** | <600 s/sample (bs 1) | — | <4 s | A100 80GB |
| [zkPoT](https://eprint.iacr.org/2023/1345) (Garg et al.) | CCS '23 | Logistic regression | — | 4208 s total | <350 MB | 26.5 s | 512 GB GCP |
| [zkMLaaS](https://ieeexplore.ieee.org/document/10001017) | GLOBECOM '22 | Logistic regression | — | 2.2 s | 24.1 MB | 5 ms | 8× V100 |
| [VeriML](https://arxiv.org/abs/1909.06961) | TPDS '21 | Neural network (bs 32) | — | 12 s | — | 0.99 s | i5 desktop |
| [Optimum Vicinity](https://eprint.iacr.org/2025/053) | CCS '25 | Convex models | — | *246× smaller circuits* | — | — | — |
| [ZKBoost](https://eprint.iacr.org/2026/202) | ePrint · Feb 2026 | XGBoost | — | *not yet extracted* | — | — | — |

⚠️ zkDL's 33-byte proof size comes from the survey's Table IV and looks implausible; verify
against the paper before citing.

**[zkDL](https://arxiv.org/abs/2307.16273)** — Sun, Bai, Li, H. Zhang. The scale leader for
DNN training proofs, and the trick is structural: `FAC4DNN` aggregates proofs across layers
*and across training steps* without being constrained by their sequential order, which is what
makes sub-second per-batch proving possible. `zkReLU` handles ReLU and its backpropagation.
CUDA implementation, [open source](https://github.com/SafeAILab/zkDL).

**[Kaizen](https://eprint.iacr.org/2024/162)** — Abbaszadeh, Pappas, Katz, Papadopoulos (UMD,
HKUST). Recursive composition of GKR-style proofs with aggregatable polynomial commitments.
The prover trains via mini-batch gradient descent and emits a commitment plus succinct proof
each iteration, with the iteration count not fixed in advance. Crucially, **proof size and
verifier time are independent of both iteration count and dataset size**. 24× faster than
generic recursive proofs.

**[Optimum Vicinity](https://eprint.iacr.org/2025/053)** — Tan, Gascón, Meiklejohn, Raykova,
X. Wang, Luo. CCS 2025. **The most interesting conceptual departure in this whole list.**
Instead of proving that every training step executed correctly, it proves the *result* lies
within a bounded distance of the mathematical optimum — turning a statement about a long
computation into a statement about a short one. Boolean circuits up to 246× smaller, arithmetic
circuits up to 5× smaller than step-by-step zkPoT. Restricted to models expressible as convex
optimization problems, so it does not (yet) reach deep nets.

**[zkPoT](https://eprint.iacr.org/2023/1345)** (Garg, Goel, Jha, Mahloujifar, Mahmoody,
Policharla, M. Wang; CCS '23) — the paper that formalized the zkPoT security definition,
combining MPC-in-the-head with zkSNARKs. Only instantiated for logistic regression; the
contribution is the definition and the feasibility experiment, not scale.

**[ZKBoost](https://eprint.iacr.org/2026/202)** — Melissaris, Polychroniadou, Takahashi, Weng,
Xu (J.P. Morgan AI Research, ASU, CNRS). First zkPoT for XGBoost, and a useful corrective:
verifiable training is not only about deep nets, and gradient-boosted trees are what most
tabular and finance production models actually are. Also fixes a security gap in prior ZK
training proofs. Fixed-point XGBoost matches standard XGBoost accuracy within 1%.

**[VeriML](https://arxiv.org/abs/1909.06961)** and **[zkMLaaS](https://ieeexplore.ieee.org/document/10001017)**
— the sampling-based ancestors. Neither proves every iteration; they commit to iteration
inputs/outputs and let the verifier challenge a random subset. Cheap, but a weaker guarantee.

**[VeriLoRA / zkLoRA](https://arxiv.org/abs/2508.21393)** — claims the first end-to-end ZKP for
LoRA fine-tuning, covering forward propagation, backward gradients and LoRA weight updates,
on LLaMA-2 up to 13B. ⚠️ Numbers above are from the survey's Table IV; the PDF has not been
read directly.

---

---

## Training without ZK proofs: adjacent trust models

Everything in [Training](#training) above produces a **succinct proof a stranger can check**.
The systems below relax that — and the relaxations are *different from each other*, which is
the whole point of the section. Keeping them here rather than in the training table is
deliberate: **their runtimes are not proving times**, and plotting them on the same axes would
be a category error.

Three distinct guarantees, easy to conflate:

| | Hides the data? | Proves computation correct? | Who can verify? |
|---|---|---|---|
| **zkPoT** (Kaizen, zkDL) | ✅ | ✅ the whole training run | anyone |
| **Verifiable FL** (RoFL, ACORN, EIFFeL) | ✅ | ⚠️ only *properties* of updates | the server / peers |
| **Private training** (PriFT) | ✅ | ❌ nothing | nobody |

### Verifiable federated learning & secure aggregation

Nobody here proves gradient descent ran correctly. They prove either that a client's update is
*well-formed* (within a norm bound, in range) or that the *aggregator* combined updates
honestly — the two halves of the same problem, attacked from opposite ends.

| System | Venue | Uses ZK? | What's actually proven |
|---|---|---|---|
| [Prio](https://crypto.stanford.edu/prio/) / Prio+ | NSDI '17 | ✅ SNIPs | Each client's submitted value is well-formed. The ancestor of this cluster. |
| [EIFFeL](https://arxiv.org/abs/2112.12727) | CCS '22 | ✅ SNIP-style | An arbitrary public predicate holds on each update; malformed updates dropped. |
| [RoFL](https://arxiv.org/abs/2107.03311) | S&P '23 | ✅ ZK range proofs | Client updates satisfy L2/L∞ norm bounds. |
| [ACORN](https://eprint.iacr.org/2022/1461) | USENIX Sec '23 | ✅ ZK validation | Client inputs satisfy L0/L2/L∞ bounds. 2–8× faster clients than Bell et al. |
| [zkFL](https://arxiv.org/abs/2310.02554) | 2023 | ✅ | The **aggregator** aggregated honestly — the dual of RoFL/ACORN. |
| [Trusted Model Aggregation](https://ieeexplore.ieee.org/document/10669208/) | TPDS '24 | ✅ | Aggregation integrity under Byzantine adversaries. |
| [RiseFL](https://www.comp.nus.edu.sg/~ooibc/risefl-20230901.pdf) | 2023 | ✅ | Targets the ZK cost that makes RoFL expensive. |
| [ByzSFL](https://arxiv.org/abs/2501.06953) | 2025 | ✅ | Not yet read. |
| [**PRoVeFL**](https://arxiv.org/abs/2607.06612) | arXiv · Jul 2026 | ❌ | Server-checks-server, via MK-FHE + discrete-log commitments. |

**[PRoVeFL](https://arxiv.org/abs/2607.06612)** — Kasyap, Pradhan, Atmaca, Cormode, Maple.
Multi-key FHE (Ring-LWE) plus discrete-log commitments; peer servers check each other's
aggregation arithmetic with bilinear pairwise checks, sound as long as ≥1 server is honest.
**It contains no zero-knowledge proofs** — the strings "zero-knowledge", "ZKP" and "SNARK"
appear nowhere in the text. Its "verifiability" is neither succinct nor publicly verifiable.
Benchmarked on LeNet5 (62k), ResNet-18 (273k — suspiciously small for ResNet-18, likely a
reduced variant) and an LSTM (818k), on a 112-CPU Xeon. Aggregation wallclock at 200 clients:
~2000 s (Krum), ~400 s (Trimmed-Mean), ~20 s (FLTrust); communication 0.001–26 GB. **Those are
per-round aggregation costs, not proving times.**

Two author overlaps worth noticing: RoFL shares its authors with
[Artemis](https://arxiv.org/abs/2409.12055) (Lycklama, Viand, Küchler, Hithnawi), and ACORN
shares Gascón, Meiklejohn and Raykova with
[Optimum Vicinity](https://eprint.iacr.org/2025/053). The same two groups are working both the
zkPoT and the secure-aggregation sides of verifiable training.

### Private training, no verifiability

Encrypt the data during training. Nobody proves anything — a malicious party can still compute
the wrong function, silently. This is an **orthogonal axis** to everything else in this repo.

**[PriFT](https://eprint.iacr.org/2026/1381)** — Ma, Makri, Zisaric (LIACS, Leiden).
ePrint 2026/1381, July 2026. Uses a transformer as a frozen feature extractor, then trains a
small network on the privacy-protected features. Supports *fully-private* training (encrypted
end-to-end) and *semi-private* (labels decrypted during training for speed). Its real
contribution is a clean head-to-head of the two dominant secure-computation approaches on one
real task, using off-the-shelf libraries (Crypten for MPC, TenSEAL for HE): **MPC beats HE**,
especially in the semi-private setting, where it runs ~3× faster than fully-private, with
accuracy close to plaintext. Open source. ⚠️ The PDF is behind Cloudflare and its reference
list has not been extracted.

Adjacent private-fine-tuning work found alongside it — *not confirmed to be PriFT's citations*:
[PrivTuner](https://arxiv.org/abs/2410.00433) (HE + LoRA),
[Private LoRA with HE](https://arxiv.org/abs/2505.07329),
[CryptPEFT](https://arxiv.org/abs/2508.12264),
[Encryption-Friendly LLM Architecture](https://arxiv.org/abs/2410.02486). The Private-LoRA-with-HE
paper is a useful contrast pair with [VeriLoRA](https://arxiv.org/abs/2508.21393): same
workload, opposite guarantee — one hides the data, the other proves the computation.

---

## Adjacent: provenance, not computation

Cheaper, weaker claims about training that avoid proving the optimization itself.

- [ZKPROV](https://arxiv.org/abs/2506.20915) — proves *which dataset* a model was trained on, without proving the training computation.
- [Verifiable Fine-Tuning](https://arxiv.org/abs/2510.16830) — binds training proofs to a dataset commitment and a declared policy.

---

## Proving properties, not computation

A **fourth verification objective** the survey's taxonomy misses entirely. Inference, testing
and training all prove a *computation* ran correctly. These prove a *model* — or its training
data — has some **property**: fairness, provenance, absence of censorship. The model stays
confidential. This is the compliance-driven use case, and the EU AI Act is why it's growing.

| System | Venue | Property proven | Scale |
|---|---|---|---|
| [FairProof](https://arxiv.org/abs/2402.12572) | ICML '24 | Local fairness certificate for fully-connected NNs | Gnark impl |
| [FairZK](https://arxiv.org/abs/2505.07997) | IEEE S&P '25 | Group fairness of logistic regression + DNNs | **47M params, 343 s** |
| [OATH](https://arxiv.org/abs/2410.02777) | 2024 | Online group fairness under distribution shift | cut-and-choose |
| [zkAudit](https://arxiv.org/abs/2404.04500) | ICML '24 | Arbitrary properties of hidden weights *and* hidden data | ImageNet-scale |
| [Show Me You Comply](https://arxiv.org/abs/2510.26576) | 2025 | Regulatory compliance of the whole system | not yet read |

**[FairZK](https://arxiv.org/abs/2505.07997)** — Zhang, Dong, Kose, Shen, Y. Zhang. The
scalability unlock is conceptual, not cryptographic: it derives fairness bounds from the
**model parameters plus aggregated input statistics**, rather than by proving inference over a
specific dataset. Sidestepping per-example inference proofs is why it reaches 47M parameters
and 343 s where inference-based fairness proofs stall — a 3.1×–1789× prover improvement.

**[zkAudit](https://arxiv.org/abs/2404.04500)** — Waiwitlikhit, Stoica, Sun, Hashimoto, Kang.
Two phases, and the first one **cross-lists into [Training](#training)**: `ZKAudit-T` proves
the model was trained by SGD on a committed dataset (a zkPoT), then `ZKAudit-I` audits
arbitrary user-defined properties over the hidden data and weights — copyright, censorship
detection, counterfactuals. Weights stay secret but **the architecture is public**, which is
exactly the mitigation the [Fiat–Shamir open question](#soundness--attacks) below turns on.

The author graph is small and worth noticing: FairProof is Yadav, **Roy Chowdhury** (EIFFeL),
**Boneh** (Prio), Chaudhuri. FairZK includes **Yupeng Zhang** (zkCNN, DeepProve). The people
building verifiable FL, zkPoT and fairness proofs are largely the same people.

---

## Soundness & attacks

Every result in this repo is downstream of an argument system, and argument systems break.
Nothing below is a demonstrated break of a deployed zkML system — but the distance between
"no known break" and "actually analyzed" is exactly where audit work lives. Entries are tagged
by status so that distinction stays sharp.

| Finding | Status | What it touches |
|---|---|---|
| [Fiat–Shamir attacks on GKR](https://eprint.iacr.org/2025/118) (CRYPTO '25) | ⚠️ **Proven attack** *(on adversarially-chosen circuits)* | zkGPT, DeepProve, zkPyTorch, zkCNN, zkLLM, SpaGKR, Kaizen |
| [Halo2 query collision](https://blog.zksecurity.xyz/posts/halo2-query-collision/) | 🐛 **Implementation bug**, fixed | ezkl, ZKML |
| [ZKBoost](https://eprint.iacr.org/2026/202) fixing prior zkPoT | ⚠️ Claimed vuln in prior work | unidentified zkPoT protocol |
| [SoK: SNARK vulnerabilities](https://arxiv.org/abs/2402.15293) | 📊 Taxonomy of 141 real bugs | every circuit here |
| Quantization / result-as-witness | ❓ **Open question** — our observation, not a bug | zkGPT-style designs |

### The Fiat–Shamir result, stated precisely

[**How to Prove False Statements: Practical Attacks on Fiat–Shamir**](https://eprint.iacr.org/2025/118)
— Khovratovich, Rothblum, Soukhanov. CRYPTO 2025. It attacks **GKR compiled to a
non-interactive argument via Fiat–Shamir**, which is the construction underneath nearly every
system in the inference table. Two attacks: an *adaptive* one that produces accepting proofs
of false statements for a specific circuit, and a *functional-equivalence* one that, given any
circuit `C` and any output `y`, constructs a functionally equivalent `C*` admitting an
accepting proof that `C*` outputs `y`.

**The caveat is load-bearing and must not be dropped.** The attack requires the *attacker* to
choose or modify the circuit. The paper explicitly says security depends on "the specific
implementation of the circuit `C`, rather than just its functionality," and that the attack
does **not** apply to fixed, honestly-chosen circuits in standard deployments. Non-adaptive
variants need either very large depth or extra assumptions. **This is not a break of any
deployed zkML system.**

What makes it worth a section anyway: **in MLaaS, the prover is the model owner, and the model
is the circuit.** If a deployment commits to *weights* but never independently pins the
*architecture*, then "construct a functionally equivalent circuit that proves the output I
want" is structurally close to the model-substitution attack that NANOZK and DeepProve exist to
prevent. Whether any specific system here satisfies the attack's preconditions **has not been
analyzed**. That analysis is the highest-value open item in this repo. Note that zkAudit
already makes the architecture public while hiding only the weights — which is precisely the
shape of the mitigation.

### The rest

**[Halo2 query collision](https://blog.zksecurity.xyz/posts/halo2-query-collision/)** (Suneal
Gong, July 2025) — in Halo2's multipoint opening argument, querying the same polynomial at the
same point twice causes one evaluation to be **silently ignored**, letting a malicious prover
forge evaluations and pass verification. The root cause is domain wrapping: with `2^k` rows,
`Rotation(0)` and `Rotation(2^k)` are the same point but the frontend doesn't deduplicate them.
Disclosed to Zcash, PSE, Axiom and **ezkl**; fixed; no production deployments compromised. Two
systems in our inference tables sit on halo2, so zkML inherits this class of bug wholesale.

**[SoK: What don't we know?](https://arxiv.org/abs/2402.15293)** — Chaliasos, Ernstberger,
Theodore, Wong, Jahanara, Livshits. A taxonomy built from **141 real SNARK vulnerabilities**.
The lesson that transfers: what is proven correct on paper routinely fails in implementation,
and **under-constrained circuits are the most common and most severe class**. Every zkML system
here is a circuit.

**Quantization as an audit surface** — ❓ *our own observation; no paper, no known bug.*
Quantized zkML pushes correctness onto range checks. zkGPT's *result-as-witness* paradigm has
the prover supply the output of Softmax/LayerNorm/GeLU as a witness and then prove it lies in
range — so soundness rests entirely on those range constraints being complete. An
under-constrained range check in a result-as-witness design would let a prover assert an
arbitrary non-linear output. Given the SoK finding above, this is where we'd look first.

---

## Alternatives to zero knowledge

zkML costs **>1000× plain inference**. This section exists so the repo doesn't quietly assume
that's always worth paying. Compare on **trust assumption**, not on speed.

| Approach | Trust assumption | Overhead | Buys you |
|---|---|---|---|
| **zkML** (everything above) | Mathematics | **>1000×** | Public verifiability, no hardware trust, privacy |
| [opML](https://arxiv.org/abs/2401.17555) | Economic — *AnyTrust*, one honest validator | ~1× | Runs 7B LLaMA on a **CPU-only PC** |
| [TEEs](https://arxiv.org/abs/2509.18886) (H100 CC) | Hardware vendor + attestation chain | **4–8%** | Real-time interactive inference |
| [Proof of Sampling](https://arxiv.org/abs/2405.00295) | Nash equilibrium, rational validators | ~1× | Cheapest; weakest guarantee |
| [OTR](https://arxiv.org/abs/2512.20176) | Hardware + economic, ZK spot-checks | ~1× | Sub-second provisional finality |
| [zk-OPML](https://link.springer.com/article/10.1007/s44443-026-00573-1) / [opp/ai](https://arxiv.org/abs/2402.15006) | Hybrid | between | ZK only where it's needed |

**[opML](https://arxiv.org/abs/2401.17555)** — Conway, So, Yu, Wong (Hyper Oracle). The
strongest argument against zkML as a default. It never generates a proof unless challenged, so
7B-LLaMA runs on a standard PC with no GPU. Security is an *AnyTrust* assumption: any single
honest validator can force correct behavior. Note the inversion worth internalizing — **when
the model is large enough that ZK proving exceeds the challenge period, opML reaches finality
first.** What it gives up: privacy, non-interactivity, and verifiability for anyone not
watching the chain.

**TEEs** — the number that frames the entire field: **4–8% throughput penalty** on NVIDIA H100
confidential computing, shrinking as batch size grows, versus >1000× for ZK. If your verifier
will trust NVIDIA's attestation, ZK is an extremely expensive way to buy the same confidence.
ZK's answer is that *some verifiers cannot make that assumption* — an adversarial counterparty,
a regulator, a public blockchain — and that TEEs have side channels. Already in production
(Phala GPU TEEs on OpenRouter).

**[Optimistic TEE-Rollups](https://arxiv.org/abs/2512.20176)** is the most interesting
synthesis: H100 TEEs for throughput, optimistic fraud proofs for finality, and **stochastic ZK
spot-checks** to bound hardware-compromise risk. ZK used where it's cheap rather than
everywhere. [opp/ai](https://arxiv.org/abs/2402.15006) splits differently — zkML for the
privacy-sensitive submodel, opML for the rest.

**When is ZK actually the right tool?** When the verifier is adversarial or anonymous, when the
model or the input must stay private, when verification must be non-interactive and permanent
(on-chain), or when no hardware root of trust is acceptable. Otherwise, one of the rows above
is probably cheaper by three orders of magnitude.

---

## Sampling-based / statistical verification

A distinct line of work that sits **between** full zkML and the no-proof alternatives above. It
*does* use cryptographic commitments — but instead of proving the whole computation, it commits
to the execution trace and **opens only a random sample of it**. That deliberately trades
soundness for speed: security is statistical and game-theoretic, not the ≈2⁻¹⁰⁰ cryptographic
soundness of the zkML sections.

The line has ancestry already elsewhere in this repo — [VeriML](#training) challenges random
*training iterations*, and [Proof of Sampling](#alternatives-to-zero-knowledge) re-executes
under a Nash-equilibrium incentive. What's new in 2026 is applying trace-sampling to **LLM/DNN
inference**.

**[Towards Verifiable AI with Lightweight Cryptographic Proofs of Inference](https://eprint.iacr.org/2026/541)**
([arXiv](https://arxiv.org/abs/2603.19025)) — Anchuri, Campanelli, Cesaretti, Gennaro, Jois,
Kayman, Ozdemir. ePrint 2026/541, March 2026. The prover commits to the inference execution
trace with Merkle-tree vector commitments, then reveals only sampled entries along random paths
from output back to input. This drops proving from the **order of minutes to the order of
milliseconds** versus cryptographic proof systems. Security rests on *trace separation between
functionally dissimilar models* plus a **rational prover facing penalties on detection**, with
detection probability amplifying over repeated queries. Evaluated on ResNet-18 and Llama-2-7B
against gradient-descent reconstruction, inverse transforms and logit swapping — none evaded
detection. That the authors include SNARK researchers (Campanelli, Gennaro) makes the
soundness/efficiency trade a deliberate design point, not an oversight.

> ⚠️ **Do not plot this next to zkML proving times as if the guarantee were the same.** A
> millisecond "proof" that catches a cheater with some probability per query is not comparable
> to a 22-second proof that catches one with overwhelming probability. The honest comparison
> axis is *cost × (detection probability × penalty)*, not cost alone. This is the right tool
> for auditing and high-volume MLaaS where queries repeat; the wrong tool for one-shot on-chain
> settlement. **From an audit standpoint**, the load-bearing question is the concrete detection
> probability as a function of how many trace paths are opened, and how a rational prover
> optimizes against it — a statistical argument, not a cryptographic-soundness one.

---

## Secure / private inference on transformers (2PC · MPC · HE)

A **whole separate line** from everything above, and the easiest to confuse with it. These
systems answer a different question: not *"prove the model ran correctly"* but *"run the model
without either party seeing the other's secret."* A **client** holds the input, a **server**
holds the weights, and they jointly compute inference so the prompt stays hidden from the
server and the weights stay hidden from the client — using homomorphic encryption + secret
sharing + oblivious transfer. It's the inference analog of [PriFT](#training-without-zk-proofs-adjacent-trust-models).

**Three things make it orthogonal to the zkML atlas:**

| | zkML (the atlas) | Secure inference (this line) |
|---|---|---|
| Guarantee | **Correctness** (a proof) | **Privacy** during computation |
| Threat model | malicious prover | **semi-honest** counterparty — a malicious party can still compute the *wrong* function |
| Bottleneck | prover compute / memory; cheap non-interactive verify | **communication** — hundreds of GB over many interactive rounds |
| Scale reached | 8–13B | **BERT-class (~110M)** — 2PC comm cost caps it far lower |

The anchor number that captures the whole line: **Iron needs 280.99 GB of communication and
216 minutes for a single BERT-base (110M) inference** (reported by BOLT). No proof is produced;
you can't hand the result to a third party and have them trust it.

| System | Venue | Model | Approach | Result | PDF |
|---|---|---|---|---|---|
| [Iron](https://proceedings.neurips.cc/paper_files/paper/2022/hash/64e2449d74f84e5b1a5c96ba7b3d308e-Abstract-Conference.html) | NeurIPS '22 | BERT (Tiny–Large) | Hybrid HE/MPC; compact-packing HE matmul | 3–14× less comm than SIRNN | ✅ NeurIPS |
| [CipherGPT](https://eprint.iacr.org/2023/1147) | ePrint '23 | **GPT** | sVOLE matmul + spline GELU + secure top-K sampling | 6.2× matmul, 1.8× GELU vs SOTA | ✅ read |
| [BOLT](https://eprint.iacr.org/2023/1893) | IEEE S&P '24 | BERT-base | MPC + HE, ML-level opts | **10.91× less comm**, 4.8–9.5× faster than Iron | ✅ [encrypto.de](https://encrypto.de/papers/PZMZS24.pdf) |
| [Nimbus](https://arxiv.org/abs/2411.15707) | NeurIPS '24 | BERT-base | Outer-product matmul encoding + input-distribution poly-approx | 2.7–4.7× over SOTA; 0.08% acc loss | ✅ arXiv |
| [Bootstrapping…](https://eprint.iacr.org/2026/1255) | ePrint '26 | BERT | **FHE** (non-interactive, "NISTI") | 349.5 s, 16.1 MB / 256-batch | ✅ read |

### Per system

**[Iron](https://proceedings.neurips.cc/paper_files/paper/2022/hash/64e2449d74f84e5b1a5c96ba7b3d308e-Abstract-Conference.html)**
— Hao, H. Li, H. Chen, Xing, Xu, T. Zhang (UESTC / NTU), NeurIPS '22. The paper that *started*
private transformer inference. Hybrid HE/MPC: a custom HE matmul with a compact-packing trick
(√m× less communication than Cheetah's matrix-vector approach, ~8× on transformers), and
SIRNN-based OT protocols for Softmax/GELU/LayerNorm. Numerically precise, so it preserves
plaintext accuracy, and it hides *every* layer's intermediates (unlike THE-X, which leaks
non-linear-layer inputs to the client — Iron explicitly critiques that). It's also the
reference the rest improve on: 280.99 GB / 216 min for one BERT-base inference.

**[CipherGPT](https://eprint.iacr.org/2023/1147)** — Hou, J. Liu, J. Li, Y. Li, Lu, Hong, Ren
(Zhejiang / Ant), ePrint '23. The **GPT** member, and the one that's genuinely interesting for
*us*: it's the only paper in this line that tackles **autoregression and sampling**. Its sVOLE
matmul is customized for generation — each response word is one inference producing an
*unbalanced* matmul, and it combines them over subfield-VOLE. Its GELU is **spline-based** (one
LUT to pick an interval, then a per-interval linear function), beating both the multi-step
(Iron/SIRNN) and high-degree-polynomial (BOLT) approaches on precision (7.4×). And it gives the
**first secure top-K *sampling* protocol**. That's the exact capability the zkML side lacks —
recall [Jolt Atlas](./docs/index.html#/op/certify) proves a single forward pass with no decode
or sampling, while CipherGPT builds bespoke 2PC protocols for word-by-word generation and
stochastic top-K decode. 6.2× matmul speedup / 4.1× bandwidth over SOTA.

**[BOLT](https://eprint.iacr.org/2023/1893)** — Pang, Zhu, Möllering, Zheng, Schneider (CMU /
Berkeley / TU Darmstadt), IEEE S&P '24. MPC + HE with ML-level optimizations across matmul and
the non-linears; **10.91× less communication and 4.8–9.5× faster than Iron**, comparable
accuracy to float. [Open source](https://github.com/Clive2312/BOLT). It's the paper that pins
the Iron anchor number quoted above.

**[Nimbus](https://arxiv.org/abs/2411.15707)** — Z. Li, K. Yang, Tan, Lu, Wu, X. Wang, Yu, et
al. (SJTU / Ant / Northwestern), NeurIPS '24. The freshest 2PC result. Two ideas: a new matmul
encoding from an **outer-product insight** (2.9–12.5× over SOTA linear-layer protocols), and a
**low-degree polynomial approximation for GELU/Softmax that exploits the observed input
distribution** (2.9–4.0× over SOTA poly-approx, 0.08% accuracy loss). 2.7–4.7× end-to-end over
SOTA on BERT-base.

**[Bootstrapping is All You Need](https://eprint.iacr.org/2026/1255)** — Xiao, Ouyang, H. Zhang,
J. Zhang, J. Liu (Zhejiang), ePrint '26 — **the one you first linked, and it's a different
animal: FHE, not 2PC.** It calls the setting *NISTI* (Non-Interactive Secure Transformer
Inference): the client encrypts under CKKS, the server evaluates on ciphertext, no interaction.
Bootstrapping is the dominant cost (66.8% of runtime in the prior SOTA), so their *Functional
Bootstrapping* fuses operations into each bootstrap step — including a **functional S2C** that
folds linear layers (`y = xW + b`) into the slot-to-coefficient transform so they cost nothing
separately — plus a trigonometric-minimax (Remez) approximation for better worst-case precision
on non-linears. 349.5 s/query and **16.1 MB** (amortized over 256 inputs), 1.9× faster / 3× less
comms than SOTA. That 16 MB — versus the 2PC systems' *hundreds of GB* — is the whole FHE trade:
no interaction, paid for with heavy homomorphic compute. (Its benchmarked transformer uses DyT /
Dynamic Tanh in place of LayerNorm.)

**The cross-paradigm parallel worth keeping:** the *hard operators are the same in both worlds*.
**Softmax, GELU, LayerNorm** are the expensive non-linears everywhere — costly lookups/range-
checks in zkML, costly OT / polynomial-approximation / bootstrapping here — while matmul is
"easy." Nimbus's input-distribution-aware poly-approx and CipherGPT's spline GELU are the MPC
mirrors of the quantization and table-sizing tricks zkML uses on the very same operators.

> **PDF availability (you asked):** all five are now read from primary PDFs. **Iron, BOLT,
> Nimbus** came from open mirrors (NeurIPS / encrypto.de / arXiv). **CipherGPT** (eprint
> 2023/1147) and **Bootstrapping** (eprint 2026/1255) were **eprint-Cloudflare-blocked to my
> fetcher** — you dropped them into `~/Downloads` and I read them from there. Every entry is now
> `pdf_available: true`, `numbers_source: primary`.

None of this is in the interactive [operator atlas](./docs/index.html) — same reason as opML,
TEEs and sampling: it's a different paradigm (privacy, not verifiable operators), so it has no
per-operator column. It lives here and in `papers.yml` under `secure_inference_2pc`.

---

## Surveys

- **[A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning](https://arxiv.org/abs/2502.18535)**
  — Peng, Zhao, T. Wang, Liao, Lin, Y. Liu, Cao, Shi, Yang, S. Zhang. arXiv:2502.18535 · Feb
  2025; also in *Artificial Intelligence Review*. **This is a survey, not a system** — no
  original benchmarks, so it is excluded from the plots. Its value is Table VII, a timeline of
  30 systems from SafetyNets (2017.6) to VeriLoRA (2025.08), and Tables IV/V/VI giving proving
  time, verification time and proof size *with hardware* for training, testing and inference
  systems. Most of the older entries in this README are sourced from it.
- **[ZKP-based Verifiable Decentralized ML: A Comprehensive Survey](https://arxiv.org/abs/2310.14848)**
  — complementary, focused on federated/decentralized settings.

---

## Quantization: the hidden variable

Every system here quantizes — finite fields have no floats. But **bit width is a free
parameter that trades accuracy for proving speed, and most papers do not report it.** A
system claiming high throughput at 8 bits is not doing the same job as one claiming lower
throughput at 16 bits, and nothing in the tables above makes that visible.

### What each system actually does

| System | Bits | Scheme | Accuracy cost reported? |
|---|---|---|---|
| [zkGPT](https://eprint.iacr.org/2025/1184) | **16** | Affine `x = S(q−z)`, per-layer scale & zero-point | ✅ PPL +0.2/+0.4/+0.3 (WikiText-2 / PTB / LAMBADA) |
| [SpaGKR](https://eprint.iacr.org/2024/1018) | **~1.58** (ternary `{−1,0,1}`) | Ternary networks — eliminates multiplication | ❌ |
| [ZEN](https://eprint.iacr.org/2021/087) | ? | Proof-friendly quantization + stranded encoding | ⚠️ "preserves accuracy", no metric |
| [zkPyTorch](https://eprint.iacr.org/2025/535) | **4** (int-4 w/act, int-8 intermediates) | Symmetric per-tensor static, sized to fit M61 | ✅ <0.03% CIFAR-10 (VGG/ResNet); ⚠️ 99.32% cosine (Llama-3) |
| [zkCNN](https://eprint.iacr.org/2021/673) | ? | Affine `a = L(q−Z)` — the scheme zkGPT inherits | ❌ |
| [zkLLM](https://arxiv.org/abs/2404.16109) | ? | Fixed-point; zkAttn avoids bit-decomposition | ❌ |
| [DeepProve](https://eprint.iacr.org/2026/1112) | **12** | Symmetric affine PTQ, calibrated; non-power-of-2 scales; orthonormal outlier smoothing | ✅ PPL 49.49 vs 49.22 fp32 (WikiText-2), cosine 0.9966 |
| [Jolt Atlas](https://arxiv.org/abs/2602.17452) | **?** | Neural teleportation to shrink lookup tables | ⚠️ "preserves accuracy", no metric |
| [NANOZK](https://arxiv.org/abs/2603.18046) | ? | Lookup approximations | ⚠️ claims perplexity preserved *exactly* |

DeepProve's bit width is now resolved: **12 bits**, with a published perplexity delta. It is
the second system here (after zkGPT) to state bit width *and* accuracy cost, and notably it
reports accuracy from the same integer engine its prover consumes — a distinction it makes
pointedly about prior work.

Jolt Atlas remains unstated, and for its design that matters most: table size grows
exponentially in the lookup input's bit width. Its only precision mentions are incidental
(a τ=4 activation table "sufficient for 16-bit fixed-point activations"). Its teleportation
is by the authors' own admission **lossy**, bounded only in raw output units (<55 on a
128-scale fixed-point representation), never in model accuracy. There is no perplexity or
task-accuracy number for any model in that paper.

Note the bit-width direction of the DeepProve-vs-zkGPT gap: DeepProve runs at **12** bits and
zkGPT at **16**, so DeepProve's ~63× throughput advantage is *not* bit-width-normalized. It
also uses a 512-token context against zkGPT's 32, and certifies a full sequence rather than a
single token. Three confounds, all pushing the same way.

### Does lower precision really mean faster proving?

Directionally yes, and there are two published measurements:

- **[SpaGKR](https://eprint.iacr.org/2024/1018)**: ternary `{−1,0,1}` weights give a further
  **~5× proof-time reduction** (on top of 45× from exploiting sparsity in linear layers).
- **[ZEN](https://eprint.iacr.org/2021/087)**: proof-friendly quantization gives
  **5.43–22.19× fewer R1CS constraints** (avg 15.35×) versus a vanilla encoding.

But the effect is **not uniform across the circuit**, and this is the part worth internalizing
before treating bit width as a single throughput knob:

1. **Non-linear ops and range checks: exponential or linear in bits.** Lookup-based softmax,
   GeLU and range checks need a table indexed by the value, so table size grows as `O(2^b)`.
   zkGPT demonstrates the cliff concretely: merging a length-32 vector of 16-bit values into
   one lookup would need a table of `2^(16×32) = 2^512` entries, which is why it *rejects*
   aggressive constraint merging. Bit-decomposition approaches instead pay cost linear in `b`.
2. **Linear algebra (the matmuls): largely flat in bits.** In sum-check/GKR systems the prover
   cost of a matmul is field operations proportional to the *number of gates*, which depends
   on parameter count, not on `b` — so long as values fit in the field. Dropping 16→8 bits
   barely touches the matmul, which is where most of a transformer's FLOPs live.
3. **Except when it changes the field.** The real win from low precision is that it lets you
   choose a *small* field (zkPyTorch's M61) instead of a 254-bit curve field like zkGPT's
   BN254. That's a large constant factor across the *whole* circuit. zkLLM states the tension
   directly: matching float accuracy with fixed-point needs large bit widths, which forces
   operations over large finite fields.
4. **Ternary is a special case, not just "2-bit".** SpaGKR's ~5× comes substantially from
   `{−1,0,1}` weights *eliminating multiplications altogether* and inducing sparsity — a
   structural change, not merely a narrower integer. Don't extrapolate its 5× to "int2 gives
   5×" for an arbitrary system.

So the intuition holds — a 2-bit result should beat an 8-bit result — but the mechanism is
mostly *lookup tables, sparsity and field size*, not the matmuls, and the size of the win
depends on how much of the circuit is non-linear. A GKR system whose cost is dominated by
attention matmuls may see little benefit; a lookup-heavy system like Jolt Atlas should see a
lot.

### Consequence for the graph

Bit width belongs on the chart. Concretely: plot tok/min vs. parameter count, **size or shade
each point by bit width**, and hollow out the markers where the paper doesn't say. Points with
no accuracy claim attached (`accuracy_retention: null` in the YAML) deserve a visual warning
too — a throughput number with unbounded accuracy loss is not a result, since any system can
go arbitrarily fast by quantizing to garbage.

---

## Known conflicts

Where two sources disagree, both are in `papers.yml`. Do not silently pick one.

1. **zkLLM proof size** — paper says <200 KB; survey Table VI says <10 KB. Trust the paper.
2. **ZKML on GPT-2** — survey says 3652 s / 18.7 s / 28 KB; zkGPT's Table 3 measures
   4026 s / 12.1 s / 7.8 KB (32 threads). Different hardware, different configs.
3. **Lu et al. on GPT-2** — survey says 287.1 s / 63 s / 4.5 GB; zkGPT measures
   112.3 s / 31.4 s / 2.24 GB. zkGPT folds communication time into the prover time "for fair
   comparison," which VOLE-based schemes need.

Plus one internal implausibility: **zkDL's 33-byte proof** (survey Table IV) is smaller than a
single group element pair and should be checked against the paper.

---

## To review

Surfaced while compiling this list, not yet read. **No numbers from these are trustworthy
until someone reads the PDF.** The full backlog with dates is under `to_review:` in
`papers.yml`; highlights:

- **SafetyNets** (2017.6) — the oldest entry in the survey timeline; interactive proofs, no ZK.
- **[Kang et al.](https://openreview.net/pdf?id=GjNRF5VTfn)** (2022.10) — scaling up trustless DNN inference.
- **ezDPS** (2022.12) — proves the whole *data-processing pipeline*, not just the model.
- **SpaGKR** (2024.6) — sparsity-aware GKR; potentially relevant to MoE models.
- **[VeriLLM](https://arxiv.org/abs/2509.24257)** (2025.9) — publicly verifiable decentralized inference.
- **zk-OPML** — hybrid optimistic verification + ZKP over isolated ONNX operators.
- **[ZKProphet](https://arxiv.org/abs/2509.22684)** (2025.9) — ZK proving performance on GPUs. Infrastructure, but decides everything above.

---

## Open questions for the graph

Before plotting tok/min against parameter count, four things need resolving:

1. ~~**Gemma 3 variant is unconfirmed.**~~ **Resolved.** It is the **270M** variant ("GPT-2
   (124 million parameters) and Gemma 3 (270 million parameters)", §1.2). Hardware is also
   resolved: a 24-core EPYC 9254 / 504 GB *primary* machine and a 16-core Ryzen 9 7950X3D /
   128 GB *secondary* machine — and the headline 174/86 TPM come from the **secondary**
   (faster clock, fewer cores); the primary peaks at 127 / 64 TPM.
2. **The tok/min axis mixes two quantities.** DeepProve reports true multi-token decode
   throughput. zkGPT and ZKML report the cost of one proof, which we divided into 60. Either
   plot only reported figures, or shape/color the derived points differently.
   **Jolt Atlas's GPT-2 point cannot go on this axis at all**: the paper states no sequence
   length and no token count for its 38 s, and never discusses autoregression, so it is
   unknown whether 38 s buys one forward pass or a whole generation.
3. **Hardware is not held constant.** zkGPT is CPU-only (16-core Xeon), Jolt Atlas is a laptop
   (M3), zkLLM and zkDL are A100-class GPUs, ZKML and Artemis run on 128 vCPU / 1 TB machines.
   A cross-system tok/min comparison is at best indicative — zkGPT attributes its entire 30%
   gap to zkLLM to CPU-vs-GPU, not to the protocol.
4. **Proof size spans six orders of magnitude** (192 bytes for ZEN → 4.5 GB for Lu et al.) and
   tracks the proof system, not the model. Any proof-size chart needs a log axis and should be
   colored by proof system (Groth16 / Halo2 / GKR+sumcheck / VOLE), or it will just rediscover
   that VOLE proofs are big.
5. **Bit width is unreported for the *fastest laptop* system.** See
   [Quantization](#quantization-the-hidden-variable). DeepProve is now resolved at 12 bits
   with a published perplexity delta; Jolt Atlas still omits it. zkGPT uses a comparatively
   expensive 16 bits. So the DeepProve-vs-zkGPT gap is *partly* quantization (12 vs 16 bits),
   partly context (512 vs 32), and partly what is proven (full sequence vs one token) — the
   protocol contribution is smaller than 63× and nobody has isolated it.

### Highest-value next actions

- ~~Read DeepProve's full PDF for bit width, Gemma 3 variant, and hardware.~~ **Done**
  (2026-07-10); see [`docs/`](./docs/index.html) for the per-operator breakdown, and
  [`docs/jolt-atlas-from-source.md`](./docs/jolt-atlas-from-source.md) for the code-grounded
  Jolt Atlas internals + a consolidated **audit findings** table (the ZK path has several
  bindings not yet re-expressed as R1CS constraints — softmax's `operand_link` is skipped in ZK
  mode; tanh/erf/sigmoid and the standalone ONNX `Clamp` op are unproven passthroughs).
- **Verify Jolt Atlas's claim that DeepProve's open-source implementation "lacks lookup
  arguments" for `Gather` reads** (Jolt Atlas §1.3). DeepProve's *paper* does not need them —
  Protocol 6 makes embedding a sparse one-hot matmul the verifier checks locally. This is a
  concrete, checkable disagreement against
  [the repo](https://github.com/Lagrange-Labs/deep-prove).
- **Ask the Jolt Atlas authors what the 38 s covers** (sequence length, token count). Without
  it their headline GPT-2 result is unplottable and uncomparable.
- Extract ZKTorch's and ZKBoost's per-model benchmark tables.
- Verify zkDL's 33-byte proof size and zkLLM's 200 KB vs 10 KB discrepancy against the papers.
- Fill in the `authors_verified: false` entries before this is cited anywhere.
