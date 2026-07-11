---
title: Jolt Atlas
paper: jolt-atlas
status: reviewed
---

## What is new

Three things, of which one is real, one is real-but-lossy, and one is real-but-unfinished.

**Prefix-suffix decomposition for small-space lookups** is the real one, and it is what the paper
should be read for. A lookup table's multilinear extension can be factored so that peak prover
memory drops from `O(|T|)` to roughly `O(|T|^{1/C})` at the cost of `C` streaming passes. This is
inherited from Jolt rather than invented here, but the application is the point: it is why a
GPT-2-sized model proves inside a laptop's memory budget at all, and *on-device proving* is a
genuinely different product from every other system in this collection.

**Neural teleportation** is the lossy one, and the paper is honest about it. TeleSparse's original
transform is two-sided and therefore exactly lossless — divide the pre-activation by λ, multiply
the output back, rescale the downstream weights. Jolt Atlas cannot afford the weight rescaling
(it would mean re-committing the weight tensors), so it uses a **one-sided approximation**: divide
the input by τ and simply do not compensate. The justification is that saturating activations spend
most of their range in the flat region where the transform is exact. It shrinks the activation
lookup table by the same factor. It is a clean trade and it is clearly labelled as lossy.

**BlindFold zero-knowledge** is the unfinished one. Jolt Atlas is the only system in the
proving-inference table that seriously attempts to *hide the witness* — Pedersen-committed
sum-check round polynomials, an R1CS encoding of the sum-check verifier, folded via Nova. That
ambition is correct and nobody else here has it. See below for what the code says about it.

## What it actually proves

For nanoGPT: a proof of a forward pass, with a verifying key, a proving key, a proof time and a
verify time. Clean.

For GPT-2: **nobody knows.** §6.2 consists of a heading and the words "JOLT Atlas (end-to-end)."
Table 3 (which LaTeX floated past the §7 heading onto p.19, which is why an earlier read of this
paper concluded there were no measurements at all) gives a five-stage prover breakdown and a total.
It gives **no sequence length, no token count, no proof size, no verifier time, and no accuracy**.
The paper never discusses autoregression or KV caching anywhere, so it is not knowable from the
text whether that total buys one forward pass or a whole generation. This is the single fact that
makes the GPT-2 result unplottable, and asking the authors what the number covers remains the
highest-value open item on this paper.

And there is no accuracy number for any model, at any bit width, anywhere in the paper. The
teleportation error is bounded only in *raw output units* on a fixed-point scale — never in
perplexity, never in task accuracy. A system whose central optimization is admittedly lossy, which
reports no accuracy metric, has not shown that the optimization is affordable.

## What to distrust

**The paper's central architectural claim is contradicted by the paper.** The abstract's
differentiator is that, unlike a zkVM, Jolt Atlas "applies [Jolt's lookup-centric approach] directly
to ONNX tensor operations," and §1.2 says it verifies "tensor relations directly at the multilinear
polynomial level" instead of "naively decomposing tensor operations into scalar computations."
Then §5.4 opens:

:::quote{src="Jolt Atlas" sec="§5.4, CPU trace vs Tensor trace"}
Currently, to verify tensor operations such as addition, multiplication, or ReLU, we begin with the
ONNX trace, decompose it into a CPU trace, and then feed this representation into the Jolt proof
system.
:::

*Currently.* The tensor-native proving that distinguishes Jolt Atlas from Jolt is aspirational. And
the architecture section confirms it: §2.2's Stage 3 includes a **`PCSumcheck`, which "[e]nsures each
execution step (PC) transitions to the next instruction (NextPC)"** — a program counter, in a system
whose selling point is that it has no CPU to emulate.

The same section ends: "the approach neither uses nor requires R1CS." Stage 1 of the proof DAG is
"the SpartanDag prov[ing] the outer R1CS constraint," and the whole of §3.2 is titled "R1CS Encoding
of the Sumcheck Verifier." Both sentences are in the same paper.

**The headline speedup over ezkl is not a measurement the authors made.** "We report ezkl timings for
the same model from their published benchmark" — a blog post, run on ezkl's hardware, which is not
the MacBook Pro M3 that Jolt Atlas ran on. The proof-time ratio compares a number the authors
measured against a number they read. The *key-generation* comparison is more defensible (ezkl's key
generation dwarfs its own proving time, and Jolt Atlas's is sub-second), but the headline is a
cross-hardware ratio against a vendor blog.

**The setup timings are suspicious on their face.** Table 1 reports verifying-key generation and
proving-key generation as *the same value to three decimal places*. That is either a coincidence, a
single measurement reported twice, or a placeholder.

**The bit width is unstated, and here it matters more than anywhere else in the repo.** Lookup-table
size is Jolt Atlas's dominant cost, and table size grows exponentially in the bit width of the
lookup input. Two incidental mentions in §4.2 — the τ=4 table is "sufficient for 16-bit fixed-point
activations," and the teleportation error is quoted on a 128-scale fixed-point representation — are
all there is. No calibration procedure, no scale-factor derivation, no zero-point discussion, no
sensitivity study. For a design where bit width *is* the cost model, that is a hole.

:::audit The ZK path is the weakest part, and the code says so
From [`site/legacy/jolt-atlas-from-source.md`](https://github.com/zksecurity/zkAI/blob/main/site/legacy/jolt-atlas-from-source.md), read against
`jolt-atlas@b20cdce`. The non-ZK path is tightly constrained by sum-checks, range checks and Shout
one-hot triples. The **BlindFold ZK path is younger, and several bindings that hold in the clear are
not re-expressed as R1CS constraints**:

- **Softmax's `operand_link` — the identity that pins the max — is intentionally skipped in ZK mode**,
  with no replacement constraint (`zk.rs:381-391`). This is a genuine under-constraint in the ZK
  softmax flow.
- The standalone ONNX `Clamp` operator is an **unproven passthrough** (`ops/clamp.rs`), and the
  tanh/erf/sigmoid clamps use dummy advice plus a prover-side `assert!`.
- Public-node reduced claims are compared in **cleartext only**; the code itself notes that "full
  soundness against an active malicious prover additionally requires an R1CS constraint … tracked as
  future work."
- The γ-weighted `joint_claim` scalar **leaks in cleartext** — an accepted, documented non-ZK leak,
  because no hiding HyperKZG exists.

None of this is a break of a shipped system; it is research code with self-documented TODOs. But
"Jolt Atlas achieves zero-knowledge through the BlindFold technique" is a claim about a code path
that is not yet fully constrained, and the SoK should say so before crediting Jolt Atlas as the one
system here that hides its witness.
:::

**Credit where due:** on-device proving is a real and under-served goal, the memory result that
enables it is genuine, and this is the only paper in the proving-inference cluster that treats
witness privacy as a first-class requirement rather than a footnote. The gap is between the ambition
and the current implementation, not in the ambition.
