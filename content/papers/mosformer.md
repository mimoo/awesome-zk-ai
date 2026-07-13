---
title: Mosformer
paper: mosformer
status: reviewed
---

Mosformer closes the gap this SoK named — *nobody has malicious security at transformer scale* — and
it closes it in exactly the way the [private inference page](/private-inference/) predicted it would
have to: **by adding a party.**

Read the threat model before you quote anything else.

## The threat model, precisely

:::quote{src="Mosformer" sec="§3.3, Threat Model"}
Consistent with the threat models adopted in [1, 2], we assume a security model with abort under the
honest-majority setting against malicious adversaries, where at most one out of three parties may be
corrupted.
:::

Four qualifiers, all load-bearing:

- **Three parties**, not two. Three *non-colluding* servers. That is a substantially stronger trust
  assumption than the dishonest-majority 2PC of [[iron]], [[bolt]], [[cheetah]] and [[nimbus]].
- **Honest majority** — at most one of three is corrupted.
- **Malicious** — a corrupted server may deviate arbitrarily. This is the real advance.
- **With abort** — *not* robust, *not* guaranteed output delivery. A detected cheat kills the
  protocol.

So the corrected statement is: **maliciously-secure transformer inference exists, in 3PC
honest-majority-with-abort. In dishonest-majority 2PC it still does not.** Our claim was right about
2PC and wrong about the field.

## What is new

Malicious security is bought in three layers. **Verifiable DPFs** let the parties check in the
offline phase that the key-dealer distributed well-formed keys. **Redundant three-party execution**
of the online comparison produces three (2,2)-shares that fold into one replicated sharing, whose
consistency property detects online tampering — the paper is explicit that VDPFs alone "provide no
guarantees against online adversarial behavior." And **MAC-based consistency checks**, deferred to
the end of each encoder/decoder block, cost 16 rounds and about 5% of runtime.

On top of that sits an idea worth stealing: **operation-aware modulus conversion.** Different rings
for different operators — linear layers in $\mathbb{Z}_{2^{64}}$, softmax and reciprocal-sqrt in
$\mathbb{Z}_{2^{32}}$, ReLU and GELU in $\mathbb{Z}_{2^{16}}$. That is mixed-precision quantization,
in MPC vocabulary, and like every mixed-precision scheme it trades accuracy for speed: 30% runtime
and 25% communication, at up to **2.4% accuracy loss**. The paper reports both numbers, which is
more than most.

## The result that should embarrass the semi-honest line

Mosformer's **malicious** online phase beats the **semi-honest** 2PC state of the art on its own
benchmark. BERT-base, LAN, online: 59.47 s and 4.60 GB — against [[bolt]]'s 533.4 s / 59.61 GB,
BumbleBee's 184.86 s / 6.40 GB, and SHAFT's 171.31 s / 10.46 GB.

Stronger security. Faster online phase.

## What to distrust

:::audit  That is an online number, and the offline phase is enormous
Malicious BERT-base costs a **further 547.66 seconds and 67.35 GB** of preprocessing on LAN — 1339 s
on WAN — because the VDPF correlated randomness has to come from somewhere.

[[bolt]], BumbleBee, [[puma]] and Ditto report **zero** offline. SHAFT reports 39.36 s / 4.92 GB.

Comparing Mosformer's online column against a system that has no offline column is not a comparison.
The honest total for malicious BERT-base on LAN is roughly **607 seconds and 72 GB**, and on that
basis it does not beat BumbleBee at all.

The paper does not hide this — §7.4.2 states it plainly. But every headline in the abstract is an
online number.
:::

**No prior malicious protocol can run these models at all,** which is simultaneously the paper's best
claim and the reason its comparison is thin. Privformer is limited to the vanilla transformer of
Vaswani et al.; Falcon is a CNN framework. So the malicious-vs-malicious comparison — 5.3× over
Privformer, 3.4× over a Falcon the authors extended themselves — runs on a **45M-parameter vanilla
transformer, not on BERT or GPT-2**. The BERT and GPT-2 rows have no malicious baseline because there
was none. That is a real first; it is just not the head-to-head the abstract implies.

**Privformer was reimplemented by the authors** (no public source), so the malicious baseline is
their reconstruction of a competitor.

The clean number the paper does let you compute — **the cost of malicious security over its own
semi-honest variant** — is the one worth carrying: BERT-base online, 59.47 s vs 20.09 s (≈3.0×) and
4.60 GB vs 1.15 GB (4.0×). **Three to four times, not the order of magnitude the folklore assumes.**

And the conclusion is worth the price of admission:

:::quote{src="Mosformer" sec="§8, Conclusion"}
Although our work makes meaningful progress toward secure and efficient transformer inference,
running modern large language models under cryptographic settings remains impractical at present.
:::
