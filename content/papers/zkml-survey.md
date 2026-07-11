---
title: ZKP-VML Survey
paper: zkml-survey
status: reviewed
---

## What is new

The taxonomy, and it is the reason this repo is organized the way it is. The survey's decisive move
is to split *what is being proven* into three objectives — **inference** ("this model produced this
output on this input"), **testing** ("this model achieves this accuracy on this dataset"), and
**training** ("this model is the result of correctly training on this data") — and then to insist
that a system's cost is only interpretable relative to which one it targets. That distinction is
what makes it possible to notice that [[zkdt]] and [[zkcnn]] are doing something categorically
different from [[zkgpt]], and it is a better organizing principle than "by proof system," which is
how most of the field talks about itself.

Its Table VII — a timeline of thirty systems, from [[safetynets]] in 2017 through to 2025 — is the
single most useful artifact in the paper, and is where most of the older entries in `papers.yml`
came from.

Beyond that: it is a survey. There are **no original benchmarks**, no reimplementations, no
reproductions. It is excluded from the plots for that reason, and it should be.

## What it actually proves

Nothing, in the technical sense — but the question worth asking of a survey is *what did the authors
actually verify?*, and the answer is: **they read abstracts.**

Its quantitative tables (IV for training, V for testing, VI for inference) are compilations of
numbers as reported by the primary papers. They are not re-measured, not normalized for hardware,
not normalized for bit width, not normalized for sequence length, and — most consequentially — **not
checked against the primary papers' own tables.**

The coverage window is worth noting too: the abstract states the review covers "ZKML research
published from June 2017 to August 2025," and the version in `references/` is a March 2026 revision
that did not extend it. So [[deepprove]], [[jolt-atlas]] and [[nanozk]] — the entire 2026 frontier
this repo is built around — are outside its scope. It is a good map of a field that has since moved.

## What to distrust

**Table VI, specifically and concretely.** Three of this repo's known conflicts trace to it, and
reading the primary papers has now resolved the most important one against the survey.

:::audit The survey's zkLLM row cannot be reconciled with zkLLM
Survey Table VI reports [[zkllm]] at **"< 3s"** verification and **"< 10KB"** proof size.

zkLLM's own Table 1 prints verifier times of **3.71 s** and **3.95 s** for its two 13B models, and
proof sizes of **141–188 kB**.

The verification figure is an inherited error: zkLLM's *abstract* promises "1-3 seconds," and its own
Table 1 contradicts its own abstract. The survey copied the abstract.

The proof size is worse — it matches *neither* zkLLM's abstract ("less than 200 kB") *nor* zkLLM's
table. It is off by more than an order of magnitude and has no visible source. `papers.yml` records
this as an unresolved conflict; it is now resolved. **Trust the paper's table, not the survey, and
not the paper's abstract either.**
:::

That single row tells you the failure mode. The survey is transcribing headline claims, and headline
claims in this field are systematically the most flattering number an author could print. The other
two recorded conflicts have the same shape — the survey's figures for ZKML and Lu et al. on GPT-2
disagree with [[zkgpt]]'s direct re-measurement of those same systems, and [[zkgpt]] is the only
party that actually ran them.

**The 33-byte proof size for [[zkdl]]** (Table IV) is smaller than a single pair of group elements
and cannot be right for any pairing-based or FRI-based scheme. It is still in `papers.yml` flagged as
implausible, and it should stay flagged until someone reads the zkDL paper.

**Hardware is recorded but never used.** Table VI diligently lists the platform for each system — a
large cloud instance here, an A100 there, an 8-core desktop somewhere else — and then presents the
proving times side by side as though they were commensurable. The survey's own column shows they are
not, and the survey never says so.

**Quantization is absent.** The word does not organize anything in this survey, and there is no
column for bit width in any of the three tables. This is the field's central confounder — [[spagkr]]
measures ternary quantization alone buying a further several-fold prover speedup, [[zen]] measures
proof-friendly quantization cutting constraint counts by an order of magnitude — and a survey whose
entire purpose is to make systems comparable does not track the variable that makes them
incomparable. That omission is the gap this repo exists to fill.

**Use it for the map, not the measurements.** The taxonomy is good and the timeline is genuinely
useful. Every number sourced from it in `papers.yml` carries `numbers_source: survey` for a reason,
and the reason has now been demonstrated rather than assumed.
