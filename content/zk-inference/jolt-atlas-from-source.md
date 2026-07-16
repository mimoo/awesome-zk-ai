---
title: Jolt Atlas, from the source
section: zk-inference
order: 70
lede: >-
  Everywhere else on this site, Jolt Atlas is described from its paper -- which is terse. This
  page is from the code (github.com/ICME-Lab/jolt-atlas @ b20cdce), read operator by operator.
  The paper says "lookup arguments"; the code has a dedicated, multi-stage protocol for every
  operator, and they are more interesting than the paper lets on.
papers: [jolt-atlas, deepprove]
status: reviewed
---

The paper is vague where the code is specific. Its operator descriptions read like *"non-linear
operations use lookup arguments"*, but reading the source, every operator has a concrete,
dedicated sum-check-plus-lookup protocol, and the recurring machinery underneath them is worth
learning once. (For what *kind* of proof system this is, not a circuit, not a zkVM, see
[Proof systems](./proof-systems/).)

## The recurring machinery

Five primitives show up in almost every operator. A per-operator taxonomy misses them because
they are cross-cutting, which is exactly why they matter.

- **Shout one-hot lookups.** Every table lookup (`exp`, `SatClamp`, `UnsignedLessThan`, ReLU,
  the activation tables) is proven the same way: the prover commits a **one-hot address
  polynomial** `ra` selecting a table row, a read-checking + read-address-fingerprint sum-check
  proves `output = Σ ra(k)·table(k)`, and `ra`'s well-formedness is pinned by a **trio**, 
  booleanity (`ra ∈ {0,1}`), hamming-weight-one (exactly one row hot), and ra-virtualisation.
- **Prefix-suffix table decomposition.** A $2^{64}$-entry table (e.g. `SatClamp<64>`) is never
  materialised; its multilinear extension is expressed over small prefix/suffix tables refreshed
  every couple of rounds. This is what lets the prover stream, and what fits GPT-2 in 16 GB.
- **The fused-rebase seam.** Quantised ops need a divide-by-$2^S$ after each integer matmul. Jolt
  Atlas never proves a division node, the operator's own sum-check *starts* from a reconstructed
  claim `acc = rescaled·2^S + R`, where `rescaled` and remainder `R` are prover **advice**, `R`
  is range-checked into $[0,2^S)$, and the saturating clamp is a `SatClamp` lookup on `rescaled`.
  It is the single most reused gadget in the codebase.
- **Neural teleportation.** To shrink a transcendental's lookup table, the prover range-reduces
  the argument modulo $\tau$ (Euclidean division), looks up the reduced value in a small dense
  table, and range-checks the remainder.
- **The auxiliary-vector transcript trick.** Small $O(\mathbb{F})$ per-row reductions are sent as
  raw transcript *advice* rather than committed polynomials, so the verifier recomputes derived
  quantities itself.

Underneath all of it: a **front-loaded batched sum-check** engine runs instances of different
arities together under one Fiat–Shamir transcript, with a Gruen split-eq product-of-MLEs kernel.

## Matrix multiplication is one engine

The paper treats matmul monolithically. In the code, **one generic engine (`einsum/dot.rs`)
proves all ~11 einsum patterns**, and attention scores $Q\cdot K^\top$ and the context product
$\cdot V$ are the *same code path* as a feed-forward matmul. Each pattern supplies three hooks:
`fold` (collapse the non-contracted output axes into eq-weights at the output randomness), an
`EqSchedule` (where a batch eq-poly rides in the round order), and `operand_points`. After
folding, an ordinary matmul is just a **degree-2 dot product over the contraction cube**;
batch matmul over attention heads rides one `EqSchedule` inside that single sum-check rather than
looping per head. The initial claim is the [fused-rebase](#the-recurring-machinery) reconstruction, not the output opening:

```rust
pub fn fused_input_claim<F: JoltField>(...) -> F {
    match rebase_bits(&node.operator) {
        Some(bits) if bits > 0 => {
            let rescaled = accessor.get_advice(VirtualPoly::ClampAcc).1;
            let remainder = accessor.get_advice(VirtualPoly::RescaleRemainder).1;
            rescaled * F::from_u64(1u64 << bits) + remainder
        }
        _ => accessor.get_reduced_opening().1,
    }
}
```

## Softmax, the flagship correction

The paper's softmax note is *"cannot be expressed as polynomial relations… uses lookup
arguments."* The code has a **four-stage batched sum-check protocol** (with a linked design
write-up), and it never proves a division. Output → input:

1. **Center and clamp.** $z = \max_k - x$, clamped to $z_c = \min(z, z_{bound}-1)$, witnessed by
   a `sat_diff` with $z = z_c + \text{sat\_diff}$.
2. **Exponentiate by two small tables.** Using $e^{a+b}=e^a e^b$, split $z_c$ into digits
   $z_c = z_{hi}\!\cdot\!B + z_{lo}$, each a Shout lookup into `lut_hi`/`lut_lo` (~401 entries vs
   a flat ~65k table), recombined as $\exp_q = \lfloor \exp_{hi}\exp_{lo}/S\rfloor$ with a
   range-checked remainder.
3. **Sum and reciprocate.** The verifier recomputes $\text{inv\_sum} = \lfloor S^2/\exp\_sum\rfloor$
   itself from a prover-sent auxiliary vector, no committed reciprocal, no proven division.
4. **Normalise.** $\exp_q\cdot\text{inv\_sum} = \text{softmax}_q\cdot S + R$.

The max is pinned **without a comparator**: a `MaxIndicator` sum-check forces $\max_k = x$ at the
one-hot argmax, and an *operand link* reconstructs the input so non-negativity does the rest, 

```rust
let z_c_eval = z_hi_eval * F::from_u64(lut.base) + z_lo_eval;
let sat_diff_eval = accessor.get_advice(VirtualPoly::SoftmaxSatDiff).1;
let x_r2 = max_k_eval - z_c_eval - sat_diff_eval;   // == committed X, or the proof fails
```

and the clamp is made *unique* by a complementary-slackness sum-check
($\text{sat\_diff}\cdot(z_{bound}-1-z_c)=0$), a reusable pattern for any saturating quantised op.

## Embedding, norm, activations, positional

- **`Gather` (embedding)** is a dedicated Read-RAF sum-check, not the sparse-one-hot-matmul that
  [[deepprove]] uses. The prover commits a one-hot `ra`; one sum-check proves both the gathered
  value *and* the address read-back by $\gamma$-folding $\text{dict}(k)+\gamma k$. A vocabulary
  router splits `GatherSmall` (dict ≤ 65536, single-chunk one-hot) from `GatherLarge` (Shout
  $d$-chunk decomposition), so the effective table stays bounded.
- **RMSNorm / LayerNorm** is a chain, not a gadget: a fused `MeanOfSquares` node (accumulate
  $\Sigma x^2$, rebase, clamp) feeds an `Rsqrt` node that **batches two integer identities** (a
  division and a square root) into one sum-check under a single folding challenge, with a
  *data-dependent* range-check bound ($r_s < 2\hat v + 1$). *(No RoPE/RMSNorm LLM ships in the
  repo, so this is proven-out by unit tests, not integration.)*
- **GeLU / tanh / erf / sigmoid** are [neural teleportation](#the-recurring-machinery): divide the
  input by $\tau$ into a prover-supplied quotient+remainder, then a single Read-RAF sum-check
  proves `output = Table[idx]` *and* `idx = signed(quotient)` at once by $\gamma$-folding the
  table MLE with a signed-identity polynomial.
- **sin / cos** (positional) use the same teleportation with $\tau = 4\pi$ scaled to ≈3217, into
  a dense $2^{12}$ table. GPT-2's learned absolute encoding, though, is just `Gather` + `Add`.

## Residual & reductions

`Add`, `Sub`, `Mul`, `Div`, `Sum` are small degree-1/2/3 sum-checks whose 64-bit pre-clamp
accumulation is re-executed into a `ClampAcc` virtual MLE (never committed), tied to the
committed operands by a cheap linear equality, then clamped by the shared `SatClamp` lookup.
`Div` proves the Euclidean identity `right·q + R − left = 0` with a committed quotient and an
`UnsignedLessThan`-range-checked remainder. So even the "trivial" ops route through the same
fused-rebase-plus-lookup machinery as everything else, which is the real lesson of reading the
source: **there is no special case; an operator is a little program of lookups and sum-checks,
and the same half-dozen primitives compose all of them.**
