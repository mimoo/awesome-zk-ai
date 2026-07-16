---
title: The landscape
section: zk-inference
order: 10
lede: >-
  Proving inference is the most crowded cell in the 2x2, and the only one with a
  live leaderboard. That leaderboard is not measuring one thing.
papers: [deepprove, jolt-atlas, zkgpt, zkpytorch, zkllm, zkml-kang, zktorch, artemis, nanozk, zip, ezkl, lu-et-al, hao-et-al, safetynets, zkcnn, spagkr, mystique, vcnn, zen, bionetta, range-arithmetic]
status: draft
---

## The claim

Proving inference means producing a string a stranger can check, which certifies:
*this model, the one committed to earlier, produced this output on this input.* Nothing
about the training. Nothing about the model's quality. One computation, executed
faithfully.

That is the cheapest of the four verification objectives, and it is cheap for a reason
worth internalizing before reading any benchmark: **the prover already knows the answer.**
A proof does not compute the forward pass, it *checks* one. Every serious speedup in this
section is downstream of exploiting that asymmetry, the result-as-witness paradigm, output
certification, batched token proving. A system that merely re-executed the model inside a
circuit would be uncompetitive by orders of magnitude.

The threat model is MLaaS. You pay for a frontier model and the provider silently serves a
smaller, more aggressively quantized one; or the model runs on a cloud you do not control;
or the output settles money on-chain and the counterparty is anonymous. All of these are
**model substitution**, and it is the concrete thing this literature exists to prevent, 
[[nanozk]] and [[deepprove]] both name it directly.

**With exactly one exception, and it is worth stopping on, because it turns out the threat
model is the dominant term in the cost.** [[bionetta]] runs the whole thing backwards: the
*model* is public, the *input* is private, and the *client* is the prover, on a phone,
proving that their face matches an enrolled template without surrendering the face. Once the
weights are public they stop being circuit *signals* and become circuit *constants*, and R1CS
charges nothing for multiplication by a constant. Every linear layer therefore costs **zero
constraints**, and ResNet18 falls from 37.85M constraints to 1.16M.

Hold that number next to the rest of this page. Five years of protocol work, sum-check for
convolution, lookup arguments, result-as-witness, circuit squeeze, buys large constant
factors. *Making the weights public* buys a factor of thirty-two on its own, and it is
unavailable to every other system here for the simple reason that the weights are the thing
they exist to hide. **A great deal of what this table reads as cryptographic progress is
the price of a security property, and nobody separates the two.**

## Who is in the race

{{ table:inference }}

{{ chart:throughput }}

Three groups of entries hide inside that table, and mixing them is the single most common
error in this field.

**The LLM systems.** [[deepprove]], [[zkgpt]], [[zkllm]], [[zkpytorch]], [[jolt-atlas]],
and, with a warning label, [[nanozk]]. These are the systems whose papers are pitched at
LLM inference. They are not the only entries in the table that have run a transformer, 
[[zktorch]], [[zkml-kang]], [[artemis]] and [[lu-et-al]] all report GPT-class benchmarks, 
but they are the ones for which an LLM is the design target rather than a coverage
datapoint. They span an enormous range of hardware: a laptop for [[jolt-atlas]], CPU-only
for [[zkgpt]], a datacenter GPU for [[zkllm]], and a many-core server CPU for [[deepprove]]
whose distributed prover is *simulated*, not deployed. They also span an enormous range
of *what they prove*, which is the subject of [the next page](./what-is-proven/) and the
reason the throughput column should be read with suspicion.

**The compilers.** [[zkml-kang]], [[zktorch]], [[ezkl]], and [[zkpytorch]] are pipelines
from an ONNX or TFLite graph down to a circuit. Most of them compete on coverage and
engineering rather than cryptographic novelty, [[zkpytorch]] says so in as many words:

:::quote{src="zkPyTorch" sec="§3.4, Hierarchical ZKP circuit optimizer"}
Therefore, rather than introducing new optimization approaches, ZKPyTorch integrates
existing techniques for primitive operations to enhance efficiency, ensuring compatibility
with state-of-the-art methods while maintaining scalability for large-scale machine
learning models.
:::

That is an honest and useful thing for a compiler paper to say. It also means a compiler's
headline number is a statement about *its backend and its quantization*, not about a new
way to prove a matmul. [[zktorch]] is the exception in this group: it is a compiler that
also ships a new accumulation protocol.

**The pre-LLM generation.** [[zkcnn]], [[vcnn]], [[zen]], [[mystique]], [[safetynets]], 
convolutional nets, no attention, and no shared choice of field. They are not obsolete;
they are the foundation, and their assumptions are still load-bearing. See
[Vision and trees](./vision-and-trees/).

Several entries sit outside all three groups. [[bionetta]] is the one described above, a
client-side prover for a public model, running on a phone, with no softmax and therefore no
transformer, which is why it appears in none of the LLM comparisons and should never be put on
the tokens-per-minute axis. [[hao-et-al]] proves *operators* (ReLU, Softmax)
rather than models, which makes it a component supplier rather than a competitor. [[zip]]
refuses to quantize at all: its honest prover computes activations in native IEEE-754 double
precision. What the proof *enforces* is weaker, that the value lies within a bounded relative
error of a certified polynomial approximation, but as a design it is the counter-thesis to
everything else here, and the cleanest evidence that quantization is a *choice*. See
[Quantization](./quantization/). [[spagkr]] changes both sides at once, a sparsity-aware GKR
protocol whose proof time scales with the *non-zero* parameters, and a ternary network on top
of it. Its (secondhand) numbers separate the two, and sparsity buys most of the win. It is
still the strongest published evidence that narrower weights make proving cheaper, but it is
not clean evidence. [[artemis]] attacks a different bottleneck again, the consistency check
that ties a committed model to the circuit that runs it, and is therefore orthogonal to every
prover in the table. [[range-arithmetic]] is an interactive sum-check descendant of
[[safetynets]] that proves fixed-point *rounding* arithmetically rather than by
bit-decomposition, and, like its ancestor, reports its costs only as log-scale plots, there
is no absolute timing in it to compare against. And [[lu-et-al]] is the VOLE outlier, a very
fast prover that emits proofs measured in gigabytes and can only convince the one verifier it
talked to.

## The shape of the field

Four observations that the table alone will not give you.

**Sum-check won, for LLMs.** Nearly every fast system in this section descends from
[[safetynets]] by way of [[zkcnn]]: represent the network as an arithmetic circuit, prove it
with sum-check and GKR rather than a general-purpose SNARK. The Halo2/PLONKish line
([[zkml-kang]], [[ezkl]], [[artemis]]) survives on tooling maturity, not on prover speed, 
and, per [[bionetta]]'s measurements of [[ezkl]], not on tiny proofs either, which is what
everyone thought it was surviving on. The R1CS/Groth16 line, meanwhile, was written off too
early: it is the only line that delivers a sub-kilobyte proof and a millisecond verifier, and
on a public model it is the fastest prover in this SoK. [Proof systems](./proof-systems/)
breaks all of this down.

**The hard part is not the matmul.** It never was. Matrix multiplication is the one thing
arithmetic circuits are naturally good at. The cost, the papers, and the bugs all live in
Softmax, GeLU, LayerNorm and re-quantization, the non-arithmetic operations. Every
technical contribution in the last five years (`tlookup`, `zkAttn`, result-as-witness,
constraint fusion, neural teleportation) is an attack on the same handful of operators.
[[bionetta]] is the clean confirmation, arriving from the far side: with the matmuls at
*literally* zero constraints, its proving cost reduces to a single quantity, the number of
non-linearity calls. Two proof systems with nothing in common, one cost model.
Strikingly, the [private inference](../private-inference/) literature, which shares no
citations with this one, is bottlenecked on *exactly the same operators* for entirely
different reasons.

**Bit width is unreported more often than not,** and it moves proving cost. That makes the
throughput column a comparison across an uncontrolled variable. See
[Quantization](./quantization/).

**Nothing here has been analyzed as a deployed system.** Every system in the table is an
argument system compiled by Fiat–Shamir, or a circuit, or both. The
[Fiat–Shamir/GKR attack](./proof-systems/) is a proven attack on the construction underneath
most of this section, under a precondition nobody has checked against these systems, and
the Halo2 query-collision bug was a real, exploitable bug in the stack two of them sit on.
The gap between "no known break" and "analyzed" is where the work is.

## Where to go next

- [What is actually being proven](./what-is-proven/), the comparability crisis. Read this
  before you quote any number from the table above.
- [Proof systems](./proof-systems/), the cryptographic taxonomy, and what each approach is
  bad at.
- [Quantization](./quantization/), the confounder in every cross-system comparison, and an
  audit surface.
- [Vision and trees](./vision-and-trees/), where the field came from, and what it assumed.
