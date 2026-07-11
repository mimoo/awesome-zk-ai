---
title: What each system actually built
section: private-inference
order: 25
lede: >-
  Four 2PC systems in a single lineage, each citing and reimplementing its predecessor,
  plus one FHE outlier that is not in the same setting and should not be put in the same
  ranking. Read one by one, with attention to what the evaluation is quietly doing.
papers: [iron, ciphergpt, bolt, nimbus, bootstrapping-fhe]
status: draft
---

{{ papers:secure_inference_2pc }}

This cell has an unusually clean genealogy. [[iron]] starts it; [[ciphergpt]], [[bolt]] and
[[nimbus]] each cite their predecessors and each claim to beat them; [[bootstrapping-fhe]] cites all
four and then does something else entirely. Every one of them is semi-honest, every one of them
publishes the model architecture, and not one of them produces a proof — see the threat-models page
for what that does and does not leave you with. What follows is what each actually contributed, and
where its evaluation is doing work its text does not acknowledge.

{{ table:secure_inference_2pc }}

## The 2PC hybrid line

**[[iron]]** — NeurIPS '22, and the paper that created the cell. Two contributions. The first is a
*compact packing* trick for the HE matrix multiplication: prior 2PC inference had been built for
CNNs, where the linear layer is a matrix-**vector** product, and Cheetah's encoding wastes ciphertext
slots when you extend it to the matrix-matrix products a transformer is made of. [[iron]] packs
more plaintext into each ciphertext while preserving the product's structure. The second is a set of
Softmax, GELU and LayerNorm protocols built on SIRNN's OT-based library, with the exponentiation in
Softmax specifically optimized.

Its most durable design decision is the one it argues for rather than the one it measures: [[iron]]
hides the intermediate activations of *every* layer, and it explicitly attacks THE-X for revealing
each non-linear layer's inputs to the client. The 2PC line has held that line ever since, and it is
why "private inference" in this cell means something stronger than it does in the HE-with-shortcuts
literature.

*Where the evaluation is doing work:* [[iron]] benchmarks in a **LAN setting only**. Its own reported
costs are therefore the most favourable ones a communication-bound protocol can be given, and — more
importantly — the number everyone else quotes as "Iron" was never measured by [[iron]] at all. It
comes from [[bolt]]'s reimplementation, under a WAN. And [[iron]]'s LayerNorm optimization, which
folds the normalization weights into the following linear layer, is *wrong* — it breaks the residual
connection, and [[bolt]] removed it before benchmarking. The cost-model page and the section index
work through both of these; they are the two most important facts about this paper and neither is in
it.

**[[ciphergpt]]** — ePrint '23, and the odd one out in the best way: it is the only system in this
cell that targets **GPT rather than BERT**, and therefore the only one that has to confront
generation.

Three protocols. (1) A **sVOLE-based matmul** specialized for autoregression: each generated word is
one inference, each produces an *unbalanced* matrix product, and [[ciphergpt]] batches those into a
single unbalanced matmul over subfield VOLE, which is efficient exactly in the regime where one
dimension dwarfs the other. (2) A **spline GELU**: split the curved region into equal-length
intervals, fit $y = ax + d$ on each, shift the whole curve so the region starts at zero (so you never
have to determine the sign first), and index a lookup table on the *high bits* of the shifted input
to recover the interval's coefficients. This is structurally a lookup argument, which is the point
the non-linearities page builds on. (3) The **first secure top-K sampling protocol** — a
shuffling-based top-K selection followed by a sampling step costing a handful of comparisons and
multiplexers.

That third one is the capability the verifiability column simply does not have. [[jolt-atlas]] and
[[zkgpt]] prove a forward pass; nobody on that side proves a stochastic decode step. [[ciphergpt]]
computes one under encryption.

*Where the evaluation is doing work:* [[ciphergpt]] compares against a [[bolt]] it **built itself**
("Since Bolt is still unavailable, we implemented it based on SIRNN with Ferret OT and followed the
parameters given in their paper"), and it implemented the secret-shared shuffle its own top-K needs,
because that was not public either. It also evaluates in a LAN setting only. Its component-level
speedups over "SOTA" are therefore ratios against its own code, on the network most favourable to
the incumbent.

**[[bolt]]** — IEEE S&P '24. The engineering high-water mark of the line, and the most carefully
reported paper in it. Cryptographically it does two things: an alternative interpretation of
ciphertext-plaintext matrix-matrix multiplication that stops wasting ciphertext slots, plus a
baby-step giant-step strategy to kill the rotations that packing would otherwise cost; and, for the
non-linears, high-degree piecewise polynomials with a Horner-scheme preprocessing trick that roughly
halves the multiplication count when the coefficients are known ahead of time. The HE matmul is good
enough that after it lands, **the non-linears are essentially the entire remaining communication
bill**, which is the fact the rest of this section is organized around.

It is also the paper that pinned [[iron]]'s cost, found [[iron]]'s LayerNorm bug, confirmed it with
[[iron]]'s authors, and published the correction in an appendix. That is the right behaviour and it
should be said plainly.

*Where the evaluation is doing work:* **word elimination.** [[bolt]]'s headline communication
advantage over [[iron]] is not purely a protocol result. It ranks input tokens by their attention
scores, obliviously bitonic-sorts them, and *discards the below-median half of the sequence* before
the encoder stack runs. It is oblivious, it is disclosed, and its accuracy cost is small — but it is
a **model change**, not a protocol improvement, and it is responsible for a large fraction of the
reported factor. To [[bolt]]'s enormous credit it reports every number both with and without word
elimination, so the honest protocol-versus-protocol row is right there in the paper. It is not the
row that gets quoted downstream.

**[[nimbus]]** — NeurIPS '24, the freshest 2PC result, and the one with the best *idea*.

Two contributions, and they attack the two halves of the cost separately. For the linear layers, a
**client-side outer product**: model weights are static, so the server can ship *encrypted* weights
to the client during a one-time setup phase, which eliminates input communication in the online
phase entirely and — because the input no longer has to be sent — permits a row-wise encoding that
computes the homomorphic matrix product as an outer product with compact output ciphertexts. For
the non-linear layers, **distribution-aware approximation**: rather than minimizing approximation
error uniformly over an interval, [[nimbus]] measures the actual activation distribution at each
encoder depth and minimizes the *probability-weighted* error, which lets it collapse GELU to a
single quadratic piece where prior work used two pieces of degree three and six — and then, because
low-degree polynomials accumulate less fixed-point error, to shrink the ring and the scale as well.

*Where the evaluation is doing work:* three things. First, its baseline is **BumbleBee**, not
[[bolt]] and not [[iron]], so its headline factor is not commensurable with [[bolt]]'s. Second, the
paper's own §1 states an end-to-end range that silently merges two different baselines; §7 separates
them, and the abstract's figure is the correct one. Third — and this is a deployment fact rather than
an evaluation trick — the client must now *store the entire encrypted model on disk* and stream it in
as layers are consumed. [[nimbus]] is candid that 2PC clients were already server-class machines, but
its design makes the client heavier still.

## The FHE outlier

**[[bootstrapping-fhe]]** — ePrint '26. Do not put this in the same ranking as the four above; it is
not in the same setting. It is pure CKKS FHE, non-interactive: the client encrypts, leaves, and the
server evaluates the whole transformer on ciphertext. The paper names the setting **NISTI**.

Its thesis is a genuine inversion. In leveled FHE, bootstrapping is the thing you *avoid* — [[bolt]]
chose leveled BFV precisely because bootstrapping was "still prohibitively expensive" — and the
standard response is to pick parameters supporting a large multiplicative depth, which inflates
ciphertext size and therefore everything else. [[bootstrapping-fhe]] argues the opposite: make each
bootstrap do more work, and the prescribed depth collapses. Concretely, **functional bootstrapping**
embeds the target non-linearity into the periodic function the bootstrap already evaluates, so GELU
and $\exp$ are computed *inside* the noise refresh; a **functional S2C** fuses the linear layers
($y = xW + b$) into the slot-to-coefficient transform, so they cost nothing separately; and the
approximation underneath is a **trigonometric minimax** fit, for which the paper proves existence
and derives a trigonometric Remez algorithm. The prior state of the art used a Fourier series, which
is optimal in $L^2$ but not in $L^\infty$ — and worst-case error is the right target when a single
bad activation ruins the inference.

The result is a system whose communication is a few ciphertexts rather than a transcript, which is
the entire reason to tolerate FHE's compute.

*Where the evaluation is doing work:* two things, both disclosed and both easy to miss. The
benchmarked model is **BERT-DyT** — LayerNorm has been replaced by Dynamic Tanh and the network
distilled from BERT — so the operator that is hardest to evaluate homomorphically has been designed
out rather than approximated. And the reported per-query cost is **amortized over a batch of
sequences**: it is a throughput figure, where every 2PC number in the table above is a
single-inference latency figure. A NISTI service answering one query at a time does not see it, and
the paper does not claim it would.

:::gap  Nobody has read the systems this line actually descends from
Four names carry most of the load in these five papers' related work and none of them is in this
repo: **Cheetah** (the matmul baseline [[iron]] improves on), **SIRNN** (the OT protocol library
every non-linear in the 2PC line is built from), **THE-X** (the weaker-privacy HE approach [[iron]]
defines itself against), and **BumbleBee** (the actual baseline [[nimbus]] beats). Two more are
load-bearing for claims made elsewhere in this section: **MOAI**, [[bootstrapping-fhe]]'s baseline,
and **Mosformer**, the only maliciously-secure transformer inference system anyone in this cell
cites — and it buys that security by adding a third party. Until those are read, this section is
reasoning about a lineage from its endpoints.
:::
