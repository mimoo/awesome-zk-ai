---
title: When verifiability is not worth the price
section: alternatives
order: 10
lede: >-
  Verifiability is not a synonym for zero knowledge. ZK buys a succinct,
  non-interactive, cryptographic guarantee. The alternatives buy a weaker but crisply
  stateable one, for a small fraction of the cost, and for most deployments that is
  the better trade.
papers: [opml, opp-ai, zk-opml, optimistic-tee-rollups, tee-confidential-llm, proof-of-sampling, proof-of-quality, lightweight-sampling-inference]
status: reviewed
---

This section exists so that the rest of the site cannot quietly assume its own premise.

A zkML prover is orders of magnitude slower than the inference it proves; the
[inference benchmarks](/zk-inference/) carry the figures. That is a very large bill, and it
buys something specific: a proof that *anyone* can check, that reveals nothing, that requires
trusting no hardware and no counterparty, and that stays valid forever without anyone
staying online. Some deployments need exactly that. Most do not.

The table below is not about speed. The right way to compare the rows in it is **not on
speed** at all. It is on the trust assumption, what, precisely, must be true for the
guarantee to hold, and who is in a position to make it false.

{{ table:alternatives_to_zk }}

## What each approach is actually assuming

**Zero knowledge assumes mathematics.** The verifier needs to believe a hardness
assumption and a correct implementation. Nobody has to be honest; nobody has to be
watching; no vendor has to be trustworthy. This is the strongest assumption set available
and it is why ZK is the answer when the verifier is adversarial, anonymous, or a
blockchain. It is also an assumption about the
*implementation* as much as the mathematics, and the implementations are young.

**Optimistic systems assume someone will bother.** [[opml]] and its relatives are secure
under *AnyTrust*: any single honest challenger can force correct behaviour. That is a
genuinely weak requirement and it is why the overhead is roughly nothing. It is also
three requirements dressed as one, an honest party must **exist**, must be **watching**,
and must find it **worth paying** to challenge, and it buys a guarantee that only holds
*after a challenge window elapses*. [The optimistic page](/alternatives/optimistic/) takes
that apart.

**TEEs assume a hardware vendor.** [[tee-confidential-llm]] is the row that frames the
entire field, because its overhead is a rounding error next to ZK's. If your verifier will
accept an attestation signed by NVIDIA, then ZK is an extremely expensive way to buy a
confidence you could have had for free. ZK's answer is not that TEEs are bad, they are
what is actually in production, but that *some verifiers cannot make that assumption*.
[The TEE page](/alternatives/tees/) states the trade without sneering at it.

**Sampling assumes a rational adversary.** [[proof-of-sampling]] and
[[lightweight-sampling-inference]] do not try to make cheating impossible. They make it
*detectable with some probability* and *expensive when detected*, and then rely on the
prover being economically rational. This is the only family with a **tunable, quantifiable**
guarantee, you can dial the soundness error, which makes it the most intellectually
honest of the alternatives and the one we spend the most time on, on
[the sampling page](/alternatives/sampling/).

**Proof of Quality assumes a judge.** [[proof-of-quality]] is the last row on the page and the
strangest, because it does not verify the computation *at all*. An inference node answers the query
off-chain; a panel of assessors then scores the (query, response) pair with a lightweight BERT
cross-encoder and the network pays out on the aggregate. Nothing checks that the model ran. Nothing
checks *which* model ran.

That makes it the far endpoint of this entire spectrum, and it deserves to be stated precisely,
because the name works against comprehension:

| | The claim established |
|---|---|
| **zkML** | *This* committed model produced *this* output on *this* input. |
| **Optimistic / sampling** | The same claim, re-executed by someone else, wholly or in part. |
| **Proof of Quality** | *Some* model produced an output that a BERT cross-encoder scored highly. |

Those are not the same claim at three price points. The third is a different claim. **Model
substitution, the precise attack zkML exists to prevent, is not prevented.** It is made
*unprofitable for a rational node* by tuning a reward parameter, and the reward function depends
only on the assessors' scores, so any model that scores the same collects the same payout. The
authors do not concede this; they *assume* it away, in a hypothesis stipulating that no cheaper
model is as good as a dearer one.

And the judge is weak.

:::audit  The judge is barely correlated with the thing it judges
By the paper's own Table 3, the cross-encoder's Pearson correlation with GPT-4 ground-truth
quality is 0.12 (GPT-3.5), 0.13 (GPT-4), 0.28 (Mistral-7B), 0.35 (Mixtral-8x7b) -- and -0.06 on
Llama3-70b, i.e. anti-correlated on one of the five models tested.
:::

The authors are candid about why: they acknowledge that the cross-encoder "is unable to identify
the subtle difference on the accuracy of the information itself", which is precisely the failure
mode you most want to catch. **A verification scheme is only as sound as its verifier**, and this
one is barely correlated with the thing it is verifying, which is exactly the regime where a
subtly wrong answer passes.

None of that makes it useless. Assessment costs well under a second and consensus settles in
milliseconds, so for a decentralized *marketplace*, where the real risk is a node collecting fees
for garbage rather than an adversary steering one classification, it is a sensible mechanism. It
is a good answer to "did I get my money's worth." It is not an answer to "was this computed
correctly," and the word *proof* in its title should not be read as claiming otherwise: there is no
proof object, no soundness error, and no extractor. It is mechanism design with a statistical judge.

**The hybrids assume you can partition the problem.** [[opp-ai]] runs the
privacy-sensitive submodel in ZK and the rest optimistically. [[zk-opml]] decomposes
inference to the ONNX operator level and generates proofs only where they are needed.
[[optimistic-tee-rollups]] is the most interesting synthesis on the page: TEEs for
throughput, fraud proofs for finality, and **stochastic ZK spot-checks** used purely to
bound the risk that the hardware itself was compromised. ZK applied where it is cheap
rather than everywhere.

:::debate  Is the hybrid the honest answer, or the one that inherits every assumption?
The optimist's reading: use each tool where its cost curve is favourable, and you get
most of ZK's guarantee for a small fraction of ZK's bill. The pessimist's reading: a
system whose security rests on hardware attestation *and* an honest challenger *and* a
sampling argument has three ways to fail, not one third of a failure. Nobody has written
down the composed security statement for any of these hybrids. Until someone does, the
optimist is asserting rather than proving.
:::

## The inversion worth internalising

The naive framing is "ZK is slow, therefore ZK loses on latency." That is not quite what
happens at scale, and [[opml]]'s own framing makes the sharper point: an optimistic system
reaches finality after a **fixed** challenge window, while a ZK system reaches finality
after a proving time that **grows with model size**. Past some model size, the proof takes
longer than the challenge period, and the optimistic system, the one with the weaker
guarantee, is also *the faster one to finality*.

So the trade is not "pay more, wait longer, get a better guarantee." Above a certain
scale it is "pay more, wait longer, get a better guarantee **and** worse latency." That is
a much harder sale, and it is why the honest case for zkML is not performance. It is the
trust assumption, and nothing else.

## So when is ZK actually the right tool?

Four situations, and they are narrower than the literature's enthusiasm suggests:

1. **The verifier is adversarial or anonymous.** No challenger will show up on your
   behalf. Nobody will trust your attestation.
2. **The model or the input must stay private**, and the proof must still convince a
   third party. This is the combination no alternative on the table offers, optimistic
   verification requires re-execution, which requires the weights.
3. **Verification must be non-interactive and permanent.** A proof settled on-chain is
   checked by parties who were not present, years later. A challenge window that has
   closed is not a proof.
4. **No hardware root of trust is acceptable**, a regulator, a competing counterparty, a
   public chain.

Outside those four, one of the rows above is probably cheaper by a margin that no protocol
improvement is going to close.

:::gap  Nobody has published the composed security statement
Every hybrid on this page combines two or three trust models, and not one paper states
the resulting guarantee as a single theorem, what an adversary must corrupt, and with
what probability they succeed. The security models are described in prose and composed by
vibes. For a field that prides itself on proofs, that is a conspicuous hole.
:::
