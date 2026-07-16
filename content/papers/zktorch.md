---
title: ZKTorch
paper: zktorch
status: reviewed
---

## What is new

ZKTorch is the same group's successor to [[zkml-kang]], and the first thing to say is that it is not
an improved ZKML. **It throws the ZKML architecture away.** ZKML compiled a model into one large
Plonkish circuit and proved it with halo2. ZKTorch compiles an ONNX model into a DAG of twenty
**basic blocks**, `CQ`, `CQ2`, `CQLin`, `MatMul`, `Permute`, `Add`/`Sub`/`Mul`, `MaxProof`,
`OneToOne`, `Ordered`, and friends, each proved by its own KZG-based protocol, and then **folds the
per-block proofs together** with an accumulation scheme. Same compiler philosophy, entirely different
cryptography underneath.

**The cryptographic contribution is parallel accumulation.** ZKTorch builds on Mira, a pairing-based
folding scheme that accumulates a NARK proof into a running accumulator via a random linear
combination. Mira's formulation is inherently *sequential*, one fold per proof, `O(N)` deep, which
is a problem when a model compiles to on the order of a hundred thousand nodes. ZKTorch's fix is
clean and is the single idea to take from the paper: observe that a NARK proof **is** an accumulator
instance, the special case with `μ = 1` and `e = 0`, tag it with a bit, and generalize the folding
prover so it accumulates *any two* accumulator instances. Folding then becomes a Merkle-tree
reduction that parallelizes, rather than a chain. Mira itself only supplied accumulation for three of
the blocks; ZKTorch relaxes the algebraic tests of ten more so they fold too.

**The engineering contribution is coverage, and it is the more impressive half.** A transpiler covers
61 ONNX layers, the paper's key empirical observation is that the entire MLPerf Edge suite uses only
61 distinct operations, plus a rule-based graph compiler with seven rewrite rules (fuse the eight-node
ONNX GeLU subgraph into one table lookup; fuse multi-head matmul and RoPE to eliminate copy
constraints; a `CustomCNN` rule that views a `[B,I,H,W]` tensor as `[BHW, I]` so that convolution
becomes a stack of `CQLin`s plus additions that are *free* by KZG homomorphism, with no shape
operations at all). The result is the first ZK system to prove **every model in MLPerf Inference:
Edge v4.1**, including SDXL, 3D-UNet, RetinaNet and an RNN-T, on a single server. Nothing else in
this repo has that breadth, and breadth is a real contribution that the headline speedup buries.

## What it actually proves

**A single forward pass, on an input of one or two tokens.**

That sentence is the whole review, and it is not visible from the abstract. The evaluation's model
table lists the input dimensions alongside the parameter counts: BERT is proven on a **one-token**
input, GPT-J on a **two-token** input, LLaMA-2-7B on a **one-token** input, the RNN-T at sequence
length one, SDXL's text encoders on one token each. The proving times in the results table are the
cost of pushing that through the network once. They are not the cost of a sequence, they are not the
cost of a generation, and they are not comparable to [[deepprove]]'s multi-token decode throughput or
[[zkgpt]]'s 32-token context without saying so.

This has a direct consequence for our own data. [[deepprove]]'s comparison table records ZKTorch's
GPT-J result as a tokens-per-minute figure, which can only have been obtained by dividing the GPT-J
proving time by its two tokens. But those two tokens are a **prompt processed in one pass**, not two
decode steps, the paper never discusses autoregression or KV caching. The arithmetic is right and the
interpretation is a category error, and it is the reason `papers.yml` should carry ZKTorch's GPT-J row
as a forward pass over a two-token input rather than as a per-token cost.

Weights and activations are committed with KZG and stay private; the **architecture is public**, since
the DAG is compiled from the ONNX file the verifier also holds. Everything runs over BN254. Quantization
is fixed-point at a single low bit width for every model except GPT-J, which needs a slightly wider one
making ZKTorch one of the few systems in this repo that states its bit width at all.

**The accuracy table is not a proven claim, and cannot be one.** It reports ROUGE for GPT-J, F1 for
BERT, WER for the RNN-T and mAP for RetinaNet under ZKTorch's scaling, against MLPerf reference values,
to show that fixed-point conversion does not degrade the model. That is a *plaintext* quantization
study: a one-token BERT input cannot produce a SQuAD F1 score. It is the right experiment to run and it
is honestly labelled ("accuracy numbers with ZKTorch scaling"), but nobody should read it as ZKTorch
proving a benchmark result, that would be the testing objective, and no proof of it exists here.

**One structural gap worth naming: the decode step is exactly what does not fold.** `ArgMax` and `TopK`
are built from `OneToOne`, `Ordered` and `CopyConstraint`, three of the seven basic blocks that have
**no accumulation support**. The paper's compiler is explicitly written to avoid the non-foldable
blocks where it can, and it can, because none of its benchmarks sample a token. A system that actually
generated text would hit the unfoldable set on every step.

## What to distrust

**The two headline numbers are not measured the same way, and only one of them is a like-for-like
comparison.** The proving-time claim, a speedup over a general-purpose ZKML framework, is honest: it
is ZKTorch against [[zkml-kang]] on GPT-2, on identical hardware, and the paper says so. The
**proof-size claim is not a measurement.** It rests on a single ResNet-50 row against [[zkcnn]],
[[mystique]] and [[pvcnn]], and the table's own caption admits that zkCNN and pvCNN *never implemented
ResNet-50*, so their entries are the proof sizes those systems reported **for much smaller models**
(VGG-16 and LeNet-5 respectively). The substitution happens to be conservative, a bigger model would
only grow the baselines' proofs, but "at least 3× smaller than specialized protocols" is an inference
from three cells, two of which are for different models, and one of which ([[mystique]]) is a VOLE
system whose gigabyte proofs make any pairing-based scheme look good.

:::audit  ZKTorch's proofs are large, and the paper never compares them to ZKML's
The proof-size story the abstract tells is "at least 3× smaller than specialized protocols", measured
on a CNN. Now read the transformer rows of the end-to-end table: BERT at 4.88 MB, GPT-J at 6.54 MB,
LLaMA-2-7B at 22.85 MB. Then read [[zkml-kang]]'s own table: its distilled GPT-2 proof is 28,128 bytes
under the KZG backend, 16,512 under IPA.

The successor's transformer proofs are three orders of magnitude larger than its predecessor's. That is
not hidden, both numbers are printed, but the two are never put side by side, and the proof size for
the one model they *do* run head-to-head (GPT-2) is the one number §6.3 omits. Accumulation buys you a
*single* proof; it does not buy you a *small* one, and the move off halo2/KZG-Plonkish to folded
per-block NARKs cost roughly everything ZKML had on succinctness. A reader who takes "3× smaller
proofs" as the summary of ZKTorch will be badly wrong about what lands on the verifier.
:::

**Section 6.3 contradicts itself in a single paragraph.** In the course of explaining why they do not
benchmark against ezkl, the authors write:

:::quote{src="ZKTorch" sec="§6.3, Comparisons with Prior Work"}
Concretely, ezkl on nanoGPT small (1-million parameters, 26M flops) needs 966s to prove, while zkml on
a larger LLM GPT-2 (117-million parameters, 189M flops) requires only 159s to prove per token.
:::

Three problems. First, the same paragraph states that ZKML proves GPT-2 in 3601 s on their hardware, 
so "159 s per token" contradicts the number their own speedup is computed against, and nothing in the
paper reconciles them. Second, ZKML's GPT-2 is a **distilled** GPT-2 whose parameter count in ZKML's
own table is nowhere near 117M (the FLOP count matches; the parameter count does not). Third, the ezkl
figure is imported from elsewhere, on other hardware, as in [[jolt-atlas]]. The comparison that carries
the paper's headline is fine; this sentence, sitting next to it, is not, and it is the sentence a
reader is most likely to quote.

**The ablations do not line up.** Two tables report GPT-J proving time with a component disabled, one
for sequential-vs-parallel Mira, one for compiler-off, and they give **different** baselines while
landing on the same enabled value, so the two speedups (6.2× and 3.7×) are not additive, not
independent, and not explained. The prose describing the compiler ablation also cites the wrong table
number. None of this is dishonest; it does mean the attribution of the end-to-end gain between "better
folding" (cryptography) and "better graph rewriting" (engineering) is *not* actually established by the
experiments, and the honest answer to "was the improvement cryptographic or engineering?" is **both, in
proportions the paper does not pin down.**

**Composed soundness is asserted, not derived.** The security argument for the DAG is a union bound
over the per-node soundness errors, with the observation that a model compiles to at most ~100,000
nodes and that the resulting error is negligible "due to our field size". Knowledge soundness of the
generalized folding is deferred to an appendix. This is standard practice and we flag no bug, but the
system's soundness now rests on twenty hand-written pairing-based protocols, a Fiat–Shamir-compiled
folding scheme, and a rule-based graph rewriter, and the number of places an under-constraint could hide
went **up** relative to ZKML, not down. the SNARK-vulnerability SoK is the relevant prior.

**The lookup tables are fixed at compile time.** `CQ` and `CQ2` require the set and the table to be known
at compile time, which is what makes their proving cost independent of table size, and which means the
admissible range of every non-linearity is a preprocessing decision. An activation outside the calibrated
range is not inaccurate; it is unprovable. Same audit surface as every lookup-based system here, and
worth stating because ZKTorch leans on `CQ2` for *all* non-linearities and scale corrections.

**Credit where due.** The generalized-Mira construction is a genuinely good idea, cleanly stated, and it
is the reason a 7B model appears in a CPU-only table at all. Proving every model in MLPerf Edge, 
diffusion, 3D segmentation, detection, RNN, is a coverage result nobody else in this repo comes close to.
The problems are in how the results are *framed*: a proof-size headline measured on the wrong models, a
speedup whose attribution the ablations do not support, and LLM results whose one- and two-token inputs
are disclosed only in a table of input dimensions that the downstream literature has already
misread.
