---
title: The landscape
section: zk-inference
order: 10
lede: >-
  Proving inference is the most crowded cell in the 2x2, and the only one with a
  live leaderboard. That leaderboard is not measuring one thing.
papers: [deepprove, jolt-atlas, zkgpt, zkpytorch, zkllm, zkml-kang, zktorch, artemis, nanozk, zip, ezkl, lu-et-al, hao-et-al, safetynets, zkcnn, spagkr, mystique, vcnn, zen]
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
section is downstream of exploiting that asymmetry — the result-as-witness paradigm, output
certification, batched token proving. A system that merely re-executed the model inside a
circuit would be uncompetitive by orders of magnitude.

The threat model is MLaaS. You pay for a frontier model and the provider silently serves a
smaller, more aggressively quantized one; or the model runs on a cloud you do not control;
or the output settles money on-chain and the counterparty is anonymous. All of these are
**model substitution**, and it is the concrete thing this literature exists to prevent —
[[nanozk]] and [[deepprove]] both name it directly.

## Who is in the race

{{ table:inference }}

{{ chart:throughput }}

Three groups of entries hide inside that table, and mixing them is the single most common
error in this field.

**The LLM systems.** [[deepprove]], [[zkgpt]], [[zkllm]], [[zkpytorch]], [[jolt-atlas]],
and — with a warning label — [[nanozk]]. These are the only systems that have touched a
transformer. They span an enormous range of hardware: a laptop for [[jolt-atlas]], CPU-only
for [[zkgpt]], a datacenter GPU for [[zkllm]], a small cluster for [[deepprove]]'s
distributed prover. They also span an enormous range of *what they prove*, which is the
subject of [the next page](./what-is-proven/) and the reason the throughput column should
be read with suspicion.

**The compilers.** [[zkml-kang]], [[zktorch]], [[ezkl]], and [[zkpytorch]] are not
protocols; they are pipelines from an ONNX or TFLite graph down to a circuit. They compete
on coverage and engineering, not on cryptographic novelty — [[zkpytorch]] says so in as
many words:

:::quote{src="zkPyTorch" sec="§4, Hierarchical circuit optimization"}
Therefore, rather than introducing new optimization approaches, ZKPyTorch integrates
existing techniques for primitive operations to enhance efficiency, ensuring compatibility
with state-of-the-art methods while maintaining scalability for large-scale machine
learning models.
:::

That is an honest and useful thing for a compiler paper to say. It also means a compiler's
headline number is a statement about *its backend and its quantization*, not about a new
way to prove a matmul.

**The pre-LLM generation.** [[zkcnn]], [[vcnn]], [[zen]], [[mystique]], [[safetynets]] —
convolutional nets, small fields, no attention. They are not obsolete; they are the
foundation, and their assumptions are still load-bearing. See
[Vision and trees](./vision-and-trees/).

Four entries sit outside all three groups. [[hao-et-al]] proves *operators* (ReLU, Softmax)
rather than models, which makes it a component supplier rather than a competitor. [[zip]]
refuses to quantize at all and proves native floating-point inference — the counter-thesis
to everything else here, and the cleanest evidence that quantization is a *choice*.
[[spagkr]] is a modification to the *model*, not the prover: make the network sparse and
ternary and the proof gets cheaper, which is the most direct published evidence that
quantization drives proving cost. And [[lu-et-al]] is the VOLE outlier — a very fast prover
that emits proofs measured in gigabytes and can only convince the one verifier it talked to.

## The shape of the field

Four observations that the table alone will not give you.

**Sum-check won.** Nearly every fast system in this section descends from [[safetynets]] by
way of [[zkcnn]]: represent the network as an arithmetic circuit, prove it with sum-check
and GKR rather than a general-purpose SNARK. The Halo2/PLONKish line ([[zkml-kang]],
[[ezkl]], [[artemis]]) survives on tooling maturity and tiny proofs, not on prover speed.
[Proof systems](./proof-systems/) breaks down why.

**The hard part is not the matmul.** It never was. Matrix multiplication is the one thing
arithmetic circuits are naturally good at. The cost, the papers, and the bugs all live in
Softmax, GeLU, LayerNorm and re-quantization — the non-arithmetic operations. Every
technical contribution in the last five years (`tlookup`, `zkAttn`, result-as-witness,
constraint fusion, neural teleportation) is an attack on the same handful of operators.
Strikingly, the [private inference](../private-inference/) literature — which shares no
citations with this one — is bottlenecked on *exactly the same operators* for entirely
different reasons.

**Bit width is unreported more often than not,** and it moves proving cost. That makes the
throughput column a comparison across an uncontrolled variable. See
[Quantization](./quantization/).

**Nothing here has been audited.** Every system in the table is an argument system compiled
by Fiat–Shamir, or a circuit, or both. the Fiat–Shamir/GKR attack is a proven attack on the
construction underneath most of this section — under a precondition nobody has checked
against these systems — and the Halo2 query-collision bug was a real, exploitable bug in the
stack two of them sit on. The gap between "no known break" and "analyzed" is where the
work is.

## Where to go next

- [What is actually being proven](./what-is-proven/) — the comparability crisis. Read this
  before you quote any number from the table above.
- [Proof systems](./proof-systems/) — the cryptographic taxonomy, and what each approach is
  bad at.
- [Quantization](./quantization/) — the confounder in every cross-system comparison, and an
  audit surface.
- [Vision and trees](./vision-and-trees/) — where the field came from, and what it assumed.
