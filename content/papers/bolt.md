---
title: BOLT
paper: bolt
status: reviewed
---

## What is new

BOLT attacks [[iron]] on four fronts at once, and the honest summary is that two of them are
cryptography and two of them are machine learning.

**The cryptography.** A better ciphertext packing for matrix-matrix multiplication that stops wasting
SIMD slots, plus a baby-step giant-step rotation schedule that cuts the ciphertext rotations the new
packing would otherwise require. And a **polynomial pre-processing technique** that reduces the
multiplication count when evaluating a fixed polynomial on secret-shared input — a generic MPC
result the authors correctly flag as independently useful. Where Iron used HE for matmul and OT for
everything else, BOLT pushes more of the computation into HE specifically to trade communication for
computation, on the bet that compute is what gets cheaper.

**The machine learning.** *Oblivious word elimination*: rank tokens by their attention scores,
compute the median obliviously via a bitonic sort, and **discard every token below it**. And
*secure-computation-aware fine-tuning*: retrain the model so it tolerates the fixed-point scales and
polynomial approximations BOLT wants to use.

Both halves work. It matters enormously which half you credit for the headline.

## What it actually proves

Nothing — no proof. Privacy against a semi-honest counterparty, on BERT-base, across four GLUE
tasks, with the parameters stated (37-bit ring, scale 12, and the HE parameters given explicitly).
The reporting discipline here is better than the zkML column's: bit widths, ring, scale, HE modulus,
network settings, and an ablation table all appear.

The claim to hold onto is that BOLT is the paper that *pins* [[iron]]'s cost, since Iron itself
publishes only ratios and log-scale plots. But note exactly what that means:

:::quote{src="BOLT" sec="§7.1.4, Iron's System"}
Because Iron [28] is not open-sourced, we implement Iron's end-to-end system following the protocols
described in their paper.
:::

The Iron anchor figure everyone quotes is **BOLT's reimplementation of Iron, under a narrow WAN
setting BOLT chose**. Iron's own paper benchmarked on a LAN and, as it happens, publishes no absolute
figures at all. So: the *communication volume* half of that anchor is bandwidth-independent and fair,
while the *wall-clock* half is a direct function of the pipe BOLT picked. Both halves are routinely
quoted as though they were Iron's own measurements.

## What to distrust

**The headline communication reduction is not a cryptographic result.** It requires throwing away
half the input tokens.

:::audit Word elimination is worth as much as all the cryptography
BOLT's own Table 3, end-to-end communication for one BERT-base inference:

| System | Communication | vs. Iron |
|---|---|---|
| Iron (BOLT's reimplementation) | 280.99 GB | — |
| **BOLT, no word elimination** | **59.61 GB** | **4.71×** |
| BOLT, with word elimination | 25.74 GB | 10.91× |

The purely cryptographic contribution — the packing, the BSGS rotations, the polynomial
pre-processing, the low-degree GELU and Softmax — is **4.71×**. The other 2.3× comes from
[eliminating] "tokens scoring below the median." BOLT processes roughly half the sequence that Iron
processes.

The headline number in the abstract, in `papers.yml`, and in the README is 10.91×. The number that
compares protocol against protocol on the same workload is 4.71×.
:::

**And the model itself is different.** BOLT does not merely quantize BERT — it **fine-tunes** it, with
word elimination active in the forward pass, so the network learns to cope both with the fixed-point
arithmetic and with having half its tokens deleted. "Matches the accuracy of plaintext models" is
therefore comparing a *retrained* model against a *non-retrained* floating-point baseline. This is
the "bend the model" move, executed twice, and [[ciphergpt]] criticizes exactly this class of
approach: "all such solutions require retraining the model, which is less desirable to machine
learning practitioners." BOLT's own defence — fine-tuning is a one-time cost amortized over
inferences — is reasonable, but it does not make the accuracy comparison apples-to-apples.

The paper does state the mechanism plainly ("word elimination introduces negligible accuracy drops,
and can significantly improve the performance of BOLT") and it does publish the ablation. The
criticism is not that BOLT hid this. It is that everyone downstream quotes the number that includes
it as if it were a protocol result.

**The reported runtime speedup is a range because it is a bandwidth sweep, not a protocol range.**
BOLT cuts communication by an order of magnitude but cuts the *round count* by only about a quarter.
On a fast link, rounds and compute dominate and BOLT's advantage sits at the bottom of its range; on
a slow link, bytes dominate and it sits at the top. The spread is a property of the network, not of
the system, and the number people quote is the one achieved against the narrowest pipe.

**Accuracy beats plaintext again.** BOLT with word elimination scores *above* the floating-point
baseline on SST-2, and Iron scores above it on two tasks. These are within the reported standard
deviation of the plaintext baseline, which is the right explanation — but it also means that the
sub-1% accuracy deltas this entire cluster reports are inside the noise floor, and "comparable
accuracy to floating-point" is not a claim any of these papers has the statistical power to
distinguish from its negation. More curiously, BOLT reports that dropping half the tokens *improves*
accuracy over not dropping them, attributing it to a ring-to-field conversion approximation. That is
an odd thing to leave at one sentence.
