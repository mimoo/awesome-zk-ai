---
title: A claim about a model, not about a computation
section: properties
order: 10
lede: >-
  Inference, testing and training all prove that a computation ran correctly. These
  systems prove that a model *is* something — fair, licensed, uncensored, compliant. That
  is a fourth objective, and the prior surveys do not have a slot for it.
papers: [fairproof, fairzk, oath, zkaudit, zk-software-auditing, e2e-ai-pipeline-verifiability, zkprov, zkml-survey, zkcnn, deepprove, zkml-kang]
status: draft
---

The canonical taxonomy of verifiable machine learning has three objectives, and
[[zkml-survey]] states it in as many words:

:::quote{src="ZKP-VML Survey" sec="§II-C, Verifiable Machine Learning"}
Depending on the stage of the ML pipeline being certified, verifiable machine learning can be divided into three primary categories: Verifiable Training, Verifiable Testing, and Verifiable Inference.
:::

Note the axis it slices on: **the stage of the pipeline being certified.** Training, then
testing, then inference — one bucket per stage, and every bucket contains proofs *that a
computation was performed as declared*. It is a good taxonomy and it exhausts its axis.

The systems on this page do not fit it, and the reason is not that they are a fourth
stage. It is that they are not about a stage at all. **They prove a property of the
artefact rather than the correctness of a process.** "This model does not discriminate
against a protected group." "These weights were derived from data I was licensed to use."
"This provider is not censoring outputs for some users." None of those is a statement
about whether a matmul was computed correctly, and you cannot reach any of them by
proving harder that one was.

We treat that as a **fourth verification objective**. It is the one place where this SoK
departs structurally from the surveys it builds on — see [Surveys](/surveys/) for the
other two departures.

{{ table:proving_properties }}

## Why it genuinely does not reduce to the other three

The obvious objection is that a property proof is just an inference proof wearing a hat:
to prove fairness, run the model on a dataset and prove the outputs satisfy a predicate.
That works, and it is what the first generation of these systems did. It also does not
scale, and — more importantly — it proves the wrong thing.

**It does not scale**, because a property of a *model* quantifies over inputs, while a
proof of *inference* is about one input. Proving a group-fairness property by inference
means proving inference over an entire evaluation set, and the cost is the cost of the
whole [inference section](/zk-inference/) multiplied by the size of the set.

[[fairzk]] is the system that breaks this, and the unlock is conceptual rather than
cryptographic: it derives fairness bounds from the **model parameters plus aggregated
input statistics**, rather than by proving inference over a specific dataset. That is a
different mathematical object — a bound on the model's behaviour, not a transcript of its
behaviour — and it is why FairZK reaches a parameter count that inference-based fairness
proofs cannot (see the table; the prover-time improvement over prior work is large enough
that it is a change of kind, not degree).

**It proves the wrong thing**, because a property proved *on a dataset* is a property of
the dataset as much as of the model. Prove fairness on the evaluation set and a malicious
provider will hand you a model that is fair on the evaluation set. [[oath]] is the system
that takes this seriously: it targets **online** group fairness — fairness on the traffic
the model actually serves, under distribution shift and under provider malfeasance — using
a cut-and-choose protocol over statistical properties of the fairness definition, with a
ZK proof of correct inference as a *subroutine* rather than as the whole mechanism. Note
what that composition says: property proofs sit **on top of** the inference systems in this
SoK. They are not a competing cell; they are a consumer of one.

## The problem that does not go away

Here is the thing an auditor has to hold onto, and it is not a cryptographic problem, so
no amount of cryptography will fix it.

**A proof that a model is fair is only as good as the definition of fairness it encodes,
and that definition is contestable in a way that "this matmul was computed correctly" is
not.**

Correctness has a referent. There is a fact of the matter about what $A \times B$ is, the
prover and verifier agree on it in advance, and a soundness bug is a discrepancy against
that fact. Fairness has no such referent. It has a *literature* — demographic parity,
equalized odds, predictive parity, individual fairness, counterfactual fairness — whose
central results include the impossibility theorems establishing that the major group-fairness
criteria **cannot in general be satisfied simultaneously**. Choosing one is choosing a
side in a normative argument, and it is a choice the *prover* is making when they write
the circuit.

So the security property degrades in a specific and predictable way. A sound ZK proof of
fairness gives you:

> The provider ran a computation which, if the predicate encoded in this circuit is the
> right notion of fairness, and if the protected-attribute labels fed to it are honest,
> establishes that this model satisfies it on this distribution.

Every clause in that sentence is a place to attack, and only the first one is
cryptographic.

:::audit  Read the predicate, not the proof
On a property-proving system, the circuit's soundness is the *easy* half of the review.
The load-bearing questions are upstream of it:

- **Which fairness definition is encoded**, and who chose it? Would the model pass under a
  different one? (Given the impossibility results, for a non-trivial model: almost
  certainly yes, some definition exists that it fails.)
- **Where do the protected-attribute labels come from?** A fairness proof over demographic
  labels the prover supplied is a proof about the prover's labels.
- **What distribution is it over?** A property proven on a dataset the prover selected is a
  property of that selection. This is [[oath]]'s entire reason for existing.
- **What is the quantifier?** [[fairproof]] certifies *local* fairness — a certificate
  about the model's behaviour in a neighbourhood of a point. That is a genuinely different
  claim from a global one, and a reader skimming for the word "fairness" will not notice
  the difference.

**What the bug looks like:** a perfectly sound proof of a predicate nobody should have
accepted. No constraint is missing. The circuit computes exactly what it says. The claim is
still worthless.
:::

This is not a reason to dismiss the work — it is a reason to *read it correctly*. The
cryptography is doing something real: it lets a provider demonstrate a property **while
keeping the model confidential**, which is the only reason this is hard at all. Absent
confidentiality, an auditor would just be given the weights. The proof is buying
confidentiality, not objectivity, and it is worth being precise that those are different
purchases.

## Provenance is the more tractable half

The fairness systems get the attention; the provenance ones may end up mattering more,
precisely because they *do* have a referent.

"These weights were derived from this committed dataset" is a claim with a fact of the
matter, exactly like "this matmul was computed correctly." There is no contestable
definition in the middle. And it is the claim that copyright litigation, licensing
compliance, and the EU AI Act's data-governance provisions actually turn on.

[[zkaudit]] is the most complete system here and it straddles both. Its first phase,
`ZKAudit-T`, proves the model was trained by SGD on a committed dataset — that is a
zero-knowledge proof of training, and it cross-lists into
[the training section](/zk-training/). Its second phase, `ZKAudit-I`, then audits arbitrary
user-defined properties over the hidden data and weights: copyright, censorship detection,
counterfactuals. The layering is the right architecture — pin the artefact first, then
interrogate it — and it is why zkAudit supports property audits that the fairness systems'
narrower approach cannot express.

zkAudit also makes a design choice with consequences well beyond this page: **the weights
stay secret but the architecture is public.** That is exactly the mitigation
the Fiat–Shamir open question turns on. A system that pins its
architecture is a system whose prover did not get to choose its circuit.

[[zkprov]] is the cheap version of the same idea — prove *which dataset* a model was
trained on, without proving the training computation at all. Weaker claim, far weaker
cost, and for a licensing dispute it may be the entire claim anyone wanted.

## The system-level end of the spectrum

Two entries reach past the model to the thing the model is embedded in, and we have read
neither, so they are listed rather than assessed. [[zk-software-auditing]] audits an
AI-enabled *system* for regulatory compliance rather than auditing a model. And
[[e2e-ai-pipeline-verifiability]] frames data ingestion, training and inference as a single
verifiable pipeline — which is, in effect, the argument that the three-objective taxonomy
should be replaced by one continuous chain of custody rather than extended by a fourth
bucket.

:::gap  Nobody has connected the chain end to end
Every link exists on its own: dataset provenance ([[zkprov]]), training ([[zkaudit]]'s
`ZKAudit-T`), inference ([the inference section](/zk-inference/)), and properties (this
page). No published system carries a single commitment through all four, so that a verifier
can trace *this output* back to *this weight commitment* back to *this training run* back
to *this licensed dataset*. [[e2e-ai-pipeline-verifiability]] proposes the framing; we have
not read it, and we do not know whether anyone has built it.
:::

## The people are the same people

Worth noticing, because it explains why these clusters share techniques. [[fairproof]] is
Yadav, Roy Chowdhury, Boneh, Chaudhuri — Roy Chowdhury also wrote EIFFeL, and Boneh
co-authored Prio, both in [federated aggregation](/federated/). [[fairzk]] includes Yupeng
Zhang, who co-authored [[zkcnn]] and [[deepprove]]. [[zkaudit]] comes from the group behind
[[zkml-kang]].

The verifiable-FL, zkPoT, inference and property-proving clusters are not four communities.
They are one community, working four problems, and the cross-pollination is why a
fairness system can suddenly get fast when someone brings a sum-check to it.
