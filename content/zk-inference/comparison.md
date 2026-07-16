---
title: System by system
section: zk-inference
order: 60
lede: >-
  Every system here claims to prove inference. They do not prove the same claim, they do not
  descend from the same idea, and their headline numbers are not on the same axis. This page
  takes them one at a time and asks the only question that survives: what did this paper
  actually contribute that did not exist before it?
papers: [safetynets, zkcnn, zkllm, zkgpt, zkpytorch, deepprove, jolt-atlas, spagkr, mystique, hao-et-al, lu-et-al, vcnn, zen, zkml-kang, zktorch, artemis, zip, range-arithmetic, nanozk, ezkl, bionetta]
status: reviewed
---

The [inference table](./) ranks these systems on throughput. That ranking is close to meaningless
on its own, the systems run different models at different bit widths on different hardware, and
several are not even proving the same *statement*. What follows is the other view: **four
lineages, each descending from a different founding idea**, and inside each, what every paper
actually added.

Read the lineages first, because they explain the numbers:

| Lineage | Founding idea | Where the cost goes |
|---|---|---|
| **Sum-check / GKR** | The network is an arithmetic circuit; prove it with sum-check. | Non-linearities and rounding seams. Matmuls are nearly free. |
| **Lookups** | Don't arithmetise anything; look it up. | Table size — exponential in bit width. |
| **R1CS / SNARK compilers** | Lower the model into a general-purpose circuit and use an off-the-shelf prover. | Constraint count, and commitment consistency. *Unless the weights are public, in which case the linear layers cost nothing at all.* |
| **VOLE / designated-verifier** | Give up the public, reusable proof; buy a very fast prover. | Communication — and you cannot publish the result. |

{{ table:inference }}

---

## I. The sum-check line

This is the highway. Seven of the systems here are one lineage, and each inherited its predecessor's
machinery.

### SafetyNets (2017), the root

[[safetynets]] is the paper everything else in this column descends from, and it is the only one
that no longer looks like the others. Ghodsi, Gu and Garg took Thaler's time-optimal interactive
proof for regular arithmetic circuits, itself a refinement of GKR, and composed it with a *new*
specialized sum-check for the activation layers of a neural network. That composition is the
founding move of the entire field: **represent the network as an arithmetic circuit and prove it
with sum-check, rather than shoving it through a general-purpose SNARK.**

What is novel is precisely that composition. The matmul protocol was Thaler's; the activation-layer
sum-check was theirs; the contribution is that the two compose end to end without the prover having
to commit to every intermediate value. It is the first demonstration that verifiable neural
inference could cost a small multiple of the inference itself rather than a catastrophic one.

Two properties make it structurally unlike every descendant, and both matter more in 2026 than they
did in 2017. It is **genuinely interactive**, the verifier sends live random challenges, there is
no Fiat–Shamir transform, which means the CRYPTO '25 attack on Fiat–Shamir-compiled GKR
that hangs over every system below it **cannot reach it**. And it is
**not zero-knowledge**: it buys integrity, not privacy. The weights and inputs are not hidden.

The price is the model class, and it is brutal. Activations must be *polynomials* over the field,
so the network is restricted to **quadratic activations** (`x → x²`) everywhere except the output
layer. No ReLU, no sigmoid, no softmax. Sum pooling, not max pooling. Read from here, essentially
the entire subsequent literature, lookup arguments, `tlookup`, `zkAttn`, result-as-witness, is
the story of *removing that one restriction*.

And the number to carry forward: its prover overhead over unverified execution is a few percent.
Nothing since comes close, and no other system on this page reports an overhead figure against
unverified execution at all, so the gap cannot be sized. That gap is not only the price of
zero-knowledge and commitments, which SafetyNets does not provide, a large part of it is [the
price of rounding](/numerics/), which SafetyNets does not pay because a polynomial network has no
rescale seam at all.

### zkCNN (2021), sum-check learns to convolve

[[zkcnn]] is the paper that made the lineage practical, and its contribution is a piece of
mathematics rather than an engineering trick. Liu, Xie and Zhang built a **linear-prover-time
sum-check for 2D convolution**, asymptotically faster than *computing the convolution directly*, 
along with an O(N) sum-check for the FFT, beating the conventional O(N log N).

That "faster than computing it" property is worth pausing on, because it is the deep reason the
sum-check line won. In most of cryptography, proving a computation costs vastly more than doing it.
Here the proof of a convolution is asymptotically cheaper than the convolution. The prover's real
cost lands elsewhere, in the commitments and the non-linearities, which is exactly the cost
structure the rest of this page keeps rediscovering.

zkCNN also straddles two of this SoK's objectives: it proves not only a single inference but
**accuracy over a public dataset**, making it an early entry in [proving testing](/zk-testing/) as
well as inference.

Its lasting influence is its **quantization scheme**, the affine `x = S(q − z)` with a per-layer
scale and zero-point, which [[zkgpt]] inherits wholesale and [[zkpytorch]] builds on. When you read
a 2025 transformer prover and find an affine quantizer with a zero-point, you are reading zkCNN.

### zkLLM (2024), the first transformer, and the first honest look at softmax

[[zkllm]] (Sun, Li, Zhang) is where the lineage meets the transformer, and it remains the largest
model anyone has run a prover over, though the paper says only that it proves "the entire inference
process", never how many tokens that covers, so the end-to-end reading is ours, not theirs. Its two
contributions are both about the thing sum-check cannot do.

**`tlookup`** is a parallelized lookup argument for non-arithmetic tensor operations, the general
machinery for handing a prover an operation that is not a polynomial. **`zkAttn`** is a bespoke
argument for attention, and its motivation is the most clear-eyed statement of the numerics problem
in the literature: it exists specifically to avoid *bit-decomposing* softmax, because
bit-decomposition approaches need large bit widths to preserve accuracy, and large bit widths force
large fields, and large fields make the prover slow.

That single paragraph is the whole [numerics](/numerics/) argument, and zkLLM is the paper that
articulated it. It is also the first system in this column built for the **GPU** rather than the
CPU, which is why its throughput is not comparable to the CPU systems around it.

What to distrust: the bit width is never stated. The reported accuracy claim is an L1 error on the
output that the paper describes as comparable to half-precision rounding, a reasonable claim, but
not a perplexity number, and not a task-accuracy number.

### zkGPT (2025), round less often

[[zkgpt]] is, in my view, the most carefully engineered paper in the lineage, and its contributions
are three, all of which fall out of one insight.

The insight, stated plainly in the paper: **rounding introduces range relations, and range
relations cost more than arithmetic relations.** Once you believe that, the optimization is
obvious, do less rounding. **Constraint fusion** merges the computation between two adjacent
rounding operations into a single rounding, generalizing a trick [[zkcnn]] and Kang et al.'s
trustless-DNN-inference paper had used only in the narrow convolution→ReLU case.

The second contribution is **circuit squeeze**: breaking GKR's layer-by-layer dependency to flatten
the circuit into a wider, shallower one, which parallelizes. The third is the **result-as-witness**
paradigm, the prover supplies the output of Softmax, LayerNorm and GeLU as advice and then proves
it lies in the correct range, rather than computing it in-circuit. zkGPT applies this to division,
square root and exponentiation, and its handling of square root is the little gem of the paper: it
converts an irrational function into two multiplications and a range check.

zkGPT also gives the **cleanest quantization accounting of anyone**, it states its bit width,
states its scheme, and reports the perplexity cost on named datasets. It is the reference point
against which the others should be normalized. Note that it sits at the *high* end of the bit-width
range, which means it is doing a materially harder job on the range-check side than a
lower-precision competitor and paying for it in the throughput column.

What to distrust: result-as-witness moves soundness *entirely* onto the range constraints. An
under-constrained range check in this design does not cause a precision bug, it lets a malicious
prover assert an arbitrary non-linear output. That is the audit surface, and the SoK of real SNARK
bugs finds under-constrained circuits to be both the most common and the most severe class.

### zkPyTorch (2025), a compiler, and a fight with the field

[[zkpytorch]] is not a protocol. At the primitive level it reuses zkCNN's convolution and zkLLM's
lookups, and it says so. It is a **compiler**, and it should be read as one, its three
contributions are all about getting a real PyTorch model into a prover without a human in the loop.

First, an ONNX-**DAG** preprocessor that handles non-sequential architectures (residuals) and
inserts *auxiliary witnesses*: division becomes a quotient plus a `remainder < divisor` proof;
softmax's `exp` and RMSNorm's `sqrt` become piecewise lookup tables. Second, a three-level circuit
optimizer whose model level **batches inference**, since a proof only verifies the output, the
autoregressive token dependency decouples and all tokens can be proven in one circuit.

The third is the one that matters, and it is the sharpest strategic idea in the lineage:
**ZKP-friendly static integer quantization sized to fit a small field.** zkPyTorch quantizes hard, 
low-bit weights and activations, wider intermediates for accumulation, *specifically so that it can
work over M61 instead of the 254-bit BN254 curve field*. That is not a lookup-table optimization; it
is a constant factor on the **entire circuit, matmuls included**, and it is a much bigger lever than
anything else on this page. Its whole quantization strategy is downstream of a field-size decision.

What to distrust: the LLM accuracy claim is a **cosine similarity** to the float model, which is a
weaker guarantee than perplexity, a high cosine similarity can still flip an argmax and change the
generated token. And, as a compiler over a Fiat–Shamir-compiled GKR backend (Expander), it inherits the
Fiat–Shamir caveat wholesale.

### DeepProve (2026), the requantization paper

[[deepprove]] is the current throughput leader, and the reason is not a faster sum-check. It is that
DeepProve took the two problems everyone else had been stepping around, **requantization** and
**autoregression**, and actually solved them.

Its requantization PIOP is the most complete treatment of [the rescale seam](/numerics/) anywhere.
The arbitrary float scale is fixed-point-encoded as an integer multiplier, so the *divisor* is a
power of two and the division becomes a **right shift**, proven with a lookup argument over
decomposable tables. Round-to-nearest is handled by adding a half before flooring. And crucially it
handles **Case 2**, requantization when the input is *out* of the expected range, via tables that
emit −1/0/+1 to detect and correct overflowing elements. It observes, accurately, that the in-range
case is "the only scenario considered by prior works," naming zkLLM and zkGPT. Everyone else had
been proving a *conditional*: correct **assuming** nothing overflowed. (Though DeepProve is the only
*paper* with an explicit out-of-range protocol, not the only *system*, see Jolt Atlas below.)

Its second idea is the elegant one, and it is a *statement* change rather than a protocol change:
**do not prove generation, prove certification.** Feed `[prompt ‖ claimed output]` through the model
in a single pass; the causal mask means position *t* cannot see token *t+1*, so if every position
predicts its successor, the whole sequence is certified. This turns an O(t²) autoregressive proving
problem into one linear forward pass, and it is the reason its throughput figures are on a
different scale from everyone else's. It is also why comparing it to a system that proves a *single
forward pass over a two-token prompt* is a category error.

Third, its quantization block is the most sophisticated in the field: symmetric affine PTQ with
calibration, mixed precision (residual layers get a wider bit length), and **outlier smoothing by
orthonormal rotation**, `XW = (XM)(Mᵀ W)`, with `M` absorbed into the previous layer's weights so
the hard-to-quantize activation tensor is never materialized. That is a standard-ML technique
imported wholesale into a prover, and it is what the [quantization page](./quantization/) means by
*bending the prover to fit the model* rather than the reverse.

What to distrust: its own reported finding, which nobody has followed up. **Gemma 3 does not survive
low precision**, its similarity to the float model collapses, and DeepProve attributes this to
extreme outlier activations plus extra RMSNorm layers that defeat the rotation trick that works on
GPT-2. The smoothing technique that makes low-bit proving viable is **architecture-dependent, and
modern architectures break it.** Every projection that assumes proving gets cheaper as we quantize
harder is betting against that result.

### SpaGKR (2024), the structural shortcut

[[spagkr]] is the odd one out in this lineage, because its win comes from changing the *model*
rather than the *prover*. It makes proof time scale with the number of **non-zero** parameters
rather than the total, which is a large gain on sparse linear layers; and it goes further, to
**ternary** weights in `{−1, 0, 1}`, which eliminates multiplication from the linear layers
entirely.

Its relevance is forward-looking rather than historical: sparsity is exactly the structure of a
**mixture-of-experts** model, and MoE is what frontier architectures actually are. Nobody has
followed that thread.

The caveat is not to over-generalize the ternary result. It is a *structural* change, removing
multiplications and inducing sparsity, not a demonstration that "fewer bits is faster" for an
arbitrary system.

---

## II. The lookup line

### Jolt Atlas (2026), arithmetise nothing

[[jolt-atlas]] is the cleanest philosophical alternative on this page. Inheriting Jolt's founding
bet, it does not express operations as *constraints* to be satisfied; it expresses them as
**lookups** into tables. Non-linearity is therefore never arithmetised at all, the thing that
costs every system in the sum-check line the most is, here, structurally absent.

Everything follows from that choice, including the costs. Table size grows **exponentially in the
bit width of the lookup input**, so bit width is more load-bearing in this design than in any
pure sum-check system. Two techniques manage it: **prefix-suffix decomposition**, which lets the
prover *stream* the table and cuts peak memory from O(|T|) to roughly O(|T|^{1/C}), this is why it
proves GPT-2 on a laptop, which no other system here can do, and **neural teleportation**, which
shrinks the activation domain so the table stays small.

Teleportation is also its most honest weakness, and the paper says so: replacing `y = σ(x)` with
`y′ = σ(x/τ)` is "a lossy approximation... but it is not significant in practice." The error is
bounded, but bounded in *raw output units of a fixed-point representation*, never in model
accuracy. There is no perplexity number and no task-accuracy number for any model in the paper.

It is also one of the few systems here that treats **zero-knowledge** as a distinct obligation to be
retrofitted rather than a property of the design. Much of the sum-check line is
verifiable-but-not-hiding, [[safetynets]] buys integrity, not privacy, and [[range-arithmetic]]
defers privacy to future work, and a raw sum-check transcript leaks the weights.
Jolt Atlas applies **BlindFold**: every sum-check round polynomial is sent as a Pedersen commitment,
the sum-check *verifier* is encoded as an R1CS circuit, and that instance is Nova-folded. The
resulting circuit is logarithmic in the computation proven.

And a finding that is only visible in the source, not the paper: **it does handle out-of-range
accumulators**, with a saturating clamp (`SatClamp`, i64 accumulator clamped to i32) discharged by a
Shout sum-check and *fused into the same rebase seam as the rescale*. Its paper never mentions this.
Its coverage is also partial in exactly the places an auditor cares about, in ZK mode `Add`/`Sub`/
`Sum` are proved un-clamped, the ONNX `Clamp` op is an unproven passthrough, and several activation
clamps are prover-side `assert!`s over unconstrained advice. **A `debug_assert` is not a
constraint.**

What to distrust, above all: it states **no model-level bit width at all**, and for the design most
sensitive to bit width, that omission matters most. Its results are not wrong; they are
*un-normalizable*.

---

## III. The R1CS / compiler line

The oldest strategy: don't invent a protocol, lower the model into a general-purpose circuit and let
an off-the-shelf prover handle it. It lost on throughput and won on breadth, and then, in
December 2025, it won on throughput too, by changing the question.

### vCNN (2020) and ZEN (2021)

[[vcnn]] encodes convolution with **Quadratic Polynomial Programs** rather than R1CS, attacking the
constraint blow-up of convolution inside a SNARK. It is mostly of historical interest now, its
VGG16 proving time is *reported* in hours (a survey figure; we do not have the paper), where zkCNN
needs seconds, but the trajectory is the point.

[[zen]] is the more interesting ancestor, and it made an argument that took the field another five
years to internalize: **optimize the network, not the prover.** Its backend is off-the-shelf
Groth16; its contribution is *proof-friendly quantization* and *stranded encoding*, which reduce
the R1CS constraint count directly. It ships both `ZENinfer` (prove one inference) and `ZENacc`
(prove accuracy on a verifier-supplied test set), and its remainder-based verification is the direct
ancestor of zkPyTorch's auxiliary witnesses and zkGPT's result-as-witness. Its own tables also
contain the earliest measurement of the in-circuit commitment bottleneck that Artemis would later
attack, ZEN just did not notice it.

### ZKML / Kang et al. (2024), the baseline, and the confounder

[[zkml-kang]] is an optimizing compiler from TensorFlow Lite graphs to halo2 circuits, and it became
the **non-interactive baseline everyone else measures against**. Its real contribution is
engineering breadth and a usable toolchain.

It is also the source of a confounder that quietly invalidates a lot of downstream claims, and it is
worth stating plainly: **ZKML's "GPT-2" is a *distilled* GPT-2**, materially smaller than the GPT-2
that DeepProve, zkGPT and Jolt Atlas run. The paper is explicit about this. Downstream comparisons
drop the word "distilled" and the parameter gap with it. Any "faster than ZKML on GPT-2" claim in
this corpus is a comparison against a smaller network. We ourselves recorded it wrongly until we
opened the paper.

### ZKTorch (2025), breadth as the contribution

[[zktorch]] is the successor to ZKML from the same group, and it is **not an improved ZKML**, it
throws away the single-halo2-circuit architecture entirely for a DAG of about twenty *basic blocks*,
each proved by a specialized protocol and then **accumulated** via a parallel extension of the Mira
accumulation scheme.

Its genuine achievement is breadth: it is the first ZK system to prove **every model in MLPerf
Inference: Edge v4.1**. That is the contribution, and the headline speedup buries it.

The thing to know before citing its LLM numbers: **every LLM benchmark is a single forward pass over
a one- or two-token input.** The paper never discusses autoregression or KV caching. Converting that
into a tokens-per-minute figure, as at least one competitor's comparison table does, is
arithmetically valid and a category error: those two tokens are one prompt in one pass, not two
decode steps. Structurally, the decode step is precisely what does *not* fold in its architecture,
because ArgMax and TopK are built from basic blocks with no accumulation support.

### Artemis / Apollo (2024), the bottleneck nobody was looking at

[[artemis]] attacks a completely different cost than everyone else on this page, and that is why it
belongs here. Not the matmuls, not the non-linearities: the **consistency checks between the
committed model parameters and the circuit that uses them**, which on large models can dominate
everything else. Artemis *reports* cutting commitment-verification overhead on VGG from roughly an
order of magnitude down to nearly nothing, a figure we have secondhand, from the survey; we do not
have the paper.

Apollo is the KZG/white-box variant; Artemis is generic over any homomorphic polynomial commitment,
so it works in transparent Halo2/IPA settings with no trusted setup. It is the clearest example in
this SoK of a paper that got a large win by profiling honestly rather than by inventing a new
argument.

### Bionetta (2025), free matmuls, if you are allowed to publish the weights

[[bionetta]] is the paper that makes this whole lineage worth re-reading, and it does it with an
observation so simple it is almost annoying: **R1CS charges nothing for multiplication by a
constant.** Every system above passes the model weights in as *signals*, and therefore pays a
constraint for every weight-times-activation product. But it only has to do that because the
weights are secret. Make the model public and the weights become circuit **constants**, and then
every matmul, every convolution and every folded BatchNorm costs **zero constraints**. Not cheap.
Zero.

ResNet18 falls from 37.85M constraints to 1.16M, and from 270 seconds to 14. On an **iPhone**.

Two things follow, and both are larger than the paper.

**The threat model is the dominant term in the cost, and nobody separates it out.** Five years of
protocol work in the sum-check line, linear-time convolution, `tlookup`, result-as-witness,
circuit squeeze, buys large constant factors. *Publishing the weights* buys a factor of thirty-two
by itself. When you read Bionetta's benchmark table beating [[ezkl]] by 580× on proving time, most
of that is not UltraGroth and not R1CS. It is a weaker security property, showing up in the
constraint count. To its credit, the paper's own Table 5 isolates the two effects cleanly. It is
just not the table anyone will quote.

**And it lands on the sum-check line's conclusion from the far side.** GKR says: matmuls are nearly
free, so the cost is the non-linear seams. R1CS-with-constant-weights says: matmuls are *literally*
free, so the cost is the non-linear seams. Bionetta's proving time is a function of exactly one
quantity, the number of non-linearity calls. Two proof systems with nothing in common, the same
cost model. That agreement is worth more than either benchmark.

Its cryptographic contribution is **UltraGroth**, which puts a LogUp-style lookup argument *inside
Groth16*, a protocol with no rounds, by splitting the witness into segments and hashing each
segment's commitment to derive the next one's challenge. One extra pairing, one extra hash. It is
the most interesting proof-system idea in recent zkML and it is sitting in a vendor tech report
that no academic paper cites. [Proof systems](./proof-systems/) has the construction.

What to distrust. It supports **no softmax, no attention, no LayerNorm**, the ReLU family and
nothing else, because the ReLU family is what its free-rescale trick works on. It is not a
transformer system and its numbers do not belong on the tokens-per-minute axis. Its trusted setup
is **per-circuit**, so retraining means a new ceremony. And the constraints themselves are not
public: the SDK ships, the Circom does not, in a system that is deployed for biometric
authentication. See [the paper page](/papers/bionetta/) for the ReLU sign check we would want
somebody to look at.

### ezkl, the toolchain

[[ezkl]] has no paper, and it is the de facto baseline that Jolt Atlas and others benchmark against.
Worth naming because a great deal of what people actually *run* is this, not any of the above.

---

## IV. The VOLE / designated-verifier line

A different bargain entirely, and one that is routinely misreported.

### Mystique (2021)

[[mystique]] is a set of **efficient conversions**, between arithmetic and Boolean, between
committed and authenticated values, and between fixed-point and **IEEE-754 floating point**, on top
of an sVOLE-based interactive ZK substrate. It is the first system here to prove a
production-scale CNN (ResNet-101).

Two things make it structurally distinct, and both are usually lost in the comparison tables. It is
**designated-verifier and interactive**: it produces a *conversation*, not a proof object. The
transcript is bound to one verifier's MAC key, so it cannot be published, posted on-chain, cached,
or checked by a second party, and its reported megabytes are **communication, not proof size**.
Anyone who plots Mystique's "proof size" next to zkGPT's is comparing two different quantities.

And it evaluates non-linear layers as **real IEEE-754 float circuits** rather than quantizing them, 
which is why its accuracy holds across 101 layers, and why no calibration or requantization story
appears in it at all. It is also the source of the FP32 gate counts that the entire [numerics
literature](/numerics/) cites when it declares floats infeasible. Its own prover is dominated by
BatchNorm, the paper measures it at "around 70% of time in both cases", because of those float
conversions.

### Hao et al. (2024) and Lu et al. (2024)

[[hao-et-al]] takes Mystique's substrate and replaces the float circuits with **fixed-point digit
decomposition plus table lookup** for non-linear functions. It gives the cleanest standalone
measurement anyone has of what non-linear dynamic range costs, softmax against ReLU, same system,
same hardware, and the gap is enormous.

But it proves individual **operators**, never an end-to-end model. There is no CNN or transformer
benchmark, and consequently **no accuracy number for any model at any precision**, which matters,
because it swapped out precisely the mechanism (float circuits) that Mystique chose to protect
accuracy through depth, and never measured the cost of the swap.

[[lu-et-al]] is the other VOLE entry, notable mainly for the trade it makes visible: a fast prover
bought with gigabyte-scale communication, and a proof nobody else can check.

---

## V. The dissenters

Three systems that reject a premise everyone else accepts.

### ZIP (2025), quantization is a choice, not a law

[[zip]] refuses to quantize. It proves inference over native **IEEE-754 double-precision** floating
point, and it is the standing counter-example to the claim, repeated in nearly every paper above, 
that floats are infeasible in a circuit.

Its trick is worth understanding exactly. Offline, approximate each activation by a piecewise
polynomial and store the coefficients in a tiny lookup table. Online, the prover computes the
activation *exactly, in double precision*, and feeds **that exact value** forward, the polynomial
output is never used downstream, which is what stops approximation error compounding across depth.
Then it proves the correct, correctly-*ordered* coefficient block was selected (an extended Caulk
lookup plus a private-interval range proof) and that the exact value lies close to the polynomial's.
The activation's proving cost is thereby decoupled from the activation's *complexity*, which is why
it generalizes across GeLU, SeLU and ELU with no redesign.

**But read the guarantee, not the headline.** ZIP does not prove that the activation is the correct
IEEE-754 value. That value is a *witness*, bound only by a relative-error inequality against the
polynomial, so what is proven is that it lies in a **δ-ball** around a certified approximation. An
honest prover puts the exact double in that ball; a malicious one may put anything in it. On GeLU,
its flagship activation, that ball is wide enough to swallow bfloat16's entire machine epsilon an
order of magnitude over. The precision is a property of *what the honest server computes*, not of
*what the proof enforces*. The full argument is on [the numerics page](/numerics/).

It is a small-model system and not a throughput competitor. Its value to this SoK is
philosophical: it proves that quantization is a **design choice made to fit the prover**, not a law
of nature.

### Range-Arithmetic (2026)

[[range-arithmetic]] is the third camp in the numerics debate. It keeps **fixed point**, but proves
the *rounding* with range proofs rather than bit decomposition, avoiding Boolean encoding and large
lookup tables entirely. It descends from SafetyNets rather than from the SNARK line: interactive,
sum-check based, **integrity only, not zero-knowledge.** Privacy is explicitly future work.

### NANOZK (2026)

[[nanozk]] claims layerwise proofs of constant size per layer regardless of model width, and its
threat model is the right one, a provider silently serving a cheaper or more aggressively quantized
model. It also claims its lookup approximations preserve perplexity *exactly*, which is an
extraordinary claim.

:::gap  Treat NANOZK with suspicion
It is an unreviewed single-author preprint whose abstract contains an unsubstituted `METHOD`
placeholder. We have kept it in the table and flagged it rather than quietly dropping it, because
excluding a paper you dislike is how a survey starts lying. But do not build on it.
:::

---

## The trajectory

Put the lineages on one axis, time, and hold the model roughly constant, and the shape of the
last two years is unmistakable.

{{ chart:timeline }}

Read that with the rest of this page in mind, because the curve is not as clean as it looks. It
is a log scale, so each gridline is a factor of ten. Some of the drop is genuine protocol
progress; some of it is hardware; some of it is a system proving a *weaker claim* than the one
above it and being plotted next to it anyway. The point of the chart is not the slope, it is
that the slope is steep enough that **the interesting question is no longer "is this fast enough
yet" but "is this proving what you think it is."**

---

## What the comparison actually shows

Three things fall out of reading them side by side.

**The lineages are not competing on the same axis.** Sum-check systems pay for non-linearities and
rounding; lookup systems pay for table size; R1CS compilers pay for constraint count and commitment
consistency; VOLE systems pay in communication and give up a public proof. A throughput ranking
across all four is a ranking across four different cost models, four different bit widths, and, in
the VOLE case, a different *kind of object* being measured.

**The best ideas were about the statement, not the protocol.** DeepProve's biggest win is not a
faster sum-check; it is realizing that you can certify a sequence in one pass instead of proving
generation. zkGPT's is realizing that rounding, not arithmetic, is the cost. zkPyTorch's is
realizing that quantization is really a *field-size* decision. SafetyNets' was realizing that a
neural network is an arithmetic circuit at all. **The protocol improvements are downstream of
someone reframing what needs to be proven.**

**And the field has a citation problem.** The [graph](/graph/) shows the proving and privacy
literatures do not cite each other at all, and the [numerics primitives](/numerics/) form a third
island read by neither. Meanwhile the systems that *do* cite each other propagate errors: a
distilled GPT-2 quoted as GPT-2, a single forward pass converted into a throughput figure, a
competitor's mechanism mischaracterized in a related-work sentence. Almost every such error in this
SoK was found by opening the PDF that the citing paper cited. That is not a high bar, and it is not
being cleared.
