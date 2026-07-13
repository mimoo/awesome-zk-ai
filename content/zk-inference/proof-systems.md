---
title: Proof systems
section: zk-inference
order: 30
lede: >-
  Six cryptographic approaches are in play. Each one was chosen because it is good at
  something a neural network does a lot of, and each one is bad at something else the
  network also does. The trade is never hidden -- but it is rarely stated.
papers: [safetynets, zkcnn, zkllm, zkgpt, zkpytorch, deepprove, spagkr, zkml-kang, ezkl, artemis, jolt-atlas, mystique, lu-et-al, zktorch, zen, vcnn, zip, hao-et-al, nanozk, bionetta, zator]
status: draft
---

A neural network's forward pass, viewed as a computation to be proven, has an unusual
shape: an enormous amount of very regular arithmetic (matmuls) punctuated by a small number
of deeply *non*-arithmetic operations (Softmax, GeLU, LayerNorm, re-quantization). Almost
every design decision in this section is a different answer to the same question — *which
half do I make cheap, and how much do I pay on the other half?*

| System | Approach | Commitment / backend |
|---|---|---|
| [[safetynets]] | Interactive proof (Thaler's IP for regular circuits) | none — no commitment, no ZK |
| [[zkcnn]] | GKR + sum-check, linear-time sum-check for convolution/FFT | — |
| [[zkllm]] | Sum-check + `tlookup` + `zkAttn`, CUDA | — |
| [[zkgpt]] | GKR + sum-check, non-interactive via Fiat–Shamir | Hyrax over BN254 |
| [[zkpytorch]] | GKR via Expander | M61, a small field |
| [[deepprove]] | Sum-check + lookup arguments | HyperKZG, BaseFold |
| [[spagkr]] | GKR / sum-check, sparsity-aware; composes with Lasso | — |
| [[jolt-atlas]] | Jolt-style lookup arguments over ONNX tensor ops | HyperKZG; ZK via BlindFold |
| [[zkml-kang]], [[ezkl]] | Halo2 / PLONKish arithmetization | KZG or IPA |
| [[artemis]] | Commit-and-prove over any homomorphic polynomial commitment | black-box (Apollo is the KZG variant) |
| [[zktorch]] | Basic blocks + parallel Mira accumulation | — |
| [[zen]], [[vcnn]] | R1CS / Groth16, QPP for convolution | trusted setup |
| [[bionetta]] | R1CS / **UltraGroth** — Groth16 with in-circuit lookup rounds | BN254, *per-circuit* trusted setup |
| [[mystique]], [[lu-et-al]] | VOLE-based interactive ZK | designated verifier |
| [[zip]] | Commit-and-prove zk-SNARK over native IEEE-754 floats | — |
| [[hao-et-al]] | Digit decomposition, for non-linear operators only | — |
| [[nanozk]] | Layerwise proofs, constant size per layer | — |

## Not a circuit, and not a zkVM

Before the primitives, a categorical point that trips up almost everyone — including us, until
we read the code. There are three ways to prove a model, and the systems in the table above are
mostly the *third*:

1. **Circuit compilers** — [[ezkl]] and [[zkml-kang]]. The model is lowered to an explicit
   arithmetic constraint system (R1CS / PLONKish gates), and a general-purpose SNARK proves
   that system was satisfied. The model *becomes* a circuit. [[zkpytorch]] is a compiler too,
   but its target is a *layered arithmetic circuit* for the Expander GKR prover — a compiler
   front end with a backend in the sum-check family, which is why it appears below rather than
   here.
2. **zkVMs** — the base [Jolt](https://github.com/a16z/jolt), RISC Zero, SP1. You compile a
   *program* to machine code and prove the CPU executed each instruction. There is an
   instruction set, a trace, a program counter.
3. **Direct sum-check over the tensor graph** — [[deepprove]], [[jolt-atlas]], [[zkcnn]],
   [[zkllm]]. **No circuit artifact and no VM.** The model becomes a DAG of tensor-operator
   nodes — an ONNX graph for [[deepprove]] and [[jolt-atlas]] — and each node gets a *bespoke*
   sum-check + lookup protocol proved directly against the multilinear polynomials of the
   tensors.

The confusing name is [[jolt-atlas]]: it borrows Jolt's *lookup argument* (Lasso/Shout,
prefix-suffix table decomposition) but throws away the CPU/instruction layer, re-pointing that
machinery at ONNX tensor operators. So it is category 3, not a zkVM — the vestigial `And/Or/Xor`
instruction tables in its `LookupTables` enum are the only fingerprint of where it came from.

**"No circuit" is a claim worth stating precisely, because it is partly false.** Everything here
is arithmetized — a sum-check relation *is* a constraint, and GKR is literally a protocol for
proving a layered arithmetic circuit. What category 3 avoids is narrower: no single *committed*
constraint system with a full witness assignment. Intermediate tensors are **virtual** — reduced
away by sum-check, never committed — so only the model weights and small lookup addresses are
committed, and the *committed witness* does not grow with the number of activations. (The proof
itself still does — see below.) That is the property people mean by "no circuit." (The lone
exception: [[jolt-atlas]]'s ZK layer, BlindFold, *does* use R1CS — to encode the sum-check
verifier, not the ML computation.)

## Where the setup lives (an orthogonal axis)

Whether a system is circuit-like and whether it needs a **trusted setup** are independent
questions — a distinction STARKs make vivid, being *transparent* (FRI, just a hash) yet very
much circuit-based (AIR). So do not read "modern sum-check system" as "no setup":

- **Trusted (universal SRS).** [[jolt-atlas]] commits by default with **HyperKZG over BN254** — a
  pairing/KZG scheme that needs a powers-of-tau ceremony and a proving/verifying-key generation
  step before a model can be proved. [[zen]], [[vcnn]] and [[bionetta]] (Groth16 and its
  derivative) need a *circuit-specific* trusted setup, stronger still.
- **Transparent (no toxic waste).** [[zkgpt]]'s Hyrax, Dory (which the base Jolt used, and which
  Jolt Atlas explicitly replaced), FRI/STARK, IPA. [[deepprove]]'s BaseFold is hash-based.

Jolt Atlas is the instructive case: it is *less* circuit-like than a STARK on the first axis, yet
*has* a trusted setup where a STARK does not — it traded the transparent Dory for pairing-based
HyperKZG deliberately, to get smaller openings suited to on-chain verification.

And the per-circuit setup has a **security property nobody advertises**, which the Fiat–Shamir box
at the bottom of this page turns out to need. A circuit-specific SRS means the verification key
*is* a commitment to the exact circuit — and in zkML the circuit *is* the architecture. A system
with a per-circuit setup is a system whose prover **cannot choose its own circuit**, because
choosing a different one produces a key the verifier will not accept. That is normally filed as a
pure cost (retraining means a new ceremony, which is why [[bionetta]] only works for fixed public
models). It is also the strongest architecture-pinning mechanism in this SoK, obtained for free as
a side effect of a choice made for entirely different reasons.

## Sum-check and GKR

**What it is.** Express the layer as a low-degree polynomial identity over the multilinear
extensions of its inputs, and have the prover convince the verifier of a *sum* over the
Boolean hypercube in a logarithmic number of rounds. GKR chains this layer by layer, so the
verifier's claim about layer $i$'s output reduces to a claim about layer $i-1$'s output.

**Why it was picked for ML.** Two reasons, and they are both about matmul. The prover runs
in time linear in the circuit — no FFT over the whole witness, no quadratic blowup — and a
matrix multiplication is exactly the kind of *regular*, data-independent circuit
sum-check is happiest on. [[safetynets]] made this move in 2017 and every fast system in
the table descends from it. [[zkcnn]] then showed convolution has a linear-time sum-check
that is *asymptotically faster than computing the convolution directly*, which is the single
most surprising result in the pre-LLM literature.

**What it is bad at.** Everything that is not a polynomial. Softmax and GeLU have no
low-degree representation, so a pure GKR system must either restrict the model (see
[[safetynets]] below), bit-decompose (expensive, and lossy), or bolt on a lookup argument —
which is what [[zkllm]] (`tlookup`), [[deepprove]] and [[zkgpt]] all do. It is also bad at
*parallelism*: the layer-by-layer structure serializes the prover, which is precisely the
bottleneck [[zkgpt]]'s "circuit squeeze" attacks by flattening the circuit into a wider,
shallower shape. And its proofs are not small — they grow with the circuit, which is why the
GKR systems' proof sizes run from kilobytes to tens of megabytes while a Groth16 system's
is a fixed handful of bytes.

**The variants worth separating.** [[zkllm]]'s `zkAttn` is a bespoke argument for the whole
attention mechanism rather than a generic lookup over its parts. [[spagkr]] makes prover
cost scale with the number of *non-zero* parameters, which matters enormously for pruned and
MoE models. [[zkpytorch]] uses an off-the-shelf GKR prover (Expander) and spends its
novelty budget on the compiler and the field choice instead.

## Lookup arguments

**What it is.** Prove that a claimed value appears in a preprocessed table. Lasso and Jolt
made this cheap enough that you can prove a *computation* by proving that each step's output
is the table entry for its input — an approach that turns "prove GeLU" into "prove a
table read".

**Why it was picked for ML.** It is the direct answer to what GKR is bad at. The
non-arithmetic operators are exactly the ones with small input domains once the model is
quantized, so they fit in tables. [[jolt-atlas]] takes the idea furthest: instead of
emulating a CPU and proving a RISC-V trace (Jolt's original framing), it proves ONNX tensor
operations directly, so there is no instruction-set indirection at all. [[deepprove]] uses
lookups alongside sum-check for exactly the operators sum-check cannot reach, including
re-quantization.

**What it is bad at.** Table size, and it is not a gentle dependence: **the table grows
exponentially in the bit width of the lookup input.** [[zkgpt]] demonstrates the cliff
rather than merely warning about it —

:::quote{src="zkGPT" sec="§9.1, Analysis of different merging levels"}
Based on our quantization, qEi is a vector with length 32 each element is 16 bit.
Consequently, the total number of possible inputs to this lookup table is 2^(16×32) = 2^512,
resulting in a prohibitively computational cost.
:::

— which is why it *rejects* the most aggressive form of its own constraint-fusion
optimization. The same pressure explains [[jolt-atlas]]'s neural teleportation (shrink the
table by rescaling the activation's input) and its prefix–suffix decomposition of tables
(cut peak prover memory so a real model fits in a laptop's RAM). It also makes
[[jolt-atlas]]'s failure to state a bit width [an unusually consequential
omission](./quantization/).

## Lookups inside Groth16 — UltraGroth

**What it is, and why it should not exist.** A LogUp-style lookup argument needs a verifier
challenge drawn *after* the prover has committed to the witness: the rational-sum identity
$\sum_i (X + z_i)^{-1} = \sum_j \mu_j (X + t_j)^{-1}$ is checked at a random $X$, and the whole
thing collapses if the prover knows $X$ in advance. **Groth16 has no rounds.** There is one
witness, one commitment, one proof. That is precisely why nobody had put a lookup argument in it,
and why the R1CS line was stuck paying a full bit decomposition for every range check.

[[bionetta]]'s **UltraGroth** adds the rounds. The witness is partitioned into $d+1$ segments;
each segment gets its own $\delta_i$ in the SRS and its own commitment $\pi_C^{\langle i\rangle}$;
that commitment is hashed to derive the *next* segment's challenge, and the challenges ride along
as public signals the verifier recomputes for itself. Fiat–Shamir, with the random oracle sitting
inside the proof rather than around it.

**What it costs.** One extra pairing in the verifier — four instead of three — one extra hash, and
$d+1$ extra $\mathbb{G}_1$ elements in the proof. In Bionetta's deployment $d = 1$, so: one round.
Completeness, soundness and zero-knowledge are proved in GGM + ROM.

**What it buys.** The thing [the numerics page](/numerics/) says the whole proof consists of: the
range check. A ReLU's $b$-constraint bit decomposition becomes $b/w$ lookups against a table of
size $2^w$, giving a prover cost of $O(2^{w+1} + bL/w + 4L)$ over $L$ range checks — i.e.
$O(N/\log N)$, with an optimal limb size $w$ that solves $2^w w^2 = Lb/2\log 2$ and lands near 18.
Measured, on Bionetta's own models, that is a 6–11× drop in constraint count, and it is the
difference between ResNet18 proving on an iPhone in 14 seconds and not fitting in the phone's
memory at all.

**What it is bad at.** Everything Groth16 is bad at, undiminished: a **per-circuit** trusted setup
(see below), and a proving key that grows with the circuit — 2.4 GB for MobileNetV2. Retrain the
model and you need a new ceremony. It is a real constraint and it is why this design belongs to
fixed, public, long-lived models — which is exactly the setting Bionetta targets and nobody else
does.

This is the most interesting cryptographic contribution in the recent zkML literature, and it is
sitting in a vendor technical report that no academic paper cites.

## Halo2 and PLONKish arithmetic circuits

**What it is.** Compile the model into a table of gates and copy-constraints, commit to the
columns, and prove with a universal SNARK. The mature, boring, tooling-rich option.

**Why it was picked for ML.** Because you can actually ship it. [[zkml-kang]] and [[ezkl]]
are the systems people deploy, and they got there by compiling from TFLite/ONNX graphs into
an existing, audited proving stack with a real ecosystem. The payoff is at the *verifier*:
proofs are kilobytes and verification is constant-size work rather than a re-run of the
circuit, which is what makes on-chain settlement plausible at all. GKR's megabyte proofs are
not going on a blockchain. It is not free, though — on GPT-2 the verifier cost is seconds, not
milliseconds.

:::debate  The verifier payoff is the reason everyone gives, and for ezkl it is not true
Somebody finally measured it. [[bionetta]] runs [[ezkl]] and [[zkml-kang]] on the same five
vision models on the same 16-thread Xeon, and the two Halo2 systems — treated as one row by
the entire literature, including the table at the top of this page — **do not have the same
verifier profile at all.**

[[zkml-kang]] behaves the way the story says: proofs of 5–7 kB, verification in 12–23 ms.
[[ezkl]] does not. Its proofs run to hundreds of kilobytes, its *verification keys* reach 37 MB,
and verification takes **seconds to tens of seconds** — 40.6 s on MobileNetV2, behind a 76 GB
proving key and four hours of proving. None of that settles on a chain. Whatever ezkl is being
tolerated for, it is not a cheap verifier.

Halo2 can of course be configured for small proofs and fast verification; [[zkml-kang]] proves
it on the same hardware. The point is narrower and worse: **the most widely deployed zkML
toolchain is not configured that way, everyone cites it as the thing you use when you need
on-chain verification, and the numbers were not in print until a competitor published them.**

And the line the field wrote off is the one that actually delivers the property: a Groth16
proof is a constant three-to-four group elements — [[bionetta]]'s is 0.88 kB on every model
from an MLP to MobileNetV2, verified in 10–20 ms against a 4 kB key. The cost is a per-circuit
trusted setup, which is a real cost. It is not the cost the literature has been quoting.
:::

**What it is bad at.** The prover. Every non-linearity becomes constraints, the constraint
count explodes, and [[zkml-kang]] is consequently the standard slow baseline in the table — the
one the GKR systems beat by orders of magnitude. Key generation is its own tax
([[jolt-atlas]] notes that [[ezkl]]'s key generation alone exceeds its own total proving
time on the same model). And there is a second, less-discussed cost that [[artemis]] exists
to attack: **the consistency check between the committed model parameters and the circuit's
copy of them** can dominate everything else on a large model. Artemis is generic over
homomorphic polynomial commitments (so it works in transparent Halo2/IPA settings with no
trusted setup); Apollo is the faster KZG-specific variant.

:::audit  Two systems here sit on a stack with a known, fixed bug
the Halo2 query-collision bug: in Halo2's multipoint opening argument, querying the same
polynomial at the same point twice caused one evaluation to be *silently ignored*, letting a
malicious prover forge evaluations. The root cause is domain wrapping — `Rotation(0)` and
`Rotation(2^k)` are the same point, and the frontend did not deduplicate. Fixed, disclosed,
no production compromise. But [[zkml-kang]] and [[ezkl]] inherit this bug class wholesale,
and it is the shape of thing an audit of a zkML circuit should be looking for.
:::

## VOLE-based ZK

**What it is.** Interactive zero-knowledge built on vector oblivious linear evaluation.
The prover is extremely fast — no FFTs, no elliptic-curve MSMs in the hot path — because it
never has to make the proof succinct.

**Why it was picked for ML.** [[mystique]] and [[lu-et-al]] both bet that prover time is the
binding constraint and everything else is negotiable. On raw prover speed the bet paid off:
[[lu-et-al]] on GPT-2 is far faster than the Halo2 baseline.

**What it is bad at, and it is disqualifying for most of the use cases in this repo.** The
proofs are not succinct — they are the largest artifacts in the entire table, by orders of
magnitude — and the verifier is *designated*: you cannot hand the proof to a third party.
That kills on-chain settlement and it kills the "publish a proof, anyone can check it" story
that motivates zkML in the first place. It also means the comparison is unfair in both
directions: [[zkgpt]] folds communication time into VOLE provers' reported time "for fair
comparison", which is the right call and part of why its measured numbers for [[lu-et-al]]
disagree with the survey's.

## Accumulation and folding

**What it is.** Prove each piece with whatever protocol suits it, then *fold* the resulting
instances together rather than verifying each one. [[zktorch]] compiles a model into "basic
blocks", proves each with a specialized protocol, and accumulates them via a parallel
extension of Mira.

**Why it was picked for ML.** It is the natural fit for a model graph, which really is a
heterogeneous pile of operators rather than one uniform circuit. It attacks proof size
directly — the thing PLONKish is good at and GKR is not — without giving up per-operator
specialization.

**Where it came from, and the tax it pays.** The idea is older than the paper. [[zator]] — a
2023 hackathon project, no paper, no review — folded a per-layer step circuit with Nova and
proved a 512-layer network, deeper than anything else in this file, two years before ZKTorch
made the approach respectable. It is worth knowing about for one reason: it is the only system
here that pays the *homogeneity tax* in the open. A folding scheme can only fold a step function
that is the same every time, and a model is not the same every time — so Zator's backbone is
five hundred and ten **identical** convolution layers, chosen to be convolutions because a dense
layer's weight matrix is ruinous merely to *hash* into the running commitment. Even then the
head and tail layers do not fit the step, and the system ships three proofs the verifier must
chain by hand. Every folding system inherits that bill. ZKTorch pays it in a compiler that
decomposes a heterogeneous graph into basic blocks — and in the seven of those blocks that have
no accumulation support at all, which is exactly why its benchmarks never sample a token.

Zator also settles, accidentally, a question the rest of the section keeps open. It is the
control experiment for *depth*: recursion genuinely does dissolve it, the folding overhead per
step really is negligible, and the network it delivered still classifies handwritten digits.
**Depth was never the binding constraint — width is** — and no amount of folding touches width.

**What it is bad at.** Now that we have read the paper's own tables, the answer is visible:
autoregression. Every LLM row it reports is a single forward pass over a one- or two-token
input, and the decode step is precisely what does *not* fold — ArgMax and TopK are built out of
three of the seven basic blocks that have no accumulation support, so the compiler is written
to steer around them, and none of its benchmarks ever sample a token. The proof-size claim
deserves the same care: it rests on a ResNet-50 row whose baseline cells hold the competing
systems' proof sizes for *smaller* models, because those systems never implemented ResNet-50.
The head-to-head proving-time claim against [[zkml-kang]], by contrast, is like-for-like.

## The two outliers

**[[safetynets]] — interactive, not zero-knowledge.** The oldest system in the section and
structurally unlike all its descendants. It is a genuine interactive proof: the verifier
sends live challenges, there is no Fiat–Shamir transform, no polynomial commitment, and no
zero-knowledge. It buys *integrity only*, at a prover overhead that nothing else here comes
within two orders of magnitude of. Read it as the floor: this is what proving costs when you
drop ZK, drop commitments, and let the model be restricted.

**[[zip]] — refuse to quantize.** Everyone else bends the model to fit the prover. ZIP bends
the prover to fit the model: the honest prover computes in native IEEE-754 double precision, and
the activations are proven against piecewise-polynomial lookups, with extra arithmetic
constraints hardening those lookups against a malicious prover. Read the guarantee carefully,
though — what the constraint system enforces is that each activation lies inside a
relative-error ball around the approximation, not that it is the true IEEE-754 value, and the
advertised timings come from a configuration whose linear layers are checked with a tolerance
too. It is not an LLM system and does not belong on the throughput chart. It belongs here
because it is the standing disproof of the assumption everything else makes — that a model must
be quantized.

:::audit  The construction under most of this page has a proven attack
the Fiat–Shamir/GKR attack (CRYPTO '25) attacks **GKR compiled to a non-interactive argument
via Fiat–Shamir** — which is [[zkgpt]], [[deepprove]], [[zkpytorch]], [[zkcnn]], [[zkllm]]
and [[spagkr]]. Two attacks: adaptive proofs of false statements for a specific circuit, and
a functional-equivalence attack that, given any circuit `C` and any output `y`, builds a
functionally equivalent `C*` admitting an accepting proof that `C*` outputs `y`.

**The precondition is load-bearing: the attacker must choose or modify the circuit.** The
paper says explicitly that this does not apply to fixed, honestly-chosen circuits in
standard deployments. It is not a break of any deployed zkML system.

It is on this page anyway, because of one structural fact: **in MLaaS the prover is the
model owner, and the model is the circuit.** A deployment that commits to *weights* but
never independently pins the *architecture* is uncomfortably close to the attack's
precondition — and "produce a functionally equivalent circuit whose output I choose" is
precisely the model-substitution threat this whole section exists to prevent. Whether any
system here satisfies the precondition **has not been analyzed.** [[safetynets]] is the one
member of the family the attack cannot touch, and for an instructive reason: it never
compiled the interaction away. The vulnerability was introduced by the very step that made
the lineage practical.

**A second system is out of reach, and it got there by accident.** [[bionetta]] is not a GKR
system at all, so the attack does not apply on its face — but the deeper reason is worth having,
because it is the mitigation everyone else needs. Its **per-circuit trusted setup** means the
verification key is derived from one specific R1CS instance. A prover who swaps in a
functionally-equivalent circuit is producing proofs against a key no verifier will accept. The
precondition — *the adversary chooses or modifies the circuit* — is not merely unmet; it is
cryptographically unreachable. And Bionetta did not do this for security. It did it because
Groth16 was the only way to get a sub-kilobyte proof onto a chain.

Which sharpens the ask for everyone else, and it is not exotic: **pin the architecture, not just
the weights.** [[zkaudit]] does it by convention — weights secret, architecture public. Bionetta
does it by construction. Every universal-SRS system in the table above does neither: it commits to
the weights and leaves the circuit free.
:::

## What is actually zero-knowledge here?

Worth stating, because the section's name promises it and the papers do not uniformly
deliver it. [[safetynets]] is explicitly *not* zero-knowledge — it hides nothing, and says
so. [[zkllm]] claims its proofs expose no model parameters. [[jolt-atlas]] gets ZK from the
BlindFold technique. [[zip]] is model-private by construction. For several of the remaining
systems the ZK property is asserted in the name and not measured anywhere — and the cost of
*adding* ZK to a system benchmarked without it is not reported by anyone.

And one system is zero-knowledge about **the other operand entirely**, which is worth separating
out because the vocabulary hides it. Everywhere else on this page, "zero-knowledge" means *the
proof does not leak the weights*. In [[bionetta]] the weights are public on purpose; what the
proof hides is the **input** — the user's face. Same property, opposite secret, and the two are
not interchangeable: a system that hides the model tells you nothing about whether it hides the
query, and almost nobody in this table states which one they are claiming.

:::gap  Is the reported throughput a zero-knowledge throughput?
For most systems in this table we cannot tell whether the benchmarked prover had
zero-knowledge enabled. Blinding costs something. If a system's headline figure is from a
non-ZK configuration and its competitor's is not, that is one more confounder on top of
[the ones we already have](./what-is-proven/).
:::
