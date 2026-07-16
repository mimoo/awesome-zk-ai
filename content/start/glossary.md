---
title: Two dialects
section: start
order: 30
lede: >-
  The verifiability literature and the privacy literature do not cite each other once. They
  have not harmonised their vocabulary either. They use different words for the same
  operation, the same word for different operations, and each has words the other simply
  lacks. This is the translation table.
papers: [deepprove, zkgpt, zkllm, zkpytorch, jolt-atlas, zip, hao-et-al, zklp, secfloat, prob-truncation, iron, bolt, ciphergpt, nimbus, bootstrapping-fhe, mystique, lu-et-al, zkml-kang, ezkl, zktorch, zkml-survey]
status: reviewed
---

## Why a glossary is a finding here

This SoK's central structural result is computed on every build and rendered in the
[citation graph](graph/): **no paper in the verifiability column cites any paper in the privacy
column, or the reverse.** Not rarely, not at all. Two communities work the two columns of the
same 2x2, bottleneck on the [same three operators](nonlinearities/) (GELU, Softmax, LayerNorm),
publish at the same venues, and do not read each other.

A vocabulary is what a community builds by reading itself. So the disconnection has a linguistic
consequence, and it is the reason this page exists:

> **Two literatures that do not cite each other have not agreed on what to call anything.**

They have different words for the same operation. They have the same word for different
operations, which is worse, because it lets a reader believe they have understood a paper they
have not. And each has a large vocabulary for which the other has no word at all, which is usually
a sign that one of them is not thinking about the problem.

So this is not a page of definitions of crypto terms. It is a **translation table**, and its
organising question is, for each concept: *what does each side call it, and does the other side
even have it?*

Every equivalence below was checked against the PDFs in `references/`. The ones we could not
check, we did not assert, they are in [the gap at the bottom](#what-we-would-not-assert), and
that list is the more important half of the page.

## The root of the split: a ring and a field

Before the vocabulary diverges, the substrate does, and almost everything else follows from it.

**The privacy column computes in a ring**, $\mathbb{Z}_{2^\ell}$, integers modulo a power of two.
That is not an aesthetic choice: secret sharing and oblivious transfer are cheapest there, and the
hardware word is already a $\mathbb{Z}_{2^{64}}$ element. **The verifiability column computes in a
prime field**, $\mathbb{F}_p$, because that is what a polynomial commitment and a sum-check need.

The words follow the substrate exactly. *Ring* is a load-bearing term in [[iron]], [[bolt]],
[[ciphergpt]], [[nimbus]] and [[prob-truncation]], and does not appear in [[deepprove]], [[zkgpt]],
[[zkllm]], [[zkpytorch]] or [[jolt-atlas]] at all. *Field* runs the other way.

And the consequence is not cosmetic. $\mathbb{Z}_{2^\ell}$ hands you **two's complement**, so a
negative number is a bit pattern, a sign is a bit, and an arithmetic right shift *is* a
floor-division by a power of two. $\mathbb{F}_p$ hands you none of that: negatives are a
convention ($-5$ is "the element $p-5$, and we all agree to read it that way"), there is no sign
bit, and [there is no division](numerics/). The same operation is therefore *free-ish* on one side
and *the single most expensive primitive* on the other.

[[hao-et-al]] is the one paper that had to translate between the two, and it says so precisely, 
notice that it reasons about two's complement while working in a field:

:::quote{src="Hao et al." sec="§2, Technical Overview — Truncation"}
To address this challenge, an important observation is that the truncation operation conducts an
arithmetic right shift on the 2’s complement representation of the real value of x, rather than
its embedded field representation.
:::

Hold that sentence. It is the hinge of the whole table below.

## The translation table

Concepts that exist in both worlds, under different names. The last column is the one to read
carefully: **"same operation" and "same idea, different guarantee" are very different claims,** and
collapsing them is exactly the sloppiness this SoK exists to attack.

| Concept | Verifiability (zkML) calls it | Privacy (MPC / 2PC / FHE) calls it | How equal, really |
|---|---|---|---|
| Squeeze a wide accumulator back down after a multiply | **requantization** ([[deepprove]]), **rescale** ([[zkgpt]], [[zkllm]]) | **truncation** ([[prob-truncation]], [[ciphergpt]], [[nimbus]], SIRNN) | **Same kernel.** Both are a floor-division by a power of two. zkML wraps it in an extra affine map. |
| Round *less often* by merging adjacent seams | **constraint fusion** ([[zkgpt]]); **delayed requantization** ([[deepprove]]) | **fused truncation-and-upcast** ([[nimbus]]) | **Same move, three names.** Independently invented on both sides. |
| The precision knob that trades accuracy for cost | **quantization bit width**; scale **and zero-point** | **fixed-point scale** (a single global fractional scale), and the **ring size** | **Same role, different generality.** The zero-point is zkML's alone. |
| Keep the weights from the counterparty | **commitment** to the weights (KZG, BaseFold) | **secret-sharing** / homomorphic **encryption** of the weights | **Both hide. Only one binds.** See below — this row is the 2x2. |
| The counterparty might cheat | **soundness** against a **malicious prover** — assumed on day one | **malicious security** — the goal none of the five systems reach; the four 2PC systems assume **semi-honest**, and the FHE one only that the **server cannot decrypt** | **Not the same property.** See below. |
| The two parties actually deployed | **prover** (holds the model) / **verifier** (holds the prompt) | **server** (holds the model) / **client** (holds the prompt) | **The same two parties.** Different guarantee purchased. |
| Make a non-polynomial computable | **lookup argument** ([[zkllm]]'s `tlookup`, Lasso); piecewise polynomial ([[zip]]) | piecewise polynomial fitted by **minimax / Remez** ([[bolt]]); spline + LUT ([[ciphergpt]]); **functional bootstrapping** ([[bootstrapping-fhe]]) | **Converged strategy, one-sided theory.** See below. |
| "The cost" | **prover time**, proof size, peak prover memory | **communication** (bytes) and **rounds**; for FHE, **bootstraps** | **No conversion exists.** Neither literature's benchmark can be expressed in the other's units. |

### Rescale *is* truncation, and it is the hardest primitive in both worlds

This is the row the rest of the page hangs on, and it is exact enough to be worth proving.

[[deepprove]] describes the problem in the vocabulary of quantization:

:::quote{src="DeepProve" sec="§4, Requantization"}
To address this, DeepProve employs re-quantization after every few layers to reduce the bit-length
of intermediate values back to a manageable size.
:::

[[prob-truncation]] describes the identical problem in the vocabulary of secret sharing, and, in
one sentence, uses **both** dialects' words for it:

:::quote{src="Probabilistic truncation in PPML" sec="Abstract"}
Taking truncation protocols as an example, a typical PPML uses fixed-point arithmetics, and the
truncation protocol is often needed to re-scale the range of the underlying data.
:::

[[ciphergpt]] gives the ideal functionality, and it is a right shift: $\texttt{Trunc}(x, s)$ returns
$x \gg s$. [[deepprove]]'s divisor is a power of two precisely so that "the division can be
considered as a right shift". They are computing the same function.

**Where they are genuinely not equal, and it matters:** zkML's requantization is the *more general*
operation. It rescales from one calibrated per-tensor scale to a different one, so it carries an
arbitrary float ratio $S_xS_w/S_y$ and an additive **zero-point**, neither of which appears in the
MPC papers, they carry a single global fractional scale and no zero-point at all. But strip the
affine wrapper off and the hard kernel is the same floor-division, with the same negative-number
problem, and it is [the dominant cost on both sides](numerics/). The right statement is *nested*,
not *identical*: **MPC's truncation is the kernel of zkML's requantization.**

And there is one direction the transfer provably cannot run, which is the exception that proves the
rule: MPC's cheap **probabilistic truncation** accepts a small per-operation failure probability, and
in ZK the prover chooses the input, so a rare failure is not rare, an accuracy cost becomes a
soundness hole. That argument is [made in full on the numerics page](numerics/), and it is about
*one* technique, not a licence to ignore the rest.

### Commitment and secret-sharing both hide the weights. Only one binds them.

This row *is* the 2x2, expressed as vocabulary.

The word **commitment** does not appear in [[iron]], [[bolt]], [[ciphergpt]], [[nimbus]],
[[secfloat]] or [[prob-truncation]]. The words **secret sharing** do not appear in [[deepprove]],
[[zkgpt]], [[zkpytorch]], [[jolt-atlas]] or [[zip]]. Each column has exactly one mechanism for
"the weights are not in the clear", and it is not the other's.

They look like alternatives. They are not, because they buy different things:

- A **commitment** is *hiding* **and *binding***. The prover cannot swap the model after the fact.
  That binding is the whole product.
- A **secret-sharing** (or an HE encryption) of the weights is *hiding* and **not binding**. The
  server holds its own share and may compute with whatever it likes.

Which is why the [threat-models page](threat-models/) can put the same entry in the last row of
every private-inference column, **output correctness: not guaranteed**, and why the privacy
column's honest summary is that it protects the *query*, not the *answer*. The two columns are not
two ways of doing one thing. They are the two halves of one thing, and neither has the other half.

### "Soundness" and "malicious security" are not translations of each other

Both are the answer to "what if the counterparty deviates", so the temptation is to map them onto
each other. Do not.

**Soundness** is a property of an *argument system*: a cheating prover cannot convince the verifier
of a false statement. It says nothing about privacy, and in the verifiability column a **malicious
prover is the default assumption**, it is what the system is *for*. The word appears throughout
[[deepprove]], [[zkgpt]], [[zip]], [[hao-et-al]] and [[zklp]].

**Malicious (active) security** is a property of a *protocol*: simulation-based security that
survives a party deviating arbitrarily, covering privacy *and* correctness. In the privacy column
it is an **aspiration, not a baseline**, every 2PC system in [the private-inference
section](private-inference/) assumes a semi-honest counterparty, which the
[threat-models page](threat-models/) shows is the single most load-bearing assumption they make.

The word **soundness** does not occur in [[iron]], [[bolt]], [[ciphergpt]], [[nimbus]],
[[bootstrapping-fhe]], [[secfloat]] or [[prob-truncation]]. Not once, in any of them. That is not a
vocabulary quirk; it is a description of what those protocols do not promise.

So the honest cross-dialect sentence is not "soundness ≈ malicious security". It is:

> **The adversary that verifiability assumes on day one is the adversary that privacy hopes to
> handle one day.**

### Both sides approximate the same three curves. Only one side has the theory.

Both columns converged on the same technique for GELU, Softmax and LayerNorm: **piecewise
approximation, with the piece selected by a table indexed on the high bits of the input**, which is
what a lookup argument is, and also what [[ciphergpt]]'s spline GELU is. That convergence is
[worked through on the non-linearities page](nonlinearities/).

The vocabulary of *approximation theory*, though, sits almost entirely on the privacy side.
[[bolt]] fits GELU with the **Remez** exchange algorithm and explains exactly why:

:::quote{src="BOLT" sec="§5.2, Accurate GELU Approximation"}
we utilize the Remez method [61] to find the optimal polynomial coefficients. Unlike polynomial
interpolation with gridsearch, the Remez method guarantees to find an optimal polynomial
approximation by iteratively adjusting the polynomial coefficients to minimize the maximum error
(also known as the maximum deviation) between the polynomial and the target function over the
specified interval.
:::

[[bootstrapping-fhe]] goes further and proves the existence of a **trigonometric minimax**
approximant, deriving a trigonometric Remez algorithm to find it, on the argument that worst-case
($L^\infty$) error is the right metric when one bad activation ruins the run.

Neither *minimax* nor *Remez* appears in [[deepprove]], [[zkgpt]], [[zkllm]], [[zkpytorch]],
[[jolt-atlas]] or [[zip]]. Among the ZK *systems* we hold, the words occur only in [[zklp]], 
which is, predictably, [one of the four papers that reads both literatures](bridge/). The one other
ZK-side hit is secondhand: [[zkml-survey]] records "Remez-style approximations" in the older
verifiable-training systems VeriML and zkMLaaS, whose PDFs we do not hold.

**Part of that absence is entirely justified, and it is worth saying so.** A zkML lookup table over
a quantized domain is not an approximation at all: it is *exact* on every input in the table, so
there is no error curve to minimise and no need for Remez. The asymmetry is a real consequence of a
real design difference, not simple ignorance.

:::gap  But the excuse runs out at exactly one system
[[zip]] does not use tables to be exact, it fits **piecewise polynomials** to GELU, SeLU and ELU
and proves the result lies within a relative-error ball $\delta$ of the fit. That is an
approximation problem with a worst-case error bound, which is the precise problem the Remez
exchange algorithm solves optimally and which [[bolt]] and [[bootstrapping-fhe]] both invoke it
for. ZIP surveys Taylor, Chebyshev and splines as its options; minimax and Remez are not among
them.

Whether a minimax fit would shrink ZIP's $\delta$, and therefore shrink the [slack available to a
malicious prover](numerics/), which on its flagship activation is looser than bfloat16's machine
epsilon, is unexamined. It is a one-citation question, and the citation is in the other column.
:::

### "Cost" does not survive translation at all

The last row of the table is the one that most often produces a false comparison, because both
columns publish a headline number and call it performance.

Verifiability counts **prover seconds, proof bytes, and peak prover memory**. Privacy counts
**communication bytes and rounds**, and a 2PC runtime is not a property of a protocol at all but a
function of a network the paper picked, which is [the argument of the cost-model
page](cost-model/). The phrase *prover time* does not occur in any of the five private-inference
papers, because there is no prover. The word *communication* is nearly absent from the zkML
provers, because after Fiat–Shamir there is no interaction to pay for.

There is no exchange rate between these units, and nobody has proposed one. A reader who puts a
zkML throughput next to a 2PC bandwidth figure has not made a comparison; they have made a
category error. (The zkML numbers do not even survive comparison *with each other*, see
[what is actually being proven](what-is-proven/).)

## False friends: the same word, different things

The rows above are terms that mean the same thing and sound different. These are worse: they
**sound the same and mean different things**, and each one is a trap a careful reader can fall
into.

### "Semi-honest"

In the privacy column, **semi-honest** describes the *adversary*: the counterparty follows the
protocol but tries to learn more than it should. It is the assumption that makes the protocol fast
and the reason a deviating server is [outside the model entirely](threat-models/).

In the verifiability column, the same word is routinely applied to the **verifier**, and means
something structurally unrelated. [[zkllm]]:

:::quote{src="zkLLM" sec="§3.6, Settings and security assumptions"}
A semi-honest assumption is applied to the verifier: the verifier accurately reports the outcome of
the proof verification (whether it is accepted or rejected) but endeavors to glean additional
information about the LLM (like hidden parameters) beyond merely confirming the correctness of the
inference result.
:::

That is honest-verifier zero-knowledge, a qualifier on the *privacy* property, and the **prover
is still assumed fully malicious.** Grep two papers for "semi-honest", find a hit in each, and
conclude they share a threat model, and you will have inverted the meaning of both. [[zip]] uses
the word the same way zkLLM does.

### "Lookup table"

Both columns say it constantly. They are not naming the same object.

- A zkML **lookup argument** (Lasso, LogUp, [[zkllm]]'s `tlookup`) is an *argument of membership*:
  the prover convinces a verifier that a claimed value really appears in a preprocessed table. It
  buys **integrity**. The table is public.
- An MPC **LUT protocol** (SIRNN-style, [[ciphergpt]]'s $\mathcal{F}_{\mathsf{LUT}}$) is an
  *oblivious evaluation*: two parties jointly read $T[i]$ without either learning $i$. It buys
  **privacy**. The index is secret.

One proves a read happened correctly; the other performs a read without revealing it. They share a
*strategy*, piecewise approximation selected by the high bits, and not a primitive. The strategy
is the transferable thing; the cryptography is not.

### "Malicious"

Appears on both sides, meaning the opposite thing about the world. In the verifiability column it
describes the party you are defending against by default. In the privacy column it names the
security level these systems have *not* achieved. A privacy paper saying "we leave malicious
security to future work" and a verifiability paper saying "sound against a malicious prover" are
not disagreeing; they are not talking about the same corner of the protocol.

## Terms with no counterpart

Where a column has a word and the other has nothing, the vocabulary is telling you what that column
is not thinking about.

### Verifiability only

| Term | One line | Where it does real work |
|---|---|---|
| **sum-check** | Reduce a claim about a sum over the Boolean hypercube to a claim at one random point. Makes matmul nearly free. | [proof systems](proof-systems/) |
| **GKR** | Chain sum-check layer by layer, so a claim about layer $i$ reduces to a claim about layer $i-1$. The spine of the fast provers. | [proof systems](proof-systems/) |
| **PLONKish / Halo2** | Compile the model to a gate table with copy-constraints. The boring, shippable option. | [[zkml-kang]], [[ezkl]] |
| **polynomial commitment** | Commit to a polynomial, later open it at a point. KZG, HyperKZG, BaseFold. The thing that binds the weights. | [proof systems](proof-systems/) |
| **lookup argument** | Prove a value appears in a preprocessed table. Cheap range checks — which is [why it actually changed zkML](numerics/). | [[deepprove]], [[jolt-atlas]] |
| **witness** | The prover's secret input. The value it *asserts* and then must prove consistent. Absent from every MPC paper we hold. | [numerics](numerics/) |
| **Fiat–Shamir** | Replace the verifier's coins with a hash, turning an interactive proof into a posted artefact. Also [the subject of a proven attack on GKR](proof-systems/). | [proof systems](proof-systems/) |
| **folding / accumulation** | Defer verification: fold many instances into one and check the fold. | [[zktorch]] |
| **VOLE / designated verifier** | Very fast prover, non-succinct proof, and the proof is only meaningful to *one* verifier — which kills the "publish it, anyone checks it" story. | [[mystique]], [[lu-et-al]] |
| **succinctness** | The proof is small and cheap to check regardless of the computation's size. The property the whole column is selling. | [proof systems](proof-systems/) |
| **soundness error** | The probability a cheating prover gets away with it. | [proof systems](proof-systems/) |

### Privacy only

| Term | One line | Where it does real work |
|---|---|---|
| **oblivious transfer (OT)** | The workhorse. Receiver gets one of the sender's messages; sender does not learn which. Every comparison and every table read costs OT invocations. | [[iron]], [[ciphergpt]] |
| **secret sharing** | Split a value across parties so no strict subset learns it. Addition is local; multiplication costs a round. | [threat models](threat-models/) |
| **garbled circuits** | Evaluate a Boolean circuit on encrypted wire labels. Constant rounds, large bandwidth. | [private inference](private-inference/) |
| **homomorphic encryption (CKKS, BFV)** | Compute on ciphertext. CKKS is *approximate* — decryption returns the plaintext plus noise. | [[bootstrapping-fhe]] |
| **bootstrapping** | Refresh a ciphertext's noise budget so evaluation can continue. The dominant cost of the non-interactive setting. | [[bootstrapping-fhe]] |
| **packing** | Fit many plaintext slots into one ciphertext so a matmul is a handful of homomorphic operations. Where the 2PC papers spend their linear-layer budget. | [cost model](cost-model/) |
| **semi-honest vs malicious** | The two adversary classes. Every system in this SoK's privacy column is the former. | [threat models](threat-models/) |
| **NISTI** | Non-Interactive Secure Transformer Inference: the client encrypts, sends, and *leaves*. A different game from 2PC, and benchmarking them head-to-head is a category error. | [threat models](threat-models/) |
| **communication / rounds** | The bill. Bytes on the wire, and network round-trips — which is why a Softmax can cost hundreds of rounds and a matmul two. | [cost model](cost-model/) |
| **ring $\mathbb{Z}_{2^\ell}$** | The arithmetic domain. Gives two's complement and a free right shift, which is why truncation is cheaper here than in a field. | above |

### The shared substrate

These belong to neither column, which is exactly why they are [the one place the two literatures
demonstrably touch](bridge/).

| Term | One line |
|---|---|
| **fixed point $Q_{m.f}$** | An integer with an implied binary point: uniform step $2^{-f}$, hard ceiling at $2^m$. Precision everywhere, **no dynamic range**. The format deep learning rejected, and the only one a circuit or a share can cheaply hold. |
| **BF16 / dynamic range** | The format the industry actually runs on: full FP32 exponent, ~7 mantissa bits. Deep learning chose **range over precision**, and fixed point is the opposite trade. This is the whole numerics problem in one row. |
| **floor-division** | $\lfloor x/2^s \rfloor$. Not a field operation. You cannot compute it — you can only guess it and range-check it. Cheap in a ring, brutal in a field. |
| **field embedding of negatives** | $-5$ is stored as $p-5$, by convention, inside a window nothing enforces. The reason [[hao-et-al]] has to reason in two's complement while working in $\mathbb{F}_p$. |
| **calibration set** | The data used to estimate activation ranges. Both columns bet that inference-time activations look like it. In zkML that bet is load-bearing for **soundness**; in MPC, for **accuracy**. Same bet, different thing riding on it. |
| **outliers** | The emergent, structural, large-magnitude activations that appear in transformers past a certain quality. They are what breaks the calibration bet, in both columns. |
| **SIRNN, Cheetah, [[secfloat]]** | The three nodes both columns cite. All three are MPC numerics primitives. The traffic runs one way. |

## Words that are ours, not the field's

Where this SoK has coined a term, it says so. Passing a house coinage off as standard vocabulary
would be the same sin as a false equivalence, one level up.

- **`claim_kind`**, our field in `papers.yml`, tagging what a system's headline number actually
  certifies: a full generated sequence, one token, a single forward pass, or unknown. **No paper
  uses this term.** We introduced it because throughput numbers in this literature are not
  comparable without it, and [that is a finding, not a schema decision](what-is-proven/).
- **"Properties" as a fourth objective**, [[zkml-survey]] gives the canonical taxonomy, and it has
  three slots: training, testing, inference. We [add a fourth](properties/) for systems that prove a
  model *is* something (fair, licensed, uncensored) rather than that a computation ran. **The
  surveys do not have this bucket**; it is our departure from them, and we argue for it rather than
  assuming it.
- **"The rescale seam"**, our name for the join between two matmuls where the accumulator must be
  squeezed back down. The papers describe the thing constantly; none of them names it.
- **"The two columns"**, our shorthand for the verifiability and privacy literatures, from the
  2x2. Nobody in either literature uses it, because [nobody in either literature is looking at the
  other one](graph/).

## What we would not assert

:::gap
A false row in a translation table is worse than a missing one, so here is what we considered and
**rejected**:

**"Quantization" = "fixed-point encoding".** Rejected as an *identity*, kept as a partial row. zkML
quantization is an affine map with a per-tensor scale **and a zero-point**, calibrated post-hoc; the
word *zero-point* does not appear in any MPC paper we hold. MPC fixed-point encoding is a single
global power-of-two scale. They play the same role and are not the same object, and [[nimbus]]
moving to a smaller ring and scale is the same *kind* of move as [[deepprove]] dropping bit width
without being the same *operation*.

**"Lookup argument" = "OT-based LUT".** Rejected outright, and moved to the false-friends section.
One is an argument of membership over a public table; the other is an oblivious read of a secret
index. Same word, same approximation strategy, different cryptographic object. Asserting the
equivalence would have been the exact error this page exists to prevent.

**"Soundness" = "malicious security".** Rejected. Both concern a deviating counterparty; one is a
property of an argument system about a *statement*, the other is simulation-based security of a
*protocol*, covering privacy too. Recorded as an asymmetry of defaults, not a synonym.

**"Prover : verifier" :: "server : client".** Rejected as a *role* mapping, kept as a *deployment*
mapping. The same two real parties appear in both columns, and in both the model owner is the one
holding the secret, but the ZK property in zkML protects the **model owner** from the verifier
(see [[zkllm]] above), while 2PC additionally protects the **client's input** from the server.
Mapping the roles without saying that would hide the entire difference.

**Iron's non-linearities as "truncation".** We could not verify it. Our own
[non-linearities page](nonlinearities/) says [[iron]] composes SIRNN protocols with "bit-width
extensions and truncations"; the word *truncation* does not appear in the [[iron]] PDF we hold. The
claim may be true of the underlying SIRNN protocols and false of Iron's text, or our text
extraction may be lossy. Flagged, not asserted, and not used as evidence anywhere above.

**A "rounds" ↔ "prover time" exchange rate.** There is none, we did not invent one, and the
temptation to is how cross-column comparisons get fabricated.
:::

## What follows from a glossary

If the two columns had a shared vocabulary, the transfers would already have happened, because
once you can *say* that requantization and truncation are the same floor-division, the next
question asks itself.

They are not merely nameable. They are the same open problem: it is the dominant cost in both
columns, its failure mode is an accuracy bug in one and a **soundness** bug in the other, and the
only papers that have looked at both shelves at once are the four sitting at the edge of the
verifiability column with nothing to prove about transformers. The seabed is shared. Nobody lives
there.
