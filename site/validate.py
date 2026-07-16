#!/usr/bin/env python3
"""
Integrity checks for the zkAI SoK. Run with `make check`; exits non-zero on ERRORs.

The point of this file: a SoK rots when its prose and its data drift apart, and the
drift is invisible. Each check below corresponds to a specific way we have seen (or
expect) that to happen. ERRORs break the build. WARNs are debts we are choosing to
carry, and are printed so they stay visible instead of quietly accumulating.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
REFS = ROOT / "references"

ERRORS: list[str] = []
WARNS: list[str] = []


def err(m):
    ERRORS.append(m)


def warn(m):
    WARNS.append(m)


def load(p, default=None):
    """Parse YAML, failing with a message a human can act on rather than a traceback.
    The commonest break in this repo is a ': ' inside an unquoted prose scalar."""
    if not p.exists():
        return default
    try:
        with p.open() as f:
            return yaml.safe_load(f) or default
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        loc = f"{p.name}:{mark.line + 1}" if mark else p.name
        src = p.read_text().splitlines()
        line = f"\n\n    {src[mark.line].strip()}\n" if mark and mark.line < len(src) else ""
        sys.exit(
            f"\n{loc}: {getattr(exc, 'problem', exc)}{line}\n"
            "  A plain YAML scalar cannot contain ': ' -- YAML reads it as a mapping.\n"
            "  Wrap the value in double quotes, or use ' -- ' instead of ': '.\n"
        )


papers_raw = load(ROOT / "papers.yml", {})
sections = load(ROOT / "site" / "sections.yml", {})
citegraph = load(REFS / "citation-graph.yml", {}) or {}
operators = load(ROOT / "operators.yml", {}) or {}

PAPERS: dict[str, dict] = {}
CAT_OF: dict[str, str] = {}
for cat, entries in papers_raw.items():
    if not isinstance(entries, list):
        continue
    for e in entries:
        if isinstance(e, dict) and "id" in e:
            PAPERS[str(e["id"])] = e
            CAT_OF[str(e["id"])] = cat

# ---------------------------------------------------------------------------
# 1. every papers.yml category is owned by a section
#    (a new category added to papers.yml would otherwise vanish from the site)
# ---------------------------------------------------------------------------
owned = set()
for s in sections.get("sections", []):
    owned.update(s.get("papers_from") or [])
for cat in papers_raw:
    if isinstance(papers_raw[cat], list) and cat not in owned:
        err(f"papers.yml category '{cat}' is not listed in any section's papers_from: "
            f"in site/sections.yml. Its papers would not appear anywhere on the site.")

# ---------------------------------------------------------------------------
# 2. citation graph refers only to real ids
# ---------------------------------------------------------------------------
external = set((citegraph.get("external") or {}).keys())
for src, dsts in (citegraph.get("citations") or {}).items():
    if src not in PAPERS and src not in external:
        err(f"citation-graph.yml: source '{src}' is neither a papers.yml id nor declared "
            f"under external:")
    for d in dsts or []:
        if d not in PAPERS and d not in external:
            err(f"citation-graph.yml: '{src}' -> '{d}', but '{d}' is neither a papers.yml id "
                f"nor declared under external:")

# ---------------------------------------------------------------------------
# 3. operators.yml scheme keys are real papers
# ---------------------------------------------------------------------------
for o in operators.get("operators") or []:
    for sid in (o.get("schemes") or {}):
        if sid not in PAPERS:
            err(f"operators.yml: operator '{o.get('id')}' has a scheme key '{sid}' that is "
                f"not a papers.yml id")
    if not o.get("id") or not o.get("name"):
        err(f"operators.yml: an operator is missing id or name: {str(o)[:80]}")

# ---------------------------------------------------------------------------
# 4. content frontmatter: sections and paper ids exist
# ---------------------------------------------------------------------------
FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
SECTION_KEYS = {s["key"] for s in sections.get("sections", [])}
content_files = sorted(CONTENT.rglob("*.md")) if CONTENT.exists() else []
covered: set[str] = set()
page_paradigms: set[str] = set()  # per-page `paradigm:` overrides, for the paradigm check below

for f in content_files:
    rel = f.relative_to(ROOT)
    m = FM.match(f.read_text())
    if not m:
        err(f"{rel}: missing YAML frontmatter")
        continue
    fm = yaml.safe_load(m.group(1)) or {}
    if f.relative_to(CONTENT).parts[0] == "papers":
        pid = fm.get("paper") or f.stem
        if pid not in PAPERS:
            err(f"{rel}: frontmatter paper: '{pid}' is not a papers.yml id")
        else:
            covered.add(pid)
        continue
    if fm.get("section") not in SECTION_KEYS:
        err(f"{rel}: frontmatter section: '{fm.get('section')}' is not a key in site/sections.yml")
    if not fm.get("title"):
        err(f"{rel}: frontmatter is missing title:")
    if fm.get("paradigm"):
        page_paradigms.add(fm["paradigm"])
    for pid in fm.get("papers") or []:
        if pid not in PAPERS:
            err(f"{rel}: frontmatter papers: lists '{pid}', which is not a papers.yml id")

# ---------------------------------------------------------------------------
# 4b. paradigm axis: the top menu must be total and reachable
#     - every section's paradigm is a declared bucket
#     - every declared bucket is reachable (a section default, or a page override) and has a home
#     A dangling top tab (a bucket no page lands under) or a section tagged with an unknown
#     bucket is exactly the "wrong shape builds green" class this check closes.
# ---------------------------------------------------------------------------
PARADIGM_KEYS = {p["key"] for p in sections.get("paradigms", [])}
section_paradigms = {s.get("paradigm", "foundations") for s in sections.get("sections", [])}
for s in sections.get("sections", []):
    par = s.get("paradigm", "foundations")
    if par not in PARADIGM_KEYS:
        err(f"sections.yml: section '{s['key']}' has paradigm '{par}', not a key in paradigms:")
reachable = section_paradigms | page_paradigms
for p in sections.get("paradigms", []):
    if p["key"] not in reachable:
        err(f"sections.yml: paradigm '{p['key']}' is a top-menu tab no section or page lands "
            f"under -- it would render as a dead tab. Give a section/page paradigm: {p['key']}.")
    if not p.get("home") and p["key"] != "foundations":
        err(f"sections.yml: paradigm '{p['key']}' has no home: page to open to.")

# ---------------------------------------------------------------------------
# 4c. orgs.yml: every org's `paper:` cross-reference is a real papers.yml id, and every
#     `privacy:` is a declared mode. Keeps the landscape's org↔paper links from rotting.
# ---------------------------------------------------------------------------
orgs_yml = load(ROOT / "orgs.yml", {}) or {}
PRIVACY_MODES = set((orgs_yml.get("privacy_modes") or {}).keys())
GROUP_KEYS = {g["key"] for g in orgs_yml.get("groups", [])}
for o in orgs_yml.get("orgs", []):
    pid = o.get("paper")
    if pid is not None and pid not in PAPERS:
        err(f"orgs.yml: org '{o.get('org')}' has paper: '{pid}', which is not a papers.yml id.")
    if o.get("privacy") and o["privacy"] not in PRIVACY_MODES:
        err(f"orgs.yml: org '{o.get('org')}' has privacy: '{o['privacy']}', not in privacy_modes:.")
    if o.get("group") not in GROUP_KEYS:
        err(f"orgs.yml: org '{o.get('org')}' has group: '{o.get('group')}', not in groups:.")

# ---------------------------------------------------------------------------
# 5. [[wikilinks]] resolve
# ---------------------------------------------------------------------------
for f in content_files:
    body = f.read_text()
    for m in re.finditer(r"\[\[([a-z0-9\-\.]+)\]\]", body, re.I):
        if m.group(1) not in PAPERS:
            err(f"{f.relative_to(ROOT)}: [[{m.group(1)}]] is not a papers.yml id")

# ---------------------------------------------------------------------------
# 6. NO HARDCODED NUMBERS IN PROSE
#    This is the load-bearing check. A figure typed into markdown is a figure that
#    will silently contradict papers.yml the moment the YAML is corrected.
#    Allowed inside :::audit callouts, where quoting two conflicting printed figures
#    against each other is the whole point.
# ---------------------------------------------------------------------------
FIGURE = re.compile(
    r"\b\d[\d,\.]*\s*(?:tok(?:ens?)?/(?:min|s|sec)|tokens? per (?:minute|second)|"
    r"×\s*(?:faster|slower)|x\s*(?:faster|slower)|GB of communication|"
    r"(?:milli)?seconds? to (?:prove|verify))",
    re.I,
)
AUDIT_BLOCK = re.compile(r"^:::(?:audit|quote).*?^:::", re.S | re.M)
FENCE = re.compile(r"```.*?```|\{\{.*?\}\}", re.S)
# A figure inside quotation marks is ATTRIBUTED, not asserted: quoting a paper's own
# "20-60x faster than the state of the art" in order to take it apart is the opposite of
# the drift this check exists to prevent. Exempt quoted spans; keep everything else strict.
QUOTED = re.compile(r"[\"“][^\"“”\n]{0,300}[\"”]")

for f in content_files:
    body = f.read_text()
    stripped = QUOTED.sub("", AUDIT_BLOCK.sub("", FENCE.sub("", body)))
    for m in FIGURE.finditer(stripped):
        line = stripped[: m.start()].count("\n") + 1
        err(f"{f.relative_to(ROOT)}: hardcoded figure asserted in prose: {m.group(0).strip()!r}. "
            f"Numbers live in papers.yml -- use a {{{{ table: }}}} / {{{{ perf: }}}} shortcode. "
            f"If you are quoting a paper's own claim in order to dispute it, put it in quotation "
            f'marks ("...") or a :::quote / :::audit callout, which are exempt.')

# ---------------------------------------------------------------------------
# 7. provenance discipline on papers.yml
# ---------------------------------------------------------------------------
VALID_PROV = {"primary", "survey", "blog", "unknown"}
for pid, p in PAPERS.items():
    ns = p.get("numbers_source")
    if p.get("benchmarks") and not ns:
        err(f"papers.yml: '{pid}' reports benchmarks but has no numbers_source: "
            f"(primary | survey | blog | unknown). An omitted tag is indistinguishable from an "
            f"unverified one -- if you do not know, say `unknown` explicitly.")
    elif ns and ns not in VALID_PROV:
        err(f"papers.yml: '{pid}' has numbers_source: '{ns}', not one of {sorted(VALID_PROV)}")
    elif ns == "unknown":
        warn(f"papers.yml: '{pid}' carries benchmark numbers whose provenance is recorded as "
             f"`unknown` -- they are quoted on the site with a dashed marker. Re-read the paper "
             f"and promote to `primary`, or drop the numbers.")
    if "authors_verified" not in p and p.get("authors"):
        warn(f"papers.yml: '{pid}' has an author list with no authors_verified: flag")
    q = p.get("quantization")
    has_tpm = any(
        isinstance(b, dict) and b.get("tokens_per_minute") is not None
        for b in (p.get("benchmarks") or [])
    )
    if has_tpm and not (isinstance(q, dict) and "bits" in q):
        warn(f"papers.yml: '{pid}' reports a throughput figure but records no "
             f"quantization.bits -- the number is not comparable to any other system. "
             f"Record `bits: null` with a note if the paper does not state it.")

# ---------------------------------------------------------------------------
# 8. debts: PDFs we hold but have not written up; papers with no home
# ---------------------------------------------------------------------------
pdfs = {p.stem for p in REFS.rglob("*.pdf")} if REFS.exists() else set()
for stem in sorted(pdfs):
    if stem in external:
        # A building block we cite but do not study (twist-shout). Holding the PDF is useful
        # and does not oblige us to write it up -- but the filename must match the id declared
        # under external:, or this exemption silently hides a genuinely unfiled paper.
        continue
    if stem in PAPERS and stem not in covered:
        warn(f"references/: we hold {stem}.pdf but there is no content/papers/{stem}.md — "
             f"the PDF has been fetched and not read.")
    if stem not in PAPERS:
        warn(f"references/: {stem}.pdf has no papers.yml entry.")

# 9. (removed) The README used to be a full paper index, and this check warned when it fell
#    behind papers.yml. The README is now deliberately a summary — the site is the index — so
#    the check measured the wrong thing and is gone. The site's own section indexes, which ARE
#    generated from papers.yml, cannot fall behind by construction.

# ---------------------------------------------------------------------------
# 10. THE HEADLINE FINDING IS A TRIPWIRE.
#
#     This corpus's most-quoted claim is that ZERO citation edges cross between the
#     verifiability literature and the privacy literature. That claim is derived, not
#     asserted -- which means a single mis-filed paper can flip it without anyone
#     noticing. A 2PC paper dropped into a verifiability section, citing Iron, would
#     turn "two communities that never talk" into "they cite each other", and the site
#     would dutifully render the new claim as fact.
#
#     So: any crossing edge must be looked at by a human before it is believed. It is
#     either a genuine and very interesting development, or a filing error. It is never
#     a detail.
# ---------------------------------------------------------------------------
# Categories that are a cross-cutting SHELF rather than a column of the 2x2. numerics_primitives
# holds the arithmetic building blocks (float and fixed-point representation) that BOTH columns
# reach for; three of its five papers are MPC, not ZK. It is owned by the zk-inference section for
# display purposes only, and inheriting that section's `verify-infer` cell would misclassify an MPC
# paper as verifiability literature -- which is precisely the filing artifact the tripwire below
# exists to catch. (Concretely: bolt -> secfloat is an MPC paper citing an MPC paper, and must not
# be counted as the privacy literature citing the verifiability literature.)
NEUTRAL_CATS = {"numerics_primitives"}

CELL_OF_SECTION = {s["key"]: s["cell"] for s in sections.get("sections", [])}
SECTION_OF_CAT = {}
for s in sections.get("sections", []):
    for c in s.get("papers_from") or []:
        SECTION_OF_CAT[c] = s["key"]


def column(pid):
    cat = CAT_OF.get(pid, "")
    if cat in NEUTRAL_CATS:
        return ""
    sec = SECTION_OF_CAT.get(cat, "")
    cell = CELL_OF_SECTION.get(sec, "")
    if cell.startswith("verify"):
        return "verify"
    if cell.startswith("private"):
        return "private"
    return ""  # meta section, or an external building block: belongs to neither column


crossing = []
for src, dsts in (citegraph.get("citations") or {}).items():
    for d in dsts or []:
        if {column(src), column(d)} == {"verify", "private"}:
            crossing.append((src, d))

if crossing:
    warn(
        f"THE HEADLINE FINDING HAS CHANGED: {len(crossing)} citation edge(s) now cross between "
        f"the verifiability and privacy literatures — "
        + "; ".join(f"{a} -> {b}" for a, b in crossing[:5])
        + ". docs/graph/index.html will now say the two communities DO cite each other. Before "
        "you believe that: is each of these papers filed in the right section? An MPC paper "
        "misfiled into a verifiability section produces exactly this, and it is a filing "
        "artifact, not a discovery."
    )
else:
    print("headline: 0 edges cross between the verifiability and privacy literatures (unchanged)")

# ---------------------------------------------------------------------------
# 11. the social card hardcodes corpus counts into an SVG, so it can rot like any other
#     hardcoded number. The rule that governs prose governs the card: if a figure is
#     baked in, something has to check it. Otherwise the link preview advertises a
#     corpus we no longer have.
# ---------------------------------------------------------------------------
og = ROOT / "site" / "static" / "og.svg"
if og.exists():
    n_papers = len(PAPERS) + sum(
        1
        for v in papers_raw.values()
        if isinstance(v, list)
        for e in v
        if isinstance(e, dict) and "id" not in e
    )
    claimed = [int(x) for x in re.findall(r'font-size="46"[^>]*>(\d+)<', og.read_text())]
    if len(claimed) >= 2 and claimed[:2] != [n_papers, len(covered)]:
        warn(
            f"site/static/og.svg (the social card) advertises {claimed[0]} papers indexed and "
            f"{claimed[1]} read, but the corpus now holds {n_papers} and {len(covered)}. "
            f"Edit the SVG and run `make og`."
        )

# ---------------------------------------------------------------------------
# 12. no dead internal links in the built site
#     (writers type `(./quantization/)`; the build resolves those, but a typo'd slug
#      would otherwise ship as a 404 that nobody notices)
# ---------------------------------------------------------------------------
DOCS = ROOT / "docs"
if DOCS.exists():
    n_links = n_dead = 0
    for f in DOCS.rglob("*.html"):
        for href in re.findall(r'href="([^"]+)"', f.read_text()):
            if re.match(r"^(https?:|mailto:|#)", href):
                continue
            n_links += 1
            if not (f.parent / href.split("#")[0]).resolve().exists():
                n_dead += 1
                err(f"dead link: docs/{f.relative_to(DOCS)} -> {href}")
    if not n_dead:
        print(f"links: {n_links} internal, none dead")

# ---------------------------------------------------------------------------
if WARNS:
    print(f"\n\033[33m{len(WARNS)} warning(s)\033[0m")
    for w in WARNS:
        print("  ·", w)
if ERRORS:
    print(f"\n\033[31m{len(ERRORS)} error(s)\033[0m")
    for e in ERRORS:
        print("  ✗", e)
    sys.exit(1)
print(f"\n\033[32mok\033[0m — {len(PAPERS)} papers, {len(content_files)} content files, "
      f"{len(operators.get('operators') or [])} operators, {len(WARNS)} warning(s)")
