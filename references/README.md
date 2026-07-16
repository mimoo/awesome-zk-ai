# References

Primary-source PDFs we've read, organized by cell of the [verifiability × privacy ×
phase](../README.md) map. Only papers whose PDFs we could actually obtain are here — many
entries in [`../papers.yml`](../papers.yml) are abstract-level only and have no PDF.

```
proving-inference/   zkML inference — DeepProve, Jolt Atlas, zkPyTorch, zkGPT, zkLLM, zkCNN…
proving-training/    zkPoT — Kaizen, zkDL, VeriLoRA, Optimum Vicinity, ZKBoost
privacy-inference/   secure 2PC/FHE inference — Iron, CipherGPT, BOLT, Nimbus, Bootstrapping-FHE
federated/           verifiable FL & secure aggregation — ACORN, EIFFeL, PRoVeFL
numerics/            the shared fixed/float substrate — garg-fp, secfloat, archer-ieee…
alternatives/        non-ZK verifiability — opML, TEEs, sampling
surveys/             ZKP-VML survey, Modulus "Cost of Intelligence" report
```

Cell directory names match the `references/<cell>/` convention in
[`AGENTS.md`](../AGENTS.md). Many entries in [`../papers.yml`](../papers.yml) are abstract-level
only and have no PDF here yet — that gap is deliberately visible (`make check` warns about PDFs
held-but-unread, and papers with no PDF at all).

## Citation graph

`citation-graph.{dot,svg,png,yml}` is a dependency graph built by `pdftotext`-ing every PDF
here and scanning each paper's text for mentions of the others (plus key external
building-block papers: Jolt, Lasso, Twist & Shout, zkCNN, GKR, Cheetah, SIRNN, BumbleBee,
THE-X, Mystique, Expander, EZKL).

- **Edge A → B** = paper A's text mentions/cites paper B. It's a *proxy* (any mention in body
  or reference list), not a hand-verified citation, so treat it as directional-ish evidence.
- **Node colour** = cell: teal = proving-inference, red = privacy-inference, green = survey,
  purple = report, grey box = external primitive.

**The headline finding:** the proving-inference cluster and the privacy-inference cluster are
**citation-disconnected** — zero edges cross between them. The zkML papers cite each other +
GKR/Lasso/zkCNN/Jolt; the MPC/HE papers cite each other + Cheetah/SIRNN/THE-X. Two separate
research communities attacking the two columns (verifiability vs privacy) of the same 2×2.

To regenerate after adding PDFs: re-run the extractor (see the scratchpad `citegraph.py`), then
`dot -Tsvg references/citation-graph.dot -o references/citation-graph.svg`.
