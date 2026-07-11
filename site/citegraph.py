#!/usr/bin/env python3
"""
Rebuild the citation graph by scanning the PDFs in references/.

    python3 site/citegraph.py            # dry run: show what would change
    python3 site/citegraph.py --write    # apply

An edge A -> B means "A's text mentions B" -- a PROXY for citation, not a verified one.
The matcher is deliberately conservative (word-boundary, case-insensitive, on a set of
aliases per paper), because a false edge is worse than a missing one: the headline finding
of this graph is that *no* edges cross between the verifiability and privacy literatures,
and one spurious match would silently destroy that claim.

So this script never overwrites the graph on its own. It proposes additions and removals
and makes you look at them. `--write` applies them; the diff is the review.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "references"
GRAPH = REFS / "citation-graph.yml"

# Some PDFs are filed under a stem that is not the graph node id.
STEM_TO_ID = {"twist-and-shout": "twist-shout"}

# Aliases that are genuinely ambiguous: the string is both a system name AND a common
# term of art, so a hit is NOT evidence of a citation.
#   "ZKML"  -- Kang et al.'s system is called ZKML, but "zkML" is also the name of the
#              entire field. Nearly every paper here says it without citing them.
#   "Jolt"  -- matches inside "Jolt Atlas", so every Jolt Atlas mention double-counts.
# Edges into these are reported with a "?" and are NEVER written without --force-ambiguous.
AMBIGUOUS = {"zkml-kang", "jolt"}

# Matching is case-INSENSITIVE by default: bibliographies title-case everything, so Nimbus's
# reference list says "Ciphergpt" and "Sirnn", and a case-sensitive match silently misses a
# real citation. But a handful of system names are also ordinary English words, and for those
# case is the only thing separating a citation from a sentence. Those stay case-sensitive.
CASE_SENSITIVE = {"iron", "bolt"}

# Aliases per node. A paper is "mentioned" if any alias appears as a whole word.
# Keep these tight. "ZEN" or "ZIP" as bare words would match half the English language,
# so they get no alias and are matched by title only -- better a missed edge than a lie.
ALIASES = {
    "deepprove": ["DeepProve", "Deep-Prove"],
    "jolt-atlas": ["Jolt Atlas", "Jolt-Atlas", "JoltAtlas"],
    "zkgpt": ["zkGPT", "ZKGPT"],
    "zkllm": ["zkLLM", "ZKLLM"],
    "zkpytorch": ["zkPyTorch", "ZKPyTorch", "ZKPYTORCH"],
    "zkml-kang": ["ZKML"],
    "zktorch": ["ZKTorch", "zkTorch"],
    "zkcnn": ["zkCNN", "ZKCNN"],
    "vcnn": ["vCNN"],
    "mystique": ["Mystique"],
    "safetynets": ["SafetyNets", "Safety-Nets"],
    "ezkl": ["EZKL", "ezkl"],
    "artemis": ["Artemis", "Apollo"],
    "spagkr": ["SpaGKR"],
    "nanozk": ["NANOZK", "NanoZK"],
    "iron": ["Iron"],
    "ciphergpt": ["CipherGPT"],
    "bolt": ["BOLT"],
    "nimbus": ["Nimbus"],
    "bootstrapping-fhe": ["Bootstrapping is All You Need"],
    "zkml-survey": ["ZKP-VML"],
    "modulus-cost-of-intelligence": ["Cost of Intelligence"],
    # external building blocks (no papers.yml entry; declared under `external:`)
    "gkr": ["GKR"],
    "jolt": ["Jolt"],
    "lasso": ["Lasso"],
    "twist-shout": ["Twist and Shout", "Twist & Shout"],
    "expander": ["Expander"],
    "cheetah": ["Cheetah"],
    "sirnn": ["SIRNN"],
    "the-x": ["THE-X"],
    "bumblebee": ["BumbleBee", "Bumblebee"],
}


def text_of(pdf: Path) -> str:
    try:
        return subprocess.run(
            ["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  ! could not read {pdf.name} (is pdftotext installed?)", file=sys.stderr)
        return ""


def main():
    if not REFS.exists():
        sys.exit("no references/ directory")
    existing = yaml.safe_load(GRAPH.read_text()) if GRAPH.exists() else {}
    old = {k: sorted(v or []) for k, v in (existing.get("citations") or {}).items()}
    external = existing.get("external") or {}

    pdfs = sorted(p for p in REFS.rglob("*.pdf"))
    print(f"scanning {len(pdfs)} PDFs...\n")

    new: dict[str, list] = {}
    flagged: list[tuple] = []
    for pdf in pdfs:
        src = STEM_TO_ID.get(pdf.stem, pdf.stem)
        if src not in ALIASES:
            print(f"  · {src}: no alias entry in citegraph.py -- add one, or it can never be cited")
        body = text_of(pdf)
        if not body:
            continue
        hits = []
        for target, names in ALIASES.items():
            if target == src:
                continue  # a paper does not cite itself
            pat = "|".join(re.escape(n) for n in names)
            flags = 0 if target in CASE_SENSITIVE else re.I
            if not re.search(rf"(?<![\w-])(?:{pat})(?![\w-])", body, flags):
                continue
            if target in AMBIGUOUS:
                flagged.append((src, target))
                continue
            hits.append(target)
        if hits:
            new[src] = sorted(hits)
    # keep any ambiguous edges that were already in the yml: a human put them there
    for a, ds in old.items():
        for d in ds:
            if d in AMBIGUOUS and a in new and d not in new[a]:
                new[a].append(d)
        if a in new:
            new[a] = sorted(new[a])

    added = {a: sorted(set(new.get(a, [])) - set(old.get(a, []))) for a in new}
    removed = {a: sorted(set(old.get(a, [])) - set(new.get(a, []))) for a in old}
    added = {k: v for k, v in added.items() if v}
    removed = {k: v for k, v in removed.items() if v}

    if not added and not removed:
        print("no changes -- the graph matches the PDFs.")
        return

    for a, ds in added.items():
        for d in ds:
            print(f"  + {a} -> {d}")
    for a, ds in removed.items():
        for d in ds:
            print(f"  ~ {a} -> {d}   (in the yml, NOT found by the matcher -- KEPT, review by hand)")

    if flagged:
        print("\nAMBIGUOUS -- string matched, but the string is also a term of art. NOT applied:")
        for a, d in sorted(set(flagged)):
            print(f"  ? {a} -> {d}")
        print("  (add these by hand if you have checked the bibliography.)")

    # ADDITIVE ONLY. A regex that fails to find a citation is weak evidence -- pdftotext
    # mangles ligatures, hyphenation and line breaks, and a bibliography may title-case a
    # name past our alias. A human who added an edge saw something we cannot see, so the
    # matcher never gets to delete their work; it only ever reports the discrepancy.
    for a, ds in removed.items():
        new.setdefault(a, [])
        new[a] = sorted(set(new[a]) | set(ds))

    print(
        f"\n{sum(len(v) for v in added.values())} to add, "
        f"{sum(len(v) for v in removed.values())} unmatched-but-kept, "
        f"{len(set(flagged))} ambiguous and skipped."
    )
    if "--write" not in sys.argv:
        print("\ndry run. Re-run with --write to apply. LOOK AT THE EDGES FIRST: a false edge\n"
              "between the verifiability and privacy clusters would quietly destroy this\n"
              "corpus's headline finding.")
        return

    out = ["# Citation/dependency graph, built by scanning the PDFs in references/ with pdftotext.",
           "# edge A -> B  means: paper A's text mentions/cites B.",
           "# Proxy: a mention anywhere in A (body or reference list). Not hand-verified.",
           "# Regenerate: python3 site/citegraph.py --write",
           "citations:"]
    for a in sorted(new):
        out.append(f"  {a}:")
        for d in new[a]:
            out.append(f"    - {d}")
    out.append("")
    out.append("# External building blocks: cited BY our corpus but not part of it.")
    out.append("external:")
    for k, v in external.items():
        out.append(f"  {k}: {v}")
    GRAPH.write_text("\n".join(out) + "\n")
    print(f"\nwrote {GRAPH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
