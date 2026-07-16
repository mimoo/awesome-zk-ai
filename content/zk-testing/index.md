---
title: Proving a score
section: zk-testing
order: 10
lede: >-
  "This model scores X on benchmark D" is the claim the market runs on, and it is the claim
  most likely to be false. It is also the thinnest cell in this SoK -- a handful of papers, all
  on small models. One of them hides the test data from the model owner; none of them ties the
  model to a time before the test set was chosen, which is what decides whether the number means
  anything. The hard part was never the proof.
papers: [zkdt, pvcnn, zkcnn, zen, artemis]
status: draft
---

The testing objective sits between inference and training: prove that a *committed* model
achieves a *claimed* accuracy on a *dataset*. It is the claim behind every leaderboard, every
model-marketplace listing, and every "our model beats theirs" in a press release. Benchmark
contamination is a live, widely-reported problem in exactly this market. And it is the emptiest
cell in the table.

{{ table:testing }}

That is the whole of it. [[zkdt]] proves accuracy for a decision tree, with a genuinely elegant
observation, test samples share nodes on a tree, so all inference paths across the whole test set
can be validated in one step instead of once per sample. [[pvcnn]] proves accuracy for a small
CNN, using a hybrid of homomorphic encryption, collaborative inference and zk-SNARKs, and
splitting the model into a private and a public component. Three more systems cross-list into this
objective from the inference cell: [[zkcnn]] and [[zen]] both ship an accuracy-proving mode
alongside their inference mode, and [[artemis]] is recorded against both objectives too.

That is the entire literature. MNIST and a decision tree. No language model, no leaderboard
benchmark, nothing that would let a lab prove its MMLU score.

## The proof is the easy half

Here is the structural reason this cell is thin, and it is not a cost problem.

Proving accuracy is, arithmetically, just *inference, batched, plus a counting argument*: run the
committed model on each test item, compare to the label, sum the matches, prove the sum. Every
technique from the inference cell applies directly, and the specialized ones, zkDT's shared paths,
Artemis's attack on commitment-consistency overhead, are exactly the optimizations you would
expect. If the only problem were "make this cheap", the inference cell would have solved it by
transfer.

The problem is that the interesting version of the claim requires the test set to be **hidden from
the model's trainer**, and the proof requires the test set to be **available to the prover**. The
prover is the model owner. So:

- If the model owner holds the test set, they can train on it. The proof then faithfully certifies
  a contaminated score. The cryptography has done its job perfectly and the number is still a lie.
- If the model owner does not hold the test set, they cannot evaluate the model on it, and so
  cannot produce the witness the proof needs.

Two of the systems above have half of this. [[zen]]'s ZENacc fixes the model commitment *before*
the verifier supplies the testing dataset, so the ordering is right, but the prover then receives
the dataset and its truth labels in the clear, and ZEN never frames the ordering as a contamination
defence. [[pvcnn]] goes the other way: the test data stays under homomorphic encryption and the
model developer computes on ciphertext, but we hold no PDF for it, and nothing in the survey's
account of it, or in its abstract, binds the model to a time before the test items were chosen.
Neither system does both, and neither states the dilemma.

**A zero-knowledge accuracy proof prevents the wrong attack.** It stops a lab from *lying about the
score it measured*. It does nothing about a lab *measuring the score on data it has already seen*, 
which is the failure mode that actually occurs, and is a data-governance problem wearing a
cryptography costume.

:::gap  The claim that would matter, and nobody proves it
Not one system in this repo proves a benchmark score for a language model on a standard
benchmark. The systems that could, the LLM provers in the inference cell, prove single passes or
generations, and nothing in their papers composes those into an accuracy claim over a committed
evaluation set. The cell that most obviously has a paying customer is the cell with the least work
in it.
:::

## What a good paper here would have to do

We are being prescriptive on purpose, because the shape of the missing paper is unusually clear.
It has to solve the *ordering* problem and the *exposure* problem, not just the arithmetic one.

**1. Bind the model commitment to a time before the test set existed.** The only defence against
contamination is temporal: commit to the weights, publish the commitment, and *then* release (or
sample) the evaluation items. This makes the interesting claim provable, "this model could not
have been trained on this test set, because it was fixed before the test set was drawn", and it
requires nothing more exotic than a commitment and a timestamping mechanism. It is also the one
ingredient that makes the whole exercise worth doing. [[zen]]'s ZENacc already has the ordering:
the model is committed first, and only then does the verifier, or a trusted third party, send
the challenge dataset. What it does not have is any of the surrounding argument. The ordering is a
setup-phase convenience, not a contamination defence; it binds nothing publicly to a time, it says
nothing about where the dataset came from, and the word contamination does not appear in the paper.
The skeleton exists in one system; nobody has closed the gap.

**2. Let the evaluation happen without the prover learning the test items.** This is where the
privacy column of the 2x2 has to be borrowed. [[pvcnn]] is the one system in the cell that reaches
for this: the testers' data stays under homomorphic encryption and the model developer computes on
ciphertext, so the developer never sees the items. Its limits are elsewhere, part of the model is
outsourced to a public server, the workload is a small CNN on MNIST, and nothing ties the test
items to a pool the developer could not already have trained on. The clean constructions are an MPC
or FHE evaluation between the model owner and a test-set holder, where the model owner learns only
the aggregate score, or an auditor-as-prover design where the party holding the test set runs the
prover against a committed model. The first exists in miniature, pvCNN is that shape, with the
correctness zk-proven and the per-tester proofs aggregated, but not as a benchmark protocol. The
auditor-as-prover design nobody has built at all.

**3. Prove the test items were sampled honestly from a committed pool.** Otherwise you have moved
the cheating from the model owner to the auditor, who can cherry-pick items to make a favoured
model look good. A public sampling rule over a committed pool, verifiable sampling, is the fix,
and it is well within reach of the existing machinery.

**4. Handle metrics that are not exact match.** Accuracy on a multiple-choice benchmark is a
comparison and a sum, and is easy in-circuit. Free-form generation graded by a rubric, or by
another model, is not, and that is what modern LLM benchmarks are. A system that proves MMLU-style
accuracy is doing something the existing techniques nearly cover; a system that proves a score from
an LLM-judged benchmark has to prove the judge too, which recursively reopens the entire problem.

**5. Report the cost per test item, not just per proof.** Accuracy proving is inference proving
multiplied by the size of the evaluation set, and evaluation sets are not small. Any system whose
per-item cost is that of the inference cell will not survive contact with a real benchmark suite.

:::debate  Is testing even a separate cell?
The survey's taxonomy makes testing an objective in its own right, and we keep it because the
economics are distinct, the buyer of a testing proof is a regulator, an exchange or a customer,
not the user of a single query. But *mechanically*, every system in it is an inference prover with
a sum on top. The argument for the cell is that its hard problems (commitment ordering, test-set
exposure, honest sampling) are not inference problems at all, and they are invisible if you file
these papers under inference. The argument against is that as currently written, the papers here
are inference papers, and the hard problems are the ones nobody worked on.
:::

## What is honest to say about this cell today

It is thin, and it is thin for a good reason that its inhabitants have not stated. Proving that
you evaluated correctly is not the difficult claim; proving that you were *entitled* to evaluate, 
that the model predates the test set, and that you never saw the answers, is. The first is
cryptography. The second is a protocol design problem with cryptography in it, and it is
unclaimed.
