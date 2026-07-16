---
title: ZIP, Zero-Knowledge AI Inference with High Precision
paper: zip
status: reviewed
---

*(The PDF lives at `references/proving-inference/high-precision.pdf`; the `papers.yml` id is `zip`.)*

## What is new

ZIP is the counter-philosophy of this whole collection, and it is worth having in the SoK for that
reason alone. Every other prover here **bends the model to fit the prover**, quantize to 4, 8, 12 or
16 bits, approximate GeLU with a spline or a quadratic, replace softmax with a lookup table. ZIP
**bends the prover to fit the model**: it proves inference in native IEEE-754 double precision,
with the actual activation functions, and eats the cost.

The technique that makes that affordable is a *relative-error-driven* argument. Rather than
hardcoding a floating-point activation into a circuit (which costs millions of constraints in
IEEE-754 semantics), ZIP has the prover supply the activation's output, proves it against a
piecewise-polynomial approximation stored in a lookup table, and then constrains the *relative
error* between the true value and the approximation to lie within a bound δ. It also hardens the
underlying lookup and range proofs with additional arithmetic constraints against a malicious
prover, an audit-minded touch that is rare in this literature.

The resulting constraint count per double-precision activation is a genuine multiple-orders-of-
magnitude reduction over hardcoding IEEE-754 semantics into a circuit, and I believe it.

## What it actually proves

**One forward pass of a small model, in full double precision, with a hidden model, on a
proof-of-concept prototype whose verifier is not succinct in any useful sense.**

- The models are LeNet-5 (MNIST, ~60K params) and mini-BERT (SST-2, ~11M params, 4 layers, hidden
  size 256), plus a ~250K-param CNN on UTKFace for the precision study. **This is not an LLM prover
  and it is not a graph point.** mini-BERT is a text classifier, not a generative model, no decode,
  no sampling, no autoregression.
- It is genuinely zero-knowledge and model-private: commit-and-prove over PlonK, with the model
  weights as the committed witness. On that axis it is in the same class as [[zkllm]] and ahead of
  [[zkgpt]] and [[deepprove]].
- The precision claim is real and is the point. There is no quantization, so there is no calibration
  set, no scale factor, no zero-point, no bit width, and therefore none of the audit surface that
  the rest of this repo worries about. That is a real security argument, not just an accuracy one.

## What to distrust

**ZIP optimizes the component that is not the bottleneck in its own largest experiment.** The
paper's entire contribution is reducing the cost of *non-linear* layers. On mini-BERT, its own
Table 7 shows the **linear** layers consuming 34.53 of 37.06 prover-hours, 93% of the total, and
they are not ZIP's work at all; they are delegated wholesale to a prior scheme. The non-linear
layers ZIP exists to accelerate account for the remaining 7%.

The story inverts with model size, and that is the finding. On LeNet-5, the non-linears dominate and
ZIP's contribution is decisive. On an 11M-parameter transformer, the linears dominate fourteen to
one. Extrapolate to anything the rest of this repo calls an LLM and ZIP's contribution becomes
rounding error on the total. The paper never remarks on this inversion, and it is visible in its own
tables.

**The verifier is not succinct.** LeNet-5 verifies in minutes. mini-BERT verifies in **most of an
hour**. For an 11M-parameter model, a client could run the plaintext inference itself millions of
times over in that window. The cause is structural, not incidental, ZIP "employs two multi-lookup
arguments per activation with four pairing[s] per lookup proof during verification," so verifier
work is **linear in the activation count**. A commit-and-prove zkSNARK whose verifier scales with
the circuit has given up the property that makes a SNARK worth having. Compare [[zkgpt]] (sub-second
on GPT-2) or [[deepprove]] (a few seconds). Nobody in the paper mentions it.

**The motivating baseline is a straw baseline, and it is doing all the rhetorical work.** ZIP's case
for abandoning fixed-point rests on two comparisons:

:::quote{src="ZIP" sec="§7, Impact of Precision"}
Moreover, Table 3 shows that quantizing all weights and inputs to fixed-point representation while
retaining the actual ELU activation function (i.e., Baseline (w/FP)), the MAE increases
significantly, demonstrating that fixed-point arithmetic severely degrades accuracy and prevents
convergence.
:::

**"No convergence"**, on a 250K-parameter CNN. And an 8.5-point accuracy collapse on mini-BERT under
fixed point. The paper states **no bit width, no scale factor, no calibration procedure, and no
quantization scheme** for either fixed-point baseline. Meanwhile, in this same collection,
[[zkgpt]] keeps perplexity within half a point on GPT-2 at 16 bits, [[deepprove]] keeps GPT-2 within
a fraction of a percent of its fp32 baseline at 12 bits, and [[zkpytorch]] loses under 0.03% on
CIFAR-10. A fixed-point baseline that fails to converge is a *badly configured* baseline, not
evidence that fixed-point is unworkable. The paper's central premise is supported by the worst
fixed-point result in the literature, produced by the authors, with its configuration unstated.

:::audit Table 5's prover totals do not add up
Two of the three prover columns in Table 5 (LeNet-5) disagree with the components printed directly
above them, each by exactly 0.10 min:

| Column | Sum of printed rows | Printed total |
|---|---|---|
| GeLU | 13.89 + 5.23 + 0.37 + 0.29 + 0.89 = **20.67** | 20.67 ✓ |
| SeLU | 11.19 + 3.49 + 0.25 + 0.19 + 0.89 = **16.01** | **15.91** ✗ |
| ELU | 9.30 + 3.42 + 0.24 + 0.19 + 0.89 = **14.04** | **13.94** ✗ |

All three *verifier* columns sum correctly, which rules out a transcription artifact in my reading.
Separately, the body text gives ZIP's UTKFace MAE as 6.15 where Table 3 prints 6.16. Small, but this
is a CCS paper.
:::

**Credit where due, and it is substantial:** ZIP prints the number that makes it look worst.
Table 4 shows a single double-precision GeLU costing hundreds of times more prover time than the
fixed-point schemes it is arguing against, and the paper puts that table in the body rather than an
appendix, calls the comparison "conservative," and concedes in the Discussion that "our prototype is
just a proof of concept to demonstrate correctness and feasibility, not performance optimization."
That is exactly the right disclosure. The problem is not that ZIP is dishonest about its costs, it
is that the *benefit* those costs buy is established only against a baseline the paper declines to
specify.
