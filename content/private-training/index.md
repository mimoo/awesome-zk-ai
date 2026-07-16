---
title: Confidentiality without a proof
section: private-training
order: 10
lede: >-
  Encrypt the data, train on the ciphertext, prove nothing. This cell is the honest opposite
  of zkPoT -- and the most telling thing about it is not what it achieves but where it has
  retreated to: nobody is trying to train a model privately any more. They are trying to
  privately fine-tune one.
papers: [prift, privtuner, private-lora-he, cryptpeft, encryption-friendly-llm, verilora, iron, bolt, bootstrapping-fhe]
status: reviewed
---

This is the bottom-right cell of the 2x2, and it is the one with the crispest statement of what it
does *not* do. Secure multi-party computation and homomorphic encryption let a party train on data
it cannot read. They produce **no proof of anything**. The security model is almost always
semi-honest: a malicious participant can compute the wrong function, return a wrong model, and
nobody will ever know. You get confidentiality from a counterparty. You do not get correctness,
and there is no artifact to hand a third party.

{{ table:private_training_no_proofs }}

One of these entries is strong, four are indexed at abstract level, and we say so rather than
pretending otherwise.

## The retreat to fine-tuning is the finding

Look at the titles. [[prift]] is *private fine-tuning*. [[privtuner]] is HE plus LoRA, explicitly a
*parameter-efficient* fine-tuning scheme. [[private-lora-he]] is private LoRA fine-tuning under
homomorphic encryption. [[cryptpeft]] uses parameter-efficient fine-tuning to make private
*inference* cheap. [[encryption-friendly-llm]] changes the model architecture itself so that
encrypted computation over it is affordable.

Not one of them trains a model from scratch. On the evidence of their titles, and [[prift]] is the
only one of them we have read, each starts from a model pretrained in the clear and confines the
encrypted work to a small slice of it. (In [[cryptpeft]]'s case that slice is the privately
*evaluated* portion rather than a trained one; see below.) That is not a coincidence and it is not a
fashion, it is a capitulation, and it is the single most useful thing this cell tells you. **Full
private training of a modern model is not close.** The frontier is: keep the expensive part in
plaintext, and pay the cryptographic tax only on the part that is small enough to afford it.

[[prift]] is the clearest example of the pattern and the most useful paper here, because it is the
only one that measures the choice instead of asserting it. It uses a transformer as a *frozen
feature extractor* and then trains a small network on the privacy-protected features, and it
benchmarks the two dominant secure-computation approaches head to head on one real task using
off-the-shelf libraries (Crypten for MPC, TenSEAL for HE). Its findings, which we report
qualitatively because they are the kind of result that ages badly as a number: **MPC beats HE**,
and its *semi-private* mode, labels decrypted during training for speed, is substantially faster
than fully-private, at accuracy close to plaintext.

That semi-private mode deserves a second look, because it is a privacy relaxation hiding inside a
performance result. Decrypting the labels is not a small concession. In the medical and financial
settings that motivate this entire cell, **the label is frequently the sensitive attribute**, the
diagnosis, the default, the outcome. A system that hides the features and reveals the labels has
protected the cheap half.

:::gap  Nobody prices full private pretraining
The one paper in this cell we have read, [[prift]], does not report what it would cost to train a
model from scratch under MPC or HE, even as an extrapolation, and the four adjacent entries are
indexed at title level, so we cannot even say they tried. The retreat to fine-tuning looks
universal, and nowhere we have looked is it argued for. A single honest back-of-the-envelope, 
"here is the encrypted cost of one pretraining step at this scale, here is the step count, here is
the number", would be a genuine contribution, and it would tell everyone in this SoK how far away
the bottom-right cell really is.
:::

## The contrast pair worth memorizing

[[private-lora-he]] and [[verilora]] are the same workload with opposite guarantees. Both
fine-tune a large open model with LoRA. One hides the data from the party doing the computation and
proves nothing about the result. The other *claims* to prove the computation was done correctly and
hides nothing from the party doing it, a claim that reaches us through a survey, not through the
paper: we have not read [[verilora]].

Nobody does both for the training computation itself. The one place this SoK finds privacy and
verifiability in the same protocol is the federated cell, and what is proven there is that a
client's update is *well-formed*, never that it came from correct training. For the training
computation the pair above is the whole picture, and it holds at the inference layer too, the
private-inference systems ([[iron]], [[bolt]], [[bootstrapping-fhe]]) and the zkML systems answer
different questions and, as the citation graph shows, do not even read each other.

## What is missing from these entries

Being blunt about our own coverage: [[prift]] is the only entry here we have read carefully, and
even for it the PDF sits behind Cloudflare and its reference list has not been extracted, so the
four adjacent papers below it in `papers.yml` are **surfaced by search, not confirmed as PriFT's
citations**. Those four carry no author list, no venue, no hardware and no benchmark row. They are
indexed so the cell is not silently short, not because we can vouch for them.

Note in particular that [[cryptpeft]] is filed here but is, by its own title, a private
*inference* system, it uses PEFT as the mechanism for shrinking the privately-computed portion of
the network, not as the thing being trained. That is a defensible filing (the technique is the
same retreat), but a reader scanning the table should know the objective is different.

:::audit  What to ask a private-training deployment
Is the adversary semi-honest or malicious, and if semi-honest, what happens the day it is not?
Who holds the decryption keys, and what does the protocol reveal at the end (the model? the loss
curve? the labels?)? Is any part of the computation performed in plaintext for speed, and is that
part actually non-sensitive? And the question this cell can never answer well: **if the server
returns a bad model, how would you find out?**
:::
