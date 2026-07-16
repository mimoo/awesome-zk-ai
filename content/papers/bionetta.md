---
title: Bionetta
paper: bionetta
status: reviewed
---

Read the threat model before you read anything else, because every number in this paper is
downstream of it and the abstract does not tell you.

Every other system in [proving inference](/zk-inference/) is **MLaaS**: a server holds a valuable
model, runs it on your input, and proves it did so honestly. The weights are the secret. The
server is the prover. Bionetta is the **exact inverse**, the *model* is public, the *input* is
private, and the *client* is the prover, on their phone. The motivating application is a biometric
one: prove that your face matches an enrolled template, without handing anybody your face.

The library's own README says the limit out loud, in a warning box, which the paper never does:

:::quote{src="Bionetta README (Anonymous1725/Bionetta)" sec="About"}
Despite astounding performance, the library is **not** intended for **private model weights** +
**public input** proving. The library is designed only for **public model weights** +
**private/public input** proving!
:::

So it is not competing with [[deepprove]] or [[zkgpt]], whatever the benchmark tables suggest. It
is answering a question nobody else in this corpus answers, and it is the only entry here whose
prover is a phone.

## What is new

**Circuit-embedded weights**, and it is almost embarrassingly simple. R1CS charges nothing for
multiplication by a *constant*. If the weights are public, they do not have to be signals, they
can be compiled into the constraint system as constants. So every linear layer, every convolution,
and every BatchNorm folded into one, costs **exactly zero constraints**. Not "cheap". Zero.
Proving cost then depends on one quantity: the number of non-linearity calls.

The effect is the largest single lever in the paper: ResNet18 falls from 37.85M constraints to
1.16M, and from 270 seconds to 14. And it is *structurally unavailable* to every MLaaS system in
this SoK, because theirs is the case where the weights are the thing you are hiding. This is the
clearest demonstration in the corpus that **the threat model, not the proof system, is the dominant
term in the cost.**

It also lands on the same conclusion the sum-check line reached from the opposite direction. GKR
says: matmuls are nearly free, so the money is in the non-linear seams. R1CS-with-constant-weights
says: matmuls are *literally* free, so the money is in the non-linear seams. Two entirely different
proof systems, one cost model. That agreement is worth more than either paper's benchmark.

**UltraGroth** is the cryptographic contribution, and it is the thing that should not be buried in
a vendor tech report. Lookup arguments need a verifier challenge sampled *after* the witness is
committed, LogUp's rational-sum identity is checked at a random point, and the prover must not
know the point in advance. Groth16 has no rounds, which is exactly why nobody puts lookups in it.

UltraGroth adds rounds. The witness is split into $d+1$ segments; each segment gets its own $\delta_i$
and its own commitment $\pi_C^{\langle i \rangle}$; the commitment is hashed to derive the *next*
segment's challenge, and the challenges are carried as public signals the verifier recomputes. The
proof grows to $\pi_A, \pi_B, \pi_C^{\langle 0 \rangle} \dots \pi_C^{\langle d \rangle}$, and
verification goes from three pairings to four. That is the entire price: **one pairing and one hash
buys lookup arguments inside Groth16.** Completeness, soundness and zero-knowledge are proved in
GGM + ROM in Appendix A.

What it buys downstream is the range check, which, per [the numerics page](/numerics/), is where
the whole proof actually lives. A ReLU's $b$-constraint bit decomposition becomes $b/w$ lookups for
limb size $w$, giving prover complexity $O(2^{w+1} + bL/w + 4L)$ over $L$ range checks, i.e.
$O(N/\log N)$. The paper solves for the optimal $w$ ($2^w w^2 = Lb / 2\log 2$, landing near 18);
the shipped SDK defaults to 15.

**The rescale seam is free.** This is the fact that changes how the numerics page has to be
written, and Bionetta states it in one line and moves on.

ReLU already decomposes its input into bits, that is how you get a sign out of a field that has no
order. But *once you have the bits, a right shift is free*: you simply drop the low ones. So the
precision cut, the rescale, the thing every other system in this corpus pays for at every seam, 
costs **nothing extra when it rides on a ReLU it was already paying for**. The paper's proposition
is that `ReLU(x) >> ρℓ` costs $b+1$ constraints, which is the same $b+1$ as a bare ReLU.

Everyone else fuses seams to make them *cheaper*: [[zkgpt]]'s constraint fusion, [[deepprove]]'s
delayed requantization, [[jolt-atlas]]'s i64 accumulate-and-rebase. Bionetta fuses the seam into an
operation whose cost it had *already spent*, which makes it not cheaper but free. It is the
strongest form of the result, it is the fourth independent discovery of it, and it cites none of
the other three for it.

## What it actually proves

One forward pass of a convolutional or fully-connected network, in fixed point with $\rho$
fractional bits, over a **public** model, on a **private** input, under a **per-circuit** Groth16
trusted setup.

Every clause there is load-bearing:

- **One forward pass.** No tokens, no sequence, no autoregression. `claim_kind: pass`.
- **CNNs and MLPs only.** The supported non-linearities are ReLU, LeakyReLU (with $\alpha$ a power
  of two, anything else is rejected), ReLU6, HardSigmoid and HardSwish. That is the ReLU family,
  and the selection is not arbitrary: those are precisely the activations whose cost the sign-bit
  decomposition *already pays for*. **There is no softmax**, the SDK's `ActivationOps.from_keras`
  maps `tf.keras.layers.Softmax` to `NOT_SUPPORTED`, and therefore no attention, no LayerNorm, no
  transformer. It is not on the tokens-per-minute axis and should never be put there.
- **Per-circuit trusted setup**, which cuts two ways and both are interesting. The cost: retraining
  the model means a new ceremony, which makes this unusable for anything that updates its weights.
  The benefit, which nobody states: a Groth16 verification key **is** a commitment to the exact
  circuit, and the circuit **is** the architecture. This is the strongest architecture-pinning in
  the corpus, stronger than [[zkaudit]]'s public-architecture convention, and it means the
  precondition of the Fiat–Shamir/GKR attack (*the prover chooses the circuit*) is
  cryptographically out of reach here. Bionetta is one of the two systems in this SoK the attack
  cannot touch, and it got there for free, as a side effect of a design choice made for other
  reasons.

## The benchmarks, and what they actually settle

Two results in Bionetta's Table 4 are more useful to this SoK than its own headline, and neither
is about Bionetta.

**The Halo2 story is wrong in the half nobody checks.** Our own [proof systems](/zk-inference/proof-systems/)
page says what everyone says: PLONKish is the slow-prover/fast-verifier bargain, and you tolerate
the prover because kilobyte proofs and millisecond verification are what make on-chain settlement
possible at all. Bionetta measured it. As **ezkl** actually ships, proofs are hundreds of kilobytes,
verification keys reach tens of megabytes, and **verification takes seconds to tens of seconds**, 
40.6 s on MobileNetV2, behind a proving key of 76 GB. None of that is going on a chain. Halo2 *can*
be configured for small proofs; the toolchain people deploy is not, and until now nobody had
published the numbers. Meanwhile [[zkml-kang]], the *other* Halo2 system, on the same hardware and
the same models, verifies in 12–23 ms with 5–7 kB proofs. **The two most-deployed PLONKish zkML
toolchains do not have the same verifier profile, and the literature treats them as one row.**

**zkCNN is still the fastest prover on small models, five years on.** Bionetta beats it only above
roughly 2M parameters, and loses to it below, [[zkcnn]] proves LeNet5 in 1.05 s against Bionetta's
3.75 s. What zkCNN pays is what GKR always pays: 23–43 kB proofs and verification in the hundreds of
milliseconds to seconds. The 2021 trade has not moved. Only the models have.

## What to distrust

**The comparison is not the comparison it looks like.** Bionetta's linear layers are free *because
its model is public*. ezkl's, ZKML's and zkCNN's are not free because theirs are not. A great deal
of the headline gap is therefore not a proof-system result at all, it is the threat model, showing
up in the constraint count. The paper never separates the two, and a reader skimming Table 4 will
attribute to UltraGroth a win that belongs to a weaker security setting. (To be fair to the paper:
its own Table 5 *does* isolate the two effects, and it is the most honest table in the report. It
just is not the one anybody will quote.)

**The precision result is real, and it points somewhere the paper does not look.** Bionetta measures
relative error against TensorFlow at $\rho \in \{15, 30, 45, 60\}$ and gets $5.2\times10^{-3}$ down
to $9.4\times10^{-7}$, four orders of magnitude of accuracy, while the constraint count *does not
change at all*, because the bit decomposition is over the 254-bit field element either way. This is
[[deepprove]]'s "four more bits costs under one percent" finding, reproduced in a completely
different proof system, and neither paper knows about the other. See the
[open question](/numerics/) it jointly sharpens. (The shipped SDK's default is $\rho = 15$, the
*least* accurate setting the paper measured.)

**The polynomial-activation argument contradicts [[safetynets]], and nobody has noticed.** Bionetta
rejects polynomial activations for a specific reason: a degree-$d$ polynomial costs $d$ constraints
per value, but *raises the precision of the result by $\rho d$ bits*, forcing a precision cut that
costs $\approx b$. "The benefit of $d$ constraints per value is lost in the overhead of precision
cuts." Now read [[safetynets]], whose entire cost advantage, a few percent of overhead, three to
six orders of magnitude better than anything since, comes from quadratic activations having **no
rescale seam at all**. Both claims are in this SoK. They cannot both be the whole truth, and the
reconciliation (SafetyNets is shallow, and precision growth is exponential in depth) is a paragraph
nobody has written.

:::audit  The ReLU sign check, and the constraint that is not there
**Unverified, and the thing we would most want somebody to check.**

The paper's own reasoning for its ReLU cost (§4.3): decompose $x$ into $b$ bits, boolean-constrain
each with $x_i(1-x_i) = 0$, that is $b$ constraints, then one more for the output. Total $b+1$.
The shipped SDK prices `ActivationOps.RELU` at exactly **255** under Groth16, with the comment
*"costs below are specified manually based on the current Circom implementation"*. And
$255 = 254 + 1$, with $b = 254$ for BN254.

**That count leaves no room for a canonicity check, and BN254 needs one.** $2^{254} > p$, so a
254-bit boolean decomposition does *not* uniquely determine a field element. For any
$x < 2^{254} - p$, about $0.32p$, which is every activation any real network will ever produce, 
the bit string of $x + p$ satisfies every booleanity constraint and recomposes to $x \bmod p$ just
as well. And its bit 253 is **set**. Since Bionetta decides the sign by reading bit $b-1$, the
paper deliberately puts the negativity threshold at $2^{b-1}$ rather than the conventional
$(p-1)/2$, and flags the choice as a convenience, the malicious decomposition makes a *positive*
activation read as *negative*, and ReLU returns zero.

This is the textbook Circom `Num2Bits` versus `Num2Bits_strict` distinction. The strict version
adds an alias check against $p$ and costs roughly double, which is consistent with 255 being the
unstrict one. If that is what the circuit does, a malicious prover can zero out any ReLU it
chooses and still produce a verifying proof, and in the biometric application, a prover who can
choose the network's activations is a prover who can forge an authentication.

**We cannot confirm it.** `codegen/generator.py` clones a repo called `bionetta-circom`, and that
repo is not public, the Python SDK ships, the constraints do not. So the range checks, which are
[the entire proof](/numerics/), are the one part of a deployed biometric system that cannot be
read. That is the finding even if the bug is not there.
:::

:::gap  It cites nobody who solved its problem
Bionetta derives a fixed-point quantization error bound from first principles in Appendix C. That
is the subject matter of [[secfloat]], [[garg-fp]] and [[zklp]], none of which it cites. A
full-text scan of the PDF returns **zero** occurrences of "MPC", "homomorphic", "SIRNN",
"Cheetah", "SecFloat", "ZKLP" and "Mystique". It is the newest node in the corpus and it walks
[the bridge](/numerics/bridge/) exactly as far as everyone else at the centre of the column
does: not at all.
:::
