---
title: How to cite, and how to correct
section: start
order: 40
lede: >-
  This is a living document with a build that checks itself. Cite the commit, not the page, 
  and if a number here is wrong, the fastest way to fix it is a pull request against the data.
status: reviewed
---

## Citing this

```bibtex
@misc{zkai,
  title        = {zkAI: Verifiable and Private AI --- A Systematization of Knowledge},
  author       = {{zkSecurity}},
  year         = {2026},
  howpublished = {\url{https://mimoo.github.io/awesome-zk-ai/}},
  note         = {Living document. Cite the commit hash for a stable reference.}
}
```

**Cite a commit, not a date.** Every page here is generated from `papers.yml`, and that file
changes whenever we read a primary source and discover the number we were carrying was wrong.
That has already happened more than once, and it will happen again. A citation to "the site,
in July" is a citation to something that no longer exists; a citation to a commit is
reproducible, because `make site` rebuilds the exact pages from the exact data.

If you are quoting a *number*, cite the paper it came from, not us. We are an index with
opinions, not a source. Every figure on this site carries a provenance dot telling you whether
we read it in the paper, took it from a survey, or got it from a vendor, follow it back.

## Correcting this

The correction you can make in thirty seconds is the most valuable one: **a number is wrong, or
its provenance is wrong.**

Numbers live in `papers.yml` and nowhere else. Prose is forbidden from hardcoding a benchmark, 
the build rejects it, precisely so that a correction to the data corrects every page at once.
So a fix is a one-line edit to a YAML file, and it propagates.

What we most want:

- **A figure we tagged `survey` that you can source to the primary paper.** Promote it, cite the
  table. This is the single highest-value contribution, because secondhand numbers are how a
  field starts citing comparison tables instead of running benchmarks.
- **A `claim_kind` that is wrong.** Is a system proving one forward pass, one token, or a whole
  generation? We have already got this wrong once, we recorded [[zktorch]]'s two-token *prompt
  pass* as a per-token decode cost, because an upstream comparison table did. If we have
  mislabelled yours, tell us; it is the field's most load-bearing distinction and the one
  everyone blurs.
- **A `null` we could fill.** `bits: null` means the paper does not state a bit width. If you
  know it does, say where.

:::gap What we will not accept
A number with no source. `numbers_source` is a required field, and `unknown` is a legitimate,
honest value, it means *we do not know where this came from and you should be suspicious*. What
is not legitimate is a plausible-looking figure with no provenance at all. We would rather have
a hole than a guess, because a hole is visible and a guess is not.
:::

## If you wrote one of these papers

Two requests, in order of how much they would help.

**Tell us what your throughput number actually measures.** Most of the disagreement on this site
is not about who is faster, it is about whether two systems are even claiming the same thing.
If your paper reports tokens per minute, we want to know: is that a forward pass, a single
decode step, or a full autoregressive generation with KV caching? Several papers do not say, and
we have recorded that as `claim_kind: full`, an ambiguity, not a claim.

**Tell us your bit width.** Proving cost depends on it, and most papers do not print it. A
throughput figure at 8 bits is not comparable to one at 16, and we cannot fix that from the
outside.

Both are one-line answers that make the whole table more honest, and neither requires you to
concede anything about your system.
