# Jolt Atlas, from the source

A code-grounded companion to the operator chapters in [`index.html`](./index.html). Those
chapters describe how each LLM operator is proven from the *papers*. This one reads the actual
Jolt Atlas implementation and replaces the paper-level guesses with what the code does — with
verbatim snippets and, for each operator, an **audit surface** note aimed at a ZK security
reviewer.

- **Source:** [`ICME-Lab/jolt-atlas`](https://github.com/ICME-Lab/jolt-atlas) @ `b20cdce` (2026-07-08).
- **Method:** 14 operator groups, each read in full by one agent and then re-verified by a
  second adversarial agent that re-opened every cited file to confirm each snippet is verbatim
  and each claim is supported by code. All 14 came back high-confidence.
- **Headline:** in the current `index.html`, every Jolt Atlas operator section is written
  speculatively — *"no dedicated protocol is given"*, *"presumably… the paper does not say."*
  **All fourteen are contradicted by the code.** Jolt Atlas has a concrete, dedicated
  sumcheck+lookup protocol for each. The paper is just terse; the code is not.

> **Scope caveat.** The repo ships only GPT-2 / nanoGPT models (`atlas-onnx-tracer/models/`).
> The RMSNorm, reciprocal-sqrt, and sin/cos code below is real and proven-out by unit tests,
> but **no RoPE/RMSNorm LLM is exercised end-to-end** in the repo. Treat that operator support
> as implemented-but-not-integration-tested.

---

## The recurring machinery

Five primitives show up in almost every operator. Learn them once; the per-operator sections
below assume them. A per-operator taxonomy (like the paper's) misses these because they are
*cross-cutting* — which is exactly why they're worth teaching.

**1. Shout one-hot lookups.** Every table lookup (`exp`, `SatClamp`, `UnsignedLessThan`, ReLU,
the activation tables) is proven the same way: the prover commits a **one-hot address
polynomial** `ra` selecting a table row, and a *read-checking + read-address-fingerprint (RAF)*
sumcheck proves `output = Σ_k ra(k)·table(k)` while a γ-folded second term proves the address
equals the intended index. `ra`'s well-formedness is pinned by a **trio** of companion
sumchecks: **booleanity** (every entry 0/1), **hamming-weight = 1** (exactly one row hot per
lookup), and **ra-virtualization** (the committed per-chunk factors multiply back to `ra`).
Those three are soundness-critical, not decorative — see `joltworks/src/subprotocols/{shout,
booleanity,hamming_weight,ra_virtual}.rs`.

**2. Prefix-suffix table decomposition.** A 2⁶⁴-entry table (e.g. `SatClamp<64>`) is never
materialized. Following Twist & Shout, its MLE is expressed as `less_than_prefix·one +
eq·less_than_suffix`-style recipes over `LOG_K` split into phases, so the prover works with
small prefix/suffix tables refreshed every couple of rounds
(`joltworks/src/lookup_tables/{prefixes,suffixes}`, `subprotocols/ps_shout`).

**3. The fused-rebase seam.** Quantized ops need a divide-by-`2^S` after each integer matmul.
Jolt Atlas never proves a division node: instead the operator's own sumcheck **starts from a
reconstructed claim** `acc(r) = rescaled(r)·2^S + R(r)`, where `rescaled` and the remainder `R`
are *prover-supplied advice* (never committed columns), `R ∈ [0,2^S)` is forced by an identity
range check, and the saturating clamp is a `SatClamp` lookup on `rescaled`. This one gadget is
shared by Einsum, Mul, Square, Cube, MeanOfSquares, Add, Sub, Sum (`onnx_proof/fused_rebase.rs`,
`clamp_lookups/`). It is the single most reused — and most soundness-load-bearing — pattern in
the codebase.

**4. Neural teleportation.** To shrink a transcendental/periodic function's lookup table, the
prover range-reduces the argument by a fixed modulus τ (Euclidean division), then looks up the
reduced value in a small dense table (2¹² for sin/cos, 2¹⁶ for tanh/erf/sigmoid). One sumcheck
proves `input = τ·q + r`; the remainder is range-checked; the reduced value is a Shout lookup
(`onnx_proof/neural_teleport/`).

**5. The auxiliary-vector transcript trick.** Small `O(F)` per-row reductions (softmax's row
max, row exp-sum, argmax) are sent as **raw transcript advice** — not committed polynomials —
so the verifier can recompute derived quantities itself (e.g. `inv_sum = ⌊S²/exp_sum⌋`). It
trades proof size for avoiding commitments, and the softmax module has an explicit `TODO(#218)`
to remove it. This trick is a recurring **audit surface**: advice is only as sound as the
sumcheck that binds it.

And underneath all of it: a **front-loaded batched sumcheck** engine
(`subprotocols/sumcheck.rs`) runs instances of different arities together under one Fiat-Shamir
transcript (each input claim rescaled by `2^(max_rounds−rounds)`, short instances starting to
bind only once the round count reaches them), with a Gruen split-eq product-of-MLEs kernel and
Toom-Cook extrapolation for the round polynomials.

---

## Matrix multiplication — `einsum`

The doc treats matmul monolithically. In the code, **one generic engine (`einsum/dot.rs`)
proves all ~11 einsum patterns**, and attention scores (`Q·Kᵀ`) and the context product (`·V`)
are the *same code path* as a plain feed-forward matmul. Each pattern supplies three hooks via
the `EinsumLayout` trait: `fold` (collapse the non-contracted output axes into eq-weights at
the output randomness), an `EqSchedule` (where a batch eq-poly rides in the round order), and
`operand_points` (scatter the final point back to the two operand openings).

After folding, an ordinary matmul is just a **degree-2 dot product over the contraction cube**:

```rust
// einsum/dot.rs:292-304
match self.params.layout.schedule() {
    EqSchedule::None => {
        let evals: [F; 2] = (0..half)
            .into_par_iter()
            .map(|i| {
                let l = self.left.sumcheck_evals(i, 2, BindingOrder::HighToLow);
                let r = self.right.sumcheck_evals(i, 2, BindingOrder::HighToLow);
                [l[0] * r[0], l[1] * r[1]]
            })
            .reduce(|| [F::zero(); 2], |a, b| array::from_fn(|i| a[i] + b[i]));
        UniPoly::from_evals_and_hint(previous_claim, &evals)
    }
```

Batch matmul (attention over heads) rides a batch eq-poly into the same sumcheck via
`EqSchedule::High`/`Low` (bind batch bits first or last) instead of a separate sumcheck per
batch element. The outer-product pattern `m,an->a1nm` is a degenerate **zero-round** instance:
`num_rounds() == 0`, it just claims the product of two point evaluations.

The sumcheck's initial claim is *not* the output opening — it's the fused-rebase reconstruction:

```rust
// fused_rebase.rs:122-135
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

> **Audit surface.** The operand values `L`, `R` are opened via the accumulator but are **not
> range-checked in the einsum module** — no field-overflow guard on `acc` lives here; it
> depends on upstream quantization invariants. Uniqueness of the `(rescaled, R)` split rests
> entirely on the `R ∈ [0,2^S)` range check being complete (a weak one lets a prover shift
> value between quotient and remainder and forge the clamped output). Two concrete gaps:
> **(1)** non-power-of-two shapes are behind `#[ignore]`d tests ("not fully validated yet") —
> every `fold` assumes `log_2()` dims. **(2)** In ZK mode the remainder claim is a placeholder
> that "reaches the proof only through the prover-supplied baked initial claims of the
> following stages" (`fused_rebase.rs:305-314`) — an explicit trust seam.

---

## Embedding lookup — `Gather`

A dedicated **Read-RAF sumcheck**, not the "sparse one-hot matmul the verifier checks locally"
that the doc attributes to DeepProve. The prover commits a one-hot address polynomial `ra`, and
one sumcheck proves both the gathered value *and* the address read-back by γ-folding
`dict(k) + γ·k`:

```rust
// gather/mod.rs:240-261 (execution sumcheck message; batched value+index read)
let univariate_poly_evals: [F; 2] = (0..index_onehot.len() / 2)
    .into_par_iter()
    // ... ra(k) * (dict(k) + gamma * identity(k)) ...
```

The router splits on vocabulary size: `GatherSmall` (dict ≤ 65536) commits a single-chunk
one-hot and validates it with batched booleanity + hamming-weight sumchecks; `GatherLarge` uses
the generic Shout `d`-chunk decomposition so the effective table is `d·2^log_k_chunk` wide
rather than a single ~70k-wide commitment. Only `ra` is committed; the dictionary and index
tensors arrive as prior-node openings, and the address value comes from an `IdentityPolynomial`
the verifier evaluates in-circuit.

> **Audit surface.** `compute_ra_evals` scatters using the **raw trace indices with no
> `k < num_words` range check** here — an out-of-range index would OOB the prover, and
> correctness leans on booleanity + hamming-weight over the *padded* power-of-two domain plus
> the identity-poly covering the padded range. `test_gather_non_power_of_two_input_len` is
> `#[ignore]`d. `fold_dictionary` carries `// TODO: Assert correct behavior for axis != 0` —
> only axis 0 is validated.

---

## Softmax — the flagship correction

The doc's Jolt softmax section says *"no dedicated protocol is given… presumably ReduceSum plus
Div… the composition, and its accuracy, is left unstated."* **The code has a fully documented,
four-stage batched-sumcheck protocol** (design writeup linked in the module header). It never
proves a division and never proves a comparator for the max.

The algorithm, output→input:

1. **Center and clamp.** `z = max_k − x`, clamped to `z_c = min(z, z_bound−1)`; the clamp is
   witnessed by a `sat_diff` such that `z = z_c + sat_diff`.
2. **Exponentiate by two small tables.** Using `e^{a+b}=e^a·e^b`, `z_c` is split into digits
   `z_c = z_hi·B + z_lo`, each a Shout lookup into `lut_hi`/`lut_lo` (~401 entries total vs a
   flat ~65k table), and `exp_q = ⌊exp_hi·exp_lo/S⌋` with remainder `r_exp ∈ [0,S)`.
3. **Sum and reciprocate.** `exp_sum` is proven by a sumcheck; the verifier recomputes
   `inv_sum = ⌊S²/exp_sum⌋` itself.
4. **Normalize.** `exp_q·inv_sum = softmax_q·S + R`, a reciprocal-multiplication relation with
   `R ∈ [0,S)`.

The max is pinned **without a comparator**, by two constraints working together: a
`MaxIndicator` sumcheck forces `max_k = x` at the one-hot `argmax` position, and an *operand
link* reconstructs the input and forces `max_k ≥ x` everywhere via the non-negativity of `z_c`
(Shout table membership) and `sat_diff` (range check):

```rust
// softmax_last_axis/mod.rs:1043-1058 — operand link
let z_c_eval = z_hi_eval * F::from_u64(lut.base) + z_lo_eval;
let sat_diff_eval = accessor.get_advice(VirtualPoly::SoftmaxSatDiff).1;
let x_r2 = max_k_eval - z_c_eval - sat_diff_eval;
let prover_x_r2 = accessor.get_nodeio(Target::Input(0)).1;
if prover_x_r2 != x_r2 {
    return Err(ProofVerifyError::InvalidOpeningProof(
        "Operand link failed: prover's X(r2) does not match max_k - z_c - sat_diff".to_string(),
    ));
}
```

The `min` clamp is made *unique* by a complementary-slackness sumcheck (input claim 0), a
reusable pattern for any saturating quantized op:

```rust
// softmax_last_axis/sat_diff.rs:203-222
// 0 = Σ eq(r1,x) * sat_diff(x) * (z_bound-1 - z_hi*B - z_lo)
//   => either sat_diff = 0, or z_c = z_bound-1  (unique z_c = min(z, z_bound-1))
```

The three auxiliary vectors are transcript advice, with an acknowledged cost and removal TODO:

```rust
// softmax_last_axis/mod.rs:4-8
//! The prover sends three auxiliary vectors (`max_k`, `exp_sum_q`, `argmax_k`) to the
//! verifier via the transcript. These let the verifier derive `inv_sum[k]` without a
//! committed polynomial, but they add O(F) field elements to the proof size.
//! TODO(#218): Remove auxiliary vectors and derive them inside the protocol.
```

> **Audit surface (highest-value finding in the sweep).**
> - **`argmax_k` has no `< N` bound.** It's used as a public index to build the one-hot `e` via
>   `index_to_field_bitvector(argmax_j, log_n)` (`max.rs:146-152`) with no check that
>   `argmax_k[k] < N`; an out-of-range value silently takes the low `log_n` bits. Likely
>   non-exploitable (the operand-link non-negativity still forces `max_k ≥ x`), but it's a
>   missing bound that deserves a written argument.
> - **Two's-complement advice roundtrip.** `max_k` is packed `from_u32(val as u32)` and read
>   back `to_u64() as i32`; confirm a crafted field element can't roundtrip to a *different*
>   `i32` than the sumchecks bound.
> - **`sat_diff` range is completeness-only.** `rc.rs` states outright that the `2^(log_scale+8)`
>   bound is not a soundness requirement — soundness comes from the slackness sumcheck. Fine,
>   but verify honest `sat_diff` stays in range on real workloads (comment cites max ~13825).
> - **The reciprocal remainder is a `debug_assert` only** — never proven — which is sound *only*
>   because the verifier recomputes `inv_sum` deterministically. If `inv_sum` ever became
>   prover-supplied, this breaks.

Attention (scores → mask → softmax → context) is composed from the einsum patterns above plus
this softmax; there is no separate head-recombination or power-of-two padding argument like
DeepProve's — in a trace-based model it doesn't arise the same way, and the code doesn't add one.

---

## RMSNorm / LayerNorm

Not one gadget but a **chain of per-node sumchecks**: a fused `MeanOfSquares` node (i64
accumulate `Σx²`, rebase by `D = N·2^S`, saturating clamp) feeding a reciprocal-sqrt node. The
reduction's input claim is the same rescale seam, reconstructed from two advices:

```rust
// mean_of_squares.rs:291-297 — the reduction sumcheck's input claim is rescaled·D + R
```

Reciprocal-sqrt batches **two** integer identities (a division and a square-root) into one
sumcheck under a single folding challenge, with the inverse and both remainders supplied
non-deterministically:

```rust
// rsqrt.rs:306-312 — prover derives inv, r_i (from Q²), r_s (from Q·inv − sqrt²) off the trace
```

Notably the range-check bound for the sqrt remainder is **data-dependent**: `RsRangeCheckOperands`
overrides `transform_right_claim` to check `r_s < 2·v̂+1` (a function of the *output*), not a
constant — a good illustration that Shout range-check bounds needn't be fixed.

> **Audit surface.** Honesty of `inv`/`sqrt` hinges on `r_i, r_s` being range-checked, **not**
> on the batched identity equation alone (`rsqrt.rs:472-475`). Confirm both remainder range
> checks are present and their bounds correct. As with all fused ops there's a scalar
> (`log_retained == 0`) fallback that opens values in the clear via `recover_small_int` — a
> distinct verification path worth reviewing separately.

---

## Activations — GeLU / tanh / erf / sigmoid

Neural teleportation again: divide the fixed-point input by τ=2 into a prover-supplied
quotient+remainder (`τ·q + r − input = 0`), then a **single Read-RAF sumcheck** proves
`output = Table[idx]` *and* `idx = signed(quotient)` simultaneously by γ-folding the table MLE
with a `SignedIdentityPoly` (a two's-complement value MLE) against the one-hot `ra`
(`erf.rs:349-360`). The 2¹⁶ table stores `activation(x·τ)`.

> **Audit surface — a real gap.** **tanh's clamp is not proven.** The clamped value is committed
> as an *unconstrained* advice opening and the in-range property is a prover-side `assert!`:
>
> ```rust
> // tanh.rs:310-326
> // TODO: rm once clamp is implemented for tanh
> provider.append_advice(VirtualPoly::DummyClampedTanhInput, clamped_eval);
> // TODO: Pass these input in a clamping lookup table ...
> assert!(clamped_tensor.iter().all(|&x| {
>     let lower_bound = -(1 << (params.op.log_table - 1));
>     let upper_bound = (1 << (params.op.log_table - 1)) - 1;
>     x >= lower_bound && x <= upper_bound
> }));
> ```
>
> `erf.rs:302` and `sigmoid.rs:303` carry the same `// TODO: Same as tanh.rs` prover-side
> assert. A `DummyClampedTanhInput` used as a lookup source with no in-circuit range check is a
> genuine under-constraint: a malicious prover isn't bound by an `assert!` in prover code.

---

## Positional encoding — sin / cos

A three-stage teleportation protocol: a degree-2 division sumcheck enforcing `input = τ·q + r`
with `τ = FOUR_PI_APPROX` (4π scaled by 256 ≈ 3217), a one-hot lookup into a 2¹² dense table,
and a remainder range check `r ∈ [0,τ)`. The only algebraic tie between quotient, remainder and
input is a single constraint:

```rust
// neural_teleport/division.rs:323-331 — eq * (tau*q + r - input)
```

> **Audit surface.** The quotient/remainder are pure prover advice constrained *only jointly*
> by `τ·q + r − input = 0`, so **uniqueness rests entirely on the remainder range check** `r < τ`.
> The remainder-range assertion at `cos.rs:329` is a plain `assert!` that always runs in the
> prover — confirm the in-circuit Shout range check (not the assert) is what the verifier
> actually relies on.

---

## Requantization + clamp

Covered as machinery above; the concrete artifacts: `rescaled` (`ClampAcc`) and `R`
(`RescaleRemainder`) are advice, the clamp is a `SatClamp<64>` lookup, and both are discharged
by prefix-suffix Shout. The clamp semantics:

```rust
// lookup_tables/sat_clamp.rs:15-22
fn materialize_entry(&self, index: u64) -> u64 {
    match XLEN {
        16 => (index as i16).clamp(i8::MIN as i16, i8::MAX as i16) as u64,
        64 => (index as i64).clamp(i32::MIN as i64, i32::MAX as i64) as u64,
        _ => unimplemented!(),
    }
}
```

> **Audit surface — a real gap.** The **standalone ONNX `Clamp` operator is an unproven
> passthrough**:
>
> ```rust
> // ops/clamp.rs:20-30
> // TODO: Clamp
> // Currently this is just a dummy implementation that passes down an operand claim ...
> ```
>
> Any model using a bare `Clamp` node is effectively unproven for that node. (Distinct from the
> *fused* `SatClamp`, which is proven.) Also: `SatClampTable`'s prefix-suffix combine hard-codes
> the i32 split and asserts `XLEN==64` only via `debug_assert` — a release build wouldn't catch
> a wrong-XLEN misuse.

---

## Residual & reductions — Add, Sum, Mul, Div

Each is a small degree-1/2/3 sumcheck whose 64-bit pre-clamp accumulation is re-executed into a
`ClampAcc` virtual MLE (never committed) and tied back to the committed operands by a cheap
linear equality (Add/Sub) or a reduction sumcheck (Sum), then clamped by the shared `SatClamp`
lookup. Div proves the Euclidean identity `right·q + R − left = 0` (degree-3) with a committed
quotient and an advice remainder pinned by an `UnsignedLessThan` range check.

The soundness-test harness is itself worth teaching: `malicious_sub.rs` runs a *faithful*
attacker that follows the protocol exactly but forges one opening (proves `left(r)+1` while
keeping the lookup and one-hot honest) to isolate **which single verifier check rejects** — a
clean template for per-check soundness regression tests. Here the operand tie is the catcher:

```rust
// ops/sub.rs:119-135 — the load-bearing operand tie
// verifier requires  left(r) - right(r) == the lookup's ClampAcc raf claim
```

> **Audit surface.** The pre-clamp `acc` is prover-supplied advice (`clamp_intermediate`
> re-executed, appended as `ClampAcc`, no separate commitment); its only anchor is that operand
> tie plus the clamp lookup. In **ZK mode, Add/Sub/Sum are proved *un-clamped*** and deliberately
> do not commit `ClampRaD` (`zk.rs:2089-2098`) — their saturating clamp is *not* range-checked
> under ZK.

---

## Range checking — the soundness backbone

The recurring primitive under requant, div, rsqrt, tanh. A remainder bound is proven as a
prefix-suffix Read-RAF Shout sumcheck that looks the remainder up in an
`UnsignedLessThanTable<XLEN>` **with the read-value claim fixed to 1** — i.e. it asserts the
comparison returns TRUE for every element rather than proving an output value:

```rust
// range_checking/mod.rs:201-208 — rv_claim hard-coded to 1 (assert "remainder < bound" is TRUE)
```

The two operands are packed into one lookup address by interleaving their bits, and the `as u32`
cast makes a single unsigned less-than enforce **both** `r ≥ 0` and `r < bound`. Bounds are
polymorphic through a claim transform: a constant (`τ`, `N·2^S`) or a data-dependent
`2·v̂+1` (sqrt) via `transform_right_claim`.

> **Audit surface.** This is where "completeness vs soundness" matters most. Several ops
> document that a range *width* is a completeness gate only, with soundness carried by a
> slackness/identity sumcheck — but several *other* ops (requant uniqueness, div) depend on the
> range check for **soundness**. An auditor must classify each range check as one or the other;
> the code is not uniformly commented on which is which.

---

## Zero-knowledge — BlindFold

The doc's ZK section is paper-level. The code names and implements **BlindFold**: every
sumcheck round polynomial and every output/opening claim is replaced by a Pedersen commitment
with fresh blinding, and one aggregate relaxed-R1CS encoding all the sumcheck verifier checks is
proved via **Nova folding + Spartan** with Hyrax-grid witness commitments. The verifier replays
the transcript over commitments and **skips the cleartext output-claim equality** (it's
delegated to the R1CS).

```rust
// subprotocols/sumcheck.rs:349-360 — the hiding step
let blinding = F::random(rng);
let commitment = pedersen_gens.commit(&batched_univariate_poly.coeffs, &blinding);
transcript.append_serializable(&commitment);
let r_j = transcript.challenge_scalar_optimized::<F>();
```

A random satisfying R1CS instance is folded in as a one-time pad (`folded = real + r·random`) so
folded values are safe to reveal.

> **Audit surface — the most serious findings are here.**
> - **Softmax `operand_link` is intentionally skipped in ZK.** The identity binding the input to
>   the max/digit/`sat_diff` decomposition is not enforced anywhere in the ZK path; the intended
>   BlindFold constraint "does not yet exist":
>   ```rust
>   // zk.rs:381-391
>   // NOTE: operand_link (X(r2) == max_k - z_c - sat_diff ...) is intentionally skipped here.
>   // In the ZK pipeline all four openings are private and surface to the verifier as the
>   // zk_mode placeholder zero ... so a direct verifier-side check would always fail.
>   ```
>   This is a genuine under-constraint in the **softmax ZK flow** — the very identity that pins
>   the max in the non-ZK path is absent.
> - **Public-node claims are compared in cleartext.** `public_node_reduced_claims` are checked by
>   plain MLE comparison that "catches honest-prover errors; full soundness against an active
>   malicious prover additionally requires an R1CS constraint … tracked as future work"
>   (`zk.rs:113-119`).
> - **One aggregate scalar leaks.** The γ-weighted `joint_claim` is revealed in cleartext because
>   "Full ZK for `joint_claim` would require a hiding HyperKZG (none today)" — per-poly openings
>   stay hidden, but this is an explicit, accepted non-ZK leak.
> - **`zk_mode` toggling is the transcript lynchpin.** It forces claim appends to a placeholder
>   zero and is manually toggled off around genuinely-public scalars; any mis-toggle desyncs
>   Fiat-Shamir or leaks a private value. Completeness of the toggling is load-bearing.

---

## Consolidated audit findings

Ranked by how much a reviewer should care. None is a claimed break of a shipped system — Jolt
Atlas is research code and several are self-documented TODOs — but each is where a security
review would start.

| # | Finding | Where | Severity | Status in code |
|---|---|---|---|---|
| 1 | Softmax `operand_link` (the max-binding identity) **not enforced in ZK mode** | `zk.rs:381-410` | High (ZK) | Intentional, no replacement constraint yet |
| 2 | Standalone ONNX `Clamp` operator is an **unproven passthrough** | `ops/clamp.rs:20-30` | High (if used) | `// TODO: Clamp` dummy |
| 3 | **tanh/erf/sigmoid clamp unproven** — dummy advice + prover-side `assert!` | `tanh.rs:310-326`, `erf.rs:302`, `sigmoid.rs:303` | High | `// TODO: rm once clamp is implemented` |
| 4 | Add/Sub/Sum **saturating clamp not range-checked under ZK** | `zk.rs:2089-2098` | Medium (ZK) | Deliberate (no `ClampRaD` committed) |
| 5 | Public-node reduced claims checked in **cleartext only** | `zk.rs:113-119` | Medium (ZK) | Acknowledged future work |
| 6 | `argmax_k` used as one-hot index with **no `< N` bound** | `softmax…/max.rs:146-152` | Low–Med | Likely non-exploitable; unwritten argument |
| 7 | Fused-rebase ZK remainder is a **placeholder trust seam** | `fused_rebase.rs:305-314` | Medium (ZK) | Documented |
| 8 | Non-power-of-two shapes (einsum, gather) behind **`#[ignore]`d tests** | multiple | Completeness | "not fully validated yet" |
| 9 | `joint_claim` aggregate scalar **leaks in cleartext** | `zk.rs:96-97` | Low (privacy) | Accepted; no hiding HyperKZG |
| 10 | Advice roundtrip via two's-complement `u32`/`i32` casts | `softmax…/mod.rs:371-384` | Low | Worth a written non-malleability argument |

The pattern across all ten: **the non-ZK path is fairly tightly constrained by sumchecks +
range checks + Shout one-hot triples, but the ZK (BlindFold) path is younger** and several
bindings that hold in the clear are not yet re-expressed as R1CS constraints. If a review is
scoped, scope it to the ZK flow first (findings 1, 4, 5, 7, 9).

---

*Generated from a 14-topic code-analysis workflow over `jolt-atlas@b20cdce`, each finding
adversarially re-verified against the source. To fold any section into `index.html`, the
matching operator ids are: `softmax`, `matmul`/`scores`/`mha`, `embed`, `rmsnorm`/`layernorm`,
`gelu`, `rope`/`ape`, `requant`/`clamp`, `residual`, `mem`, `zk`.*
