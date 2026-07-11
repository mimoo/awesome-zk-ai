#!/usr/bin/env python3
"""
zkAI SoK static site generator.

Joins the structured data (papers.yml, operators.yml, references/citation-graph.yml)
with the prose (content/**/*.md) and emits docs/.

Design rule: numbers come from YAML, prose comes from markdown, and the two meet only
here. Prose never hardcodes a figure -- it calls a shortcode and the figure is rendered
from papers.yml at build time. That is what stops the SoK drifting from its own data.

    python3 site/build.py            # build
    python3 site/build.py --serve    # build + serve on :8000

Everything under docs/ is generated. Do not hand-edit it.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

try:
    import markdown as md_lib
except ImportError:
    sys.exit("need: python3 -m pip install --user markdown")

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CONTENT = ROOT / "content"
DOCS = ROOT / "docs"
TPL = SITE / "templates"

# ---------------------------------------------------------------------------
# data loading
# ---------------------------------------------------------------------------


def load_yaml(p: Path, default=None):
    if not p.exists():
        return default
    with p.open() as f:
        return yaml.safe_load(f) or default


@dataclass
class Paper:
    id: str
    data: dict
    cat: str  # papers.yml top-level key
    section: str  # sections.yml key that owns that category

    @property
    def name(self) -> str:
        return str(self.data.get("name") or self.data.get("title") or self.id)

    @property
    def url(self) -> str:
        return f"papers/{self.id}.html"

    @property
    def year(self):
        return self.data.get("year")

    @property
    def provenance(self) -> str:
        # "" means the entry carries no numbers at all -- there is nothing to vouch for,
        # so it gets no marker. Only an entry that HAS figures and no tag is suspicious.
        tag = str(self.data.get("numbers_source") or "").strip()
        if tag:
            return tag
        return "unknown" if self.data.get("benchmarks") else ""


@dataclass
class Page:
    slug: str
    section: str
    title: str
    order: int
    lede: str
    body_md: str
    papers: list
    status: str
    src: Path
    html: str = ""
    headings: list = field(default_factory=list)

    @property
    def url(self) -> str:
        d = SECTION_DIR[self.section]
        return f"{d}/{self.slug}.html" if d else f"{self.slug}.html"


# ---------------------------------------------------------------------------
# globals populated by load()
# ---------------------------------------------------------------------------
PAPERS: dict[str, Paper] = {}
PAPERS_BY_CAT: dict[str, list] = {}
STUBS: dict[str, list] = {}  # papers.yml entries with no id: backlog, not yet read
SECTIONS: list[dict] = []
GENERATED: list[dict] = []
SECTION_DIR: dict[str, str] = {}
PAGES: list[Page] = []
PAGES_BY_SECTION: dict[str, list] = {}
SLUG_INDEX: dict[str, Page] = {}  # slug -> page, for resolving extensionless links
CITES: dict[str, list] = {}
CITED_BY: dict[str, list] = {}
EXTERNAL: dict[str, str] = {}
OPERATORS: dict = {}
PAPER_NOTES: dict[str, dict] = {}
DISCUSSED_IN: dict[str, list] = {}
WARNINGS: list[str] = []

# proof-system families, for colouring charts. An entry may set `proof_family`
# explicitly; otherwise we guess from its `proof_system` string and warn.
FAMILY = {
    "gkr": ("GKR / sum-check", "#01a9b4"),
    "halo2": ("Halo2 / arithmetic circuit", "#c58203"),
    "lookup": ("Lookup arguments (Lasso/Jolt)", "#a8c256"),
    "vole": ("VOLE-based ZK", "#9866f1"),
    "accum": ("Accumulation / folding", "#e9483c"),
    "other": ("Other", "#7d8a93"),
}
CLAIM = {
    "pass": "single forward pass",
    "token": "per token",
    "seq": "amortised over a full sequence",
    "full": "whole inference, token count unstated",
}


def guess_family(p: Paper) -> str:
    if p.data.get("proof_family"):
        return str(p.data["proof_family"])
    s = " ".join(
        str(p.data.get(k, "")) for k in ("proof_system", "commitment_scheme", "approach")
    ).lower()
    if "gkr" in s or "sum-check" in s or "sumcheck" in s:
        return "gkr"
    if "halo2" in s or "plonk" in s or "groth" in s or "r1cs" in s:
        return "halo2"
    if "lasso" in s or "jolt" in s or "lookup" in s:
        return "lookup"
    if "vole" in s or "quicksilver" in s:
        return "vole"
    if "fold" in s or "accumul" in s or "nova" in s:
        return "accum"
    return "other"


def load():
    global SECTIONS, GENERATED, OPERATORS
    cfg = load_yaml(SITE / "sections.yml", {})
    SECTIONS = cfg.get("sections", [])
    GENERATED = cfg.get("generated", [])
    for s in SECTIONS:
        SECTION_DIR[s["key"]] = s["dir"]
    for g in GENERATED:
        SECTION_DIR[g["key"]] = g["dir"]

    cat_owner = {}
    for s in SECTIONS:
        for c in s.get("papers_from") or []:
            cat_owner[c] = s["key"]

    raw = load_yaml(ROOT / "papers.yml", {})
    for cat, entries in raw.items():
        if not isinstance(entries, list):
            continue
        if cat not in cat_owner:
            WARNINGS.append(
                f"papers.yml key '{cat}' is not claimed by any section in site/sections.yml "
                f"-- its {len(entries)} papers will not appear in any section index."
            )
        PAPERS_BY_CAT[cat] = []
        for e in entries:
            if not isinstance(e, dict):
                continue
            if "id" not in e:
                # Deliberately lightweight: a backlog stub (title/date/category/note) for a
                # paper we have not read. It gets no page -- but it must still be listed,
                # or the site would quietly imply we had read everything we know about.
                STUBS.setdefault(cat, []).append(e)
                continue
            p = Paper(id=str(e["id"]), data=e, cat=cat, section=cat_owner.get(cat, ""))
            if p.id in PAPERS:
                WARNINGS.append(f"duplicate paper id '{p.id}' (in {PAPERS[p.id].cat} and {cat})")
            PAPERS[p.id] = p
            PAPERS_BY_CAT[cat].append(p)

    # citation graph
    cg = load_yaml(ROOT / "references" / "citation-graph.yml", {}) or {}
    EXTERNAL.update(cg.get("external", {}) or {})
    for src, dsts in (cg.get("citations") or {}).items():
        CITES[src] = list(dsts or [])
        for d in dsts or []:
            CITED_BY.setdefault(d, []).append(src)

    OPERATORS = load_yaml(ROOT / "operators.yml", {}) or {}

    load_content()


FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)


def parse_front(text: str, src: Path):
    m = FM_RE.match(text)
    if not m:
        WARNINGS.append(f"{src.relative_to(ROOT)}: no frontmatter -- skipped")
        return None, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def load_content():
    if not CONTENT.exists():
        return
    for f in sorted(CONTENT.rglob("*.md")):
        fm, body = parse_front(f.read_text(), f)
        if fm is None:
            continue
        rel = f.relative_to(CONTENT)
        if rel.parts[0] == "papers":
            pid = fm.get("paper") or f.stem
            if pid not in PAPERS:
                WARNINGS.append(f"{rel}: paper id '{pid}' is not in papers.yml -- skipped")
                continue
            PAPER_NOTES[pid] = {"fm": fm, "body": body, "src": f}
            continue
        sec = fm.get("section")
        if sec not in SECTION_DIR:
            WARNINGS.append(f"{rel}: section '{sec}' is not in site/sections.yml -- skipped")
            continue
        pg = Page(
            slug=fm.get("slug") or f.stem,
            section=sec,
            title=fm.get("title") or f.stem,
            order=int(fm.get("order") or 999),
            lede=fm.get("lede") or "",
            body_md=body,
            papers=list(fm.get("papers") or []),
            status=fm.get("status") or "draft",
            src=f,
        )
        for pid in pg.papers:
            if pid not in PAPERS:
                WARNINGS.append(f"{rel}: frontmatter papers: unknown id '{pid}'")
            else:
                DISCUSSED_IN.setdefault(pid, []).append(pg)
        PAGES.append(pg)
        PAGES_BY_SECTION.setdefault(sec, []).append(pg)
    for k in PAGES_BY_SECTION:
        PAGES_BY_SECTION[k].sort(key=lambda p: (p.order, p.title))
    for pg in PAGES:
        SLUG_INDEX.setdefault(pg.slug, pg)


# ---------------------------------------------------------------------------
# formatting helpers
# ---------------------------------------------------------------------------
E = html.escape


def fmt_params(n):
    if n is None:
        return "—"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            v = n / div
            return f"{v:.0f}{suf}" if v == int(v) else f"{v:.1f}{suf}"
    return f"{n:.0f}"


def fmt_num(v):
    if v is None:
        return '<span class="na">—</span>'
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, list):
        vals = [fmt_num(x) for x in v]
        return "–".join(vals) if len(v) == 2 and all(isinstance(x, (int, float)) for x in v) else ", ".join(vals)
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return f"{v:g}"
    return E(str(v))


def prov_dot(kind: str) -> str:
    k = (kind or "").lower()
    if not k:
        return ""  # no numbers recorded -> nothing to vouch for -> no marker
    cls = k if k in ("primary", "survey", "blog") else "blog"
    label = {
        "primary": "read in the paper",
        "survey": "secondhand, from a survey",
        "blog": "vendor / blog claim",
        "unknown": "provenance not recorded — treat with suspicion",
    }.get(k, "provenance not recorded — treat with suspicion")
    return f'<span class="prov {cls}" title="{E(str(label))}"></span>'


PROV_KEY = (
    '<div class="prov-key">'
    '<span><i class="prov primary"></i> primary — read in the paper</span>'
    '<span><i class="prov survey"></i> survey — secondhand</span>'
    '<span><i class="prov blog"></i> vendor claim, or provenance unrecorded</span>'
    "</div>"
)


def rel(from_url: str, to_url: str) -> str:
    """Relative link between two site-root-relative urls."""
    depth = from_url.count("/")
    return "../" * depth + to_url


# ---------------------------------------------------------------------------
# markdown pipeline
#   1. pull math + shortcodes out into tokens so markdown can't mangle them
#   2. expand ::: callouts (recursively rendering their bodies)
#   3. expand [[paper]] links
#   4. run markdown
#   5. put math + shortcodes back
# ---------------------------------------------------------------------------
CALLOUT_RE = re.compile(
    r"^:::(?P<kind>gap|debate|audit|quote|note)(?P<attrs>\{[^}\n]*\})?[ \t]*(?P<title>[^\n]*)\n"
    r"(?P<body>.*?)\n:::[ \t]*$",
    re.S | re.M,
)
ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
SHORTCODE_RE = re.compile(r"\{\{\s*([a-z_]+)\s*:?\s*([^}]*?)\s*\}\}")
WIKILINK_RE = re.compile(r"\[\[([a-z0-9\-\.]+)\]\]", re.I)
FENCE_RE = re.compile(r"```.*?```", re.S)
MATH_RE = re.compile(r"(\$\$.+?\$\$|\$[^$\n]+?\$)", re.S)


class Ctx:
    """Per-page render context: where we are, so links can be relative."""

    def __init__(self, url: str):
        self.url = url
        self.math: list[str] = []
        self.codes: list[str] = []

    def link(self, to: str) -> str:
        return rel(self.url, to)


def protect_math(text: str, ctx: Ctx) -> str:
    out, last = [], 0
    for fence in FENCE_RE.finditer(text):
        out.append(_protect_math_span(text[last:fence.start()], ctx))
        out.append(fence.group(0))
        last = fence.end()
    out.append(_protect_math_span(text[last:], ctx))
    return "".join(out)


def _protect_math_span(s: str, ctx: Ctx) -> str:
    def sub(m):
        ctx.math.append(m.group(1))
        return f"MATHTOKEN{len(ctx.math)-1}ZZ"

    return MATH_RE.sub(sub, s)


def expand_wikilinks(text: str, ctx: Ctx) -> str:
    def sub(m):
        pid = m.group(1)
        p = PAPERS.get(pid)
        if not p:
            WARNINGS.append(f"{ctx.url}: [[{pid}]] is not a paper id in papers.yml")
            return f'<span class="na" title="unknown paper id">{E(pid)}</span>'
        return f'<a href="{ctx.link(p.url)}">{E(p.name)}</a>'

    return WIKILINK_RE.sub(sub, text)


def expand_callouts(text: str, ctx: Ctx) -> str:
    def sub(m):
        kind = m.group("kind")
        title = (m.group("title") or "").strip()
        attrs = dict(ATTR_RE.findall(m.group("attrs") or ""))
        body = render_md(m.group("body"), ctx, inner=True)
        if kind == "gap":
            return (
                '<div class="gap"><span class="gm">gap</span><div class="gap-body">'
                + (f"<h5>{E(title)}</h5>" if title else "")
                + body
                + "</div></div>"
            )
        if kind == "debate":
            return f'<div class="debate"><h4>{E(title or "Debate")}</h4>{body}</div>'
        if kind == "audit":
            return f'<div class="audit"><span class="audit-h">{E(title or "Audit surface")}</span>{body}</div>'
        if kind == "quote":
            src = attrs.get("src", "")
            sec = attrs.get("sec", "")
            cite = f"<cite><b>{E(src)}</b>" + (f" · {E(sec)}" if sec else "") + "</cite>" if src else ""
            return f'<blockquote class="q">{body}{cite}</blockquote>'
        return f'<div class="audit">{body}</div>'

    return CALLOUT_RE.sub(sub, text)


def stash_shortcodes(text: str, ctx: Ctx) -> str:
    def sub(m):
        name, arg = m.group(1), m.group(2)
        try:
            out = render_shortcode(name, arg, ctx)
        except Exception as exc:  # a bad shortcode must not kill the build silently
            WARNINGS.append(f"{ctx.url}: shortcode {{{{ {name}:{arg} }}}} failed: {exc}")
            out = f'<div class="banner stub">shortcode {E(name)} failed: {E(str(exc))}</div>'
        ctx.codes.append(out)
        return f"SHORTCODETOKEN{len(ctx.codes)-1}ZZ"

    return SHORTCODE_RE.sub(sub, text)


MD = md_lib.Markdown(
    extensions=["tables", "fenced_code", "attr_list", "footnotes", "sane_lists", "md_in_html"],
    output_format="html5",
)


def render_md(text: str, ctx: Ctx, inner: bool = False) -> str:
    if not inner:
        text = protect_math(text, ctx)
        text = expand_callouts(text, ctx)
        text = stash_shortcodes(text, ctx)
    text = expand_wikilinks(text, ctx)
    MD.reset()
    out = MD.convert(text)
    if inner:
        return out
    # unwrap block shortcodes that markdown wrapped in <p>
    out = fix_links(out, ctx)
    out = re.sub(r"<p>\s*(SHORTCODETOKEN\d+ZZ)\s*</p>", r"\1", out)
    out = re.sub(r"SHORTCODETOKEN(\d+)ZZ", lambda m: ctx.codes[int(m.group(1))], out)
    out = re.sub(r"MATHTOKEN(\d+)ZZ", lambda m: ctx.math[int(m.group(1))], out)
    return out


HREF_RE = re.compile(r'href="([^"]+)"')


def fix_links(html_str: str, ctx: Ctx) -> str:
    """Resolve extensionless relative links written in markdown.

    Writers naturally type `[Quantization](./quantization/)` or `(../private-inference/)`.
    The site emits flat `.html` files (so it works over file:// as well as a web server),
    so those links would 404. Rather than make every author remember the convention, we
    resolve them here: a bare slug becomes the page with that slug, a bare section name
    becomes that section's index. Anything we cannot resolve is a build warning, not a
    silent dead link.
    """

    def sub(m):
        href = m.group(1)
        # Root-absolute links ("/soundness/") are resolved too, not skipped: they would
        # break on any host that is not the domain root (GitHub Pages project sites) and
        # over file:// entirely.
        if re.match(r"^(https?:|mailto:|#|\.\./vendor)", href) or href.endswith(".html"):
            return m.group(0)
        frag = ""
        if "#" in href:
            href, frag = href.split("#", 1)
            frag = "#" + frag
        if "." in href.rsplit("/", 1)[-1] and not href.rstrip("/").endswith((".", "..")):
            return m.group(0)  # some other extension -- leave alone
        target = href.rstrip("/").rsplit("/", 1)[-1]
        if not target or target in (".", ".."):
            # bare "./" or "../": the writer means "this section" / "one level up"
            here = ctx.url.rsplit("/", 1)[0] if "/" in ctx.url else ""
            dest = f"{here}/index.html" if (here and target == ".") else "index.html"
            return f'href="{ctx.link(dest)}{frag}"'
        for key, d in SECTION_DIR.items():
            if d == target:
                return f'href="{ctx.link(d + "/index.html")}{frag}"'
        pg = SLUG_INDEX.get(target)
        if pg:
            return f'href="{ctx.link(pg.url)}{frag}"'
        if target in PAPERS:
            return f'href="{ctx.link(PAPERS[target].url)}{frag}"'
        WARNINGS.append(f"{ctx.url}: link '{m.group(1)}' does not resolve to a page or paper")
        return m.group(0)

    return HREF_RE.sub(sub, html_str)


def headings_of(html_str: str):
    out = []
    for m in re.finditer(r"<h([23])>(.*?)</h\1>", html_str, re.S):
        lvl, txt = int(m.group(1)), re.sub(r"<[^>]+>", "", m.group(2))
        out.append((lvl, txt, re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")))
    return out


def add_heading_ids(html_str: str) -> str:
    def sub(m):
        lvl, txt = m.group(1), m.group(2)
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", txt).lower()).strip("-")
        return f'<h{lvl} id="{slug}">{txt}</h{lvl}>'

    return re.sub(r"<h([23])>(.*?)</h\1>", sub, html_str, flags=re.S)


# ---------------------------------------------------------------------------
# shortcodes
# ---------------------------------------------------------------------------
def render_shortcode(name: str, arg: str, ctx: Ctx) -> str:
    parts = arg.split()
    key = parts[0] if parts else ""
    opts = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
    if name == "table":
        return sc_table(key, opts, ctx)
    if name == "papers":
        return sc_papers(key, ctx)
    if name == "perf":
        return sc_perf(key, ctx)
    if name == "chart":
        return {
            "throughput": sc_chart_throughput,
            "timeline": sc_chart_timeline,
            "citations": sc_chart_citations,
        }[key](ctx)
    if name == "coverage":
        return sc_coverage(ctx)
    raise KeyError(f"unknown shortcode '{name}'")


def bench_rows(cat: str):
    """Flatten (paper, benchmark) pairs for a papers.yml category."""
    for p in PAPERS_BY_CAT.get(cat, []):
        bs = p.data.get("benchmarks") or []
        if not bs:
            yield p, {}
        for b in bs:
            if isinstance(b, dict):
                yield p, b


DEFAULT_COLS = [
    ("model", "Model"),
    ("params", "Params"),
    ("context_window", "Context"),
    ("tokens_per_minute", "Tok/min"),
    ("proving_time_s", "Prove (s)"),
    ("proof_size_mb", "Proof (MB)"),
    ("verification_time_s", "Verify (s)"),
    ("communication_mb", "Comm (MB)"),
    ("accuracy", "Accuracy"),
]


def cell(b: dict, p: Paper, k: str) -> str:
    v = b.get(k, None)
    if k == "params":
        return fmt_params(v)
    if k == "model" and v is None:
        v = b.get("models") or p.data.get("model")
    if v is None:
        v = p.data.get(k)
    if v is None:
        return '<span class="na">—</span>'
    return fmt_num(v)


def sc_table(cat: str, opts: dict, ctx: Ctx) -> str:
    if cat not in PAPERS_BY_CAT:
        raise KeyError(f"no such papers.yml key '{cat}'")
    rows = list(bench_rows(cat))
    if "cols" in opts:
        cols = [(c, c.split(".")[-1].replace("_", " ").title()) for c in opts["cols"].split(",")]
    else:
        present = {k for _, b in rows for k, v in b.items() if v is not None}
        cols = [(k, lbl) for k, lbl in DEFAULT_COLS if k in present or k == "model"]
    head = "".join(f"<th>{E(l)}</th>" for _, l in cols)
    body = []
    for p, b in rows:
        tds = "".join(f"<td>{cell(b, p, k)}</td>" for k, _ in cols)
        body.append(
            f'<tr><th><a href="{ctx.link(p.url)}">{E(p.name)}</a> {prov_dot(p.provenance)}</th>{tds}</tr>'
        )
    return (
        '<div class="scrollx"><table class="matrix"><thead><tr><th>System</th>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
        + PROV_KEY
    )


def sc_papers(cat: str, ctx: Ctx) -> str:
    ps = PAPERS_BY_CAT.get(cat)
    if ps is None:
        raise KeyError(f"no such papers.yml key '{cat}'")
    cards = []
    for p in ps:
        d = p.data
        blurb = str(d.get("approach") or d.get("notes") or d.get("title") or "")
        blurb = blurb.strip().replace("\n", " ")
        if len(blurb) > 190:
            blurb = blurb[:187].rsplit(" ", 1)[0] + "…"
        venue = d.get("venue") or d.get("year") or ""
        cards.append(
            f'<div class="card meta"><div class="kicker">{E(str(venue))}</div>'
            f'<h4><a href="{ctx.link(p.url)}">{E(p.name)}</a></h4>'
            f"<p>{E(blurb)}</p>"
            f'<div class="foot">{E(p.provenance)} {prov_dot(p.provenance)}</div></div>'
        )
    return '<div class="cards">' + "".join(cards) + "</div>"


def headline(p: Paper):
    """The one number that characterises a system, with its unit."""
    for b in p.data.get("benchmarks") or []:
        if not isinstance(b, dict):
            continue
        if b.get("tokens_per_minute") is not None:
            return f"{fmt_num(b['tokens_per_minute'])} tok/min", b.get("model")
        if b.get("proving_time_s") is not None:
            return f"{fmt_num(b['proving_time_s'])} s to prove", b.get("model") or b.get("models")
    return None, None


def sc_perf(pid: str, ctx: Ctx) -> str:
    p = PAPERS.get(pid)
    if not p:
        raise KeyError(f"no such paper '{pid}'")
    val, model = headline(p)
    if not val:
        return f'<span class="perf na" title="papers.yml reports no benchmark">{E(p.name)}: not reported</span>'
    m = f" ({E(str(model))})" if model else ""
    return (
        f'<a class="perf" href="{ctx.link(p.url)}">{E(p.name)}: {val}{m}</a>{prov_dot(p.provenance)}'
    )


# --- charts (server-rendered SVG; no JS needed to read them) ---------------
import math


def sc_chart_throughput(ctx: Ctx) -> str:
    pts = []
    for p in PAPERS_BY_CAT.get("inference", []):
        fam = guess_family(p)
        for b in p.data.get("benchmarks") or []:
            if not isinstance(b, dict):
                continue
            n, t = b.get("params"), b.get("tokens_per_minute")
            if not n or not t:
                continue
            label = str(b.get("model") or p.name)
            pts.append(
                dict(
                    id=p.id, name=p.name, model=label, n=float(n), t=float(t), fam=fam,
                    kind=b.get("claim_kind") or p.data.get("claim_kind") or "",
                    prov=p.provenance, url=p.url,
                )
            )
    if not pts:
        return '<div class="banner stub">no throughput data in papers.yml yet</div>'

    W, H = 820, 430
    L, R, T, B = 58, 24, 22, 46
    xs = [math.log10(p["n"]) for p in pts]
    ys = [math.log10(p["t"]) for p in pts]
    x0, x1 = min(xs) - 0.25, max(xs) + 0.25
    y0, y1 = min(ys) - 0.35, max(ys) + 0.35
    sx = lambda v: L + (math.log10(v) - x0) / (x1 - x0) * (W - L - R)
    sy = lambda v: H - B - (math.log10(v) - y0) / (y1 - y0) * (H - T - B)

    g = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Proving throughput versus model size">']
    g.append('<g class="grid">')
    for d in range(int(math.floor(y0)), int(math.ceil(y1)) + 1):
        v = 10 ** d
        if y0 <= d <= y1:
            g.append(f'<line x1="{L}" x2="{W-R}" y1="{sy(v):.1f}" y2="{sy(v):.1f}"/>')
    g.append("</g>")
    g.append('<g class="axis">')
    for d in range(int(math.floor(y0)), int(math.ceil(y1)) + 1):
        v = 10 ** d
        if y0 <= d <= y1:
            lbl = f"{v:g}" if v >= 1 else f"{v:g}"
            g.append(f'<text x="{L-9}" y="{sy(v)+3.5:.1f}" text-anchor="end">{lbl}</text>')
    for v, lbl in ((1e8, "100M"), (1e9, "1B"), (1e10, "10B")):
        if x0 <= math.log10(v) <= x1:
            g.append(f'<text x="{sx(v):.1f}" y="{H-B+20}" text-anchor="middle">{lbl}</text>')
    g.append(f'<text x="{L}" y="{H-8}" fill="#6f7d86">model parameters →</text>')
    g.append(
        f'<text x="{L-9}" y="{T+2}" text-anchor="end" fill="#6f7d86">tok/min</text>'
    )
    g.append("</g>")
    # Marker radius encodes the STRENGTH of the claim, because that is the thing the
    # y-axis silently hides: a big dot proved a whole sequence, a small one proved a
    # single pass, and a dashed one did not say what it proved.
    RADIUS = {"seq": 8.5, "token": 6.0, "pass": 4.5, "full": 6.0, "": 6.0}
    for p in sorted(pts, key=lambda d: -d["n"]):
        col = FAMILY[p["fam"]][1]
        fill = col if p["prov"] == "primary" else "none"
        kind = p["kind"]
        r = RADIUS.get(kind, 6.0)
        # an unstated claim is drawn as an unstated claim
        dash = ' stroke-dasharray="3 2"' if kind in ("full", "") else ""
        cx, cy = sx(p["n"]), sy(p["t"])
        claim = CLAIM.get(kind, "claim NOT stated by the paper")
        tip = f'{p["name"]} · {p["model"]} · {p["t"]:g} tok/min · {claim} · {p["prov"]}'
        lbl = p["model"] if p["model"] != p["name"] else p["name"]
        g.append(
            f'<g class="pt"><a href="{ctx.link(p["url"])}">'
            f"<title>{E(tip)}</title>"
            f'<circle class="dot" cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{col}"{dash}/>'
            f'<text class="dlabel" x="{cx + r + 5:.1f}" y="{cy+4:.1f}">{E(lbl)}</text>'
            "</a></g>"
        )
    g.append("</svg>")
    fams = sorted({p["fam"] for p in pts})
    legend = "".join(
        f'<span><i style="background:{FAMILY[f][1]}"></i>{E(FAMILY[f][0])}</span>' for f in fams
    )
    legend += (
        '<span><i class="ring"></i>hollow = secondhand number</span>'
        '<span><i style="background:#7d8a93;width:15px;height:15px"></i>large = whole sequence proved</span>'
        '<span><i style="background:#7d8a93;width:8px;height:8px"></i>small = one forward pass</span>'
        '<span><i class="ring" style="border-style:dashed"></i>dashed = claim not stated</span>'
    )
    return (
        '<div class="viz">' + "".join(g) + f'<div class="legend">{legend}</div></div>'
        '<p style="font-size:13px;color:#6f7d86;margin-top:10px">Both axes log. A point is one '
        "reported benchmark, not one system — and <strong>the points are not making the same "
        "claim</strong>. Marker size is the strength of the claim: a large dot certified a whole "
        "generated sequence, a small one proved a single forward pass, and a dashed one did not "
        "say. Reading this chart as a leaderboard is the mistake it is drawn to prevent.</p>"
    )


def sc_chart_timeline(ctx: Ctx) -> str:
    pts = []
    for p in PAPERS_BY_CAT.get("inference", []):
        d = p.data.get("date")
        if not d:
            continue
        for b in p.data.get("benchmarks") or []:
            if not isinstance(b, dict):
                continue
            n = b.get("params")
            if not n or float(n) > 2e8:  # GPT-2 class only, so we compare like with like
                continue
            secs = b.get("proving_time_s")
            if secs is None and b.get("tokens_per_minute"):
                secs = 60.0 / float(b["tokens_per_minute"])
            if not secs:
                continue
            pts.append(
                dict(id=p.id, name=p.name, date=str(d), s=float(secs), fam=guess_family(p),
                     prov=p.provenance, url=p.url, model=b.get("model") or "")
            )
    if len(pts) < 2:
        return '<div class="banner stub">not enough dated GPT-2-class data points yet</div>'

    def ord_(ds):
        y, m, dd = (list(map(int, ds.split("-"))) + [1, 1])[:3]
        return y + (m - 1) / 12 + dd / 365

    W, H = 820, 380
    L, R, T, B = 62, 24, 22, 44
    xs = [ord_(p["date"]) for p in pts]
    x0, x1 = min(xs) - 0.15, max(xs) + 0.35
    ys = [math.log10(p["s"]) for p in pts]
    y0, y1 = min(ys) - 0.4, max(ys) + 0.4
    sx = lambda v: L + (v - x0) / (x1 - x0) * (W - L - R)
    sy = lambda v: H - B - (math.log10(v) - y0) / (y1 - y0) * (H - T - B)

    g = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Proving time for GPT-2 over time">']
    g.append('<g class="grid">')
    for d in range(int(math.floor(y0)), int(math.ceil(y1)) + 1):
        g.append(f'<line x1="{L}" x2="{W-R}" y1="{sy(10**d):.1f}" y2="{sy(10**d):.1f}"/>')
    g.append("</g><g class=\"axis\">")
    for d in range(int(math.floor(y0)), int(math.ceil(y1)) + 1):
        v = 10 ** d
        lbl = f"{v:g}s" if v >= 1 else f"{v:g}s"
        g.append(f'<text x="{L-9}" y="{sy(v)+3.5:.1f}" text-anchor="end">{lbl}</text>')
    for yr in range(int(x0), int(x1) + 1):
        if x0 <= yr <= x1:
            g.append(f'<text x="{sx(yr):.1f}" y="{H-B+20}" text-anchor="middle">{yr}</text>')
    g.append(f'<text x="{L-9}" y="{T+2}" text-anchor="end" fill="#6f7d86">sec / token</text>')
    g.append("</g>")
    for p in sorted(pts, key=lambda d: -d["s"]):
        col = FAMILY[p["fam"]][1]
        fill = col if p["prov"] == "primary" else "none"
        cx, cy = sx(ord_(p["date"])), sy(p["s"])
        tip = "{} · {:g} s/token · {} · {}".format(p["name"], p["s"], p["date"], p["prov"])
        href = ctx.link(p["url"])
        g.append(
            f'<g class="pt"><a href="{href}">'
            f"<title>{E(tip)}</title>"
            f'<circle class="dot" cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{fill}" stroke="{col}"/>'
            f'<text class="dlabel" x="{cx+11:.1f}" y="{cy+4:.1f}">{E(p["name"])}</text></a></g>'
        )
    g.append("</svg>")
    return (
        '<div class="viz">' + "".join(g) + "</div>"
        '<p style="font-size:13px;color:#6f7d86;margin-top:10px">GPT-2-class models only, so the '
        "curve is not confounded by model size. Log y-axis: each gridline is 10×. Points derived "
        "from <code>proving_time_s</code>, or from <code>60 / tokens_per_minute</code> where the "
        "paper reports only throughput.</p>"
    )


# Cross-cutting shelves, not columns. `numerics_primitives` holds the arithmetic building blocks
# both columns reach for, and three of its five papers are MPC rather than ZK. It is displayed
# under zk-inference, but inheriting that section's verify-infer cell would count an MPC paper as
# verifiability literature and fabricate a crossing edge. Kept in sync with validate.py.
NEUTRAL_CATS = {"numerics_primitives"}


def cell_of(pid: str) -> str:
    """'verify' | 'private' | 'meta' | '' -- which column of the 2x2 a node sits in."""
    p = PAPERS.get(pid)
    if not p:
        return ""  # external building block: belongs to neither literature
    if p.cat in NEUTRAL_CATS:
        return "meta"
    sec = next((s for s in SECTIONS if s["key"] == p.section), None)
    if not sec:
        return ""
    c = sec["cell"]
    return "verify" if c.startswith("verify") else "private" if c.startswith("private") else "meta"


def bridge_nodes():
    """Papers cited BY BOTH columns.

    The two systems literatures have no direct edges between them. But that is not the same
    as having nothing in common: if a paper is cited by a verifiability paper AND by a
    privacy paper, it is a shared foundation the two communities reach for without reaching
    for each other. Those nodes are the actual contact surface, and they are more interesting
    than the absence of a direct edge.
    """
    out = []
    for n in sorted({d for ds in CITES.values() for d in ds}):
        citers = {a for a, ds in CITES.items() if n in ds}
        cols = {cell_of(a) for a in citers}
        if "verify" in cols and "private" in cols:
            out.append((n, sorted(citers)))
    return out


def crossing_edges():
    """Edges between the VERIFIABILITY literature and the PRIVACY literature.

    Not 'edges between any two sections' -- a survey citing zkGPT crosses a section
    boundary but says nothing about the two columns talking to each other. The claim
    this SoK actually makes is about the two columns, so that is what we count.
    """
    out = []
    for a, ds in CITES.items():
        ca = cell_of(a)
        for b in ds:
            cb = cell_of(b)
            if {ca, cb} == {"verify", "private"}:
                out.append((a, b))
    return out


def sc_chart_citations(ctx: Ctx) -> str:
    """The citation graph, inline. Its point is what is NOT there: the two columns of the
    2x2 have no edges between them."""
    if not CITES:
        return '<div class="banner stub">references/citation-graph.yml is empty</div>'
    svg = render_dot(build_dot())
    crossing = len(crossing_edges())
    n_edges = sum(len(v) for v in CITES.values())
    caption = (
        f'<p style="font-size:13px;color:#6f7d86;margin-top:10px">{n_edges} edges across the corpus. '
        f"<b>{crossing}</b> of them join the verifiability literature to the privacy literature. "
        f'Full graph: <a href="{ctx.link("graph/index.html")}">the citation graph</a>.</p>'
    )
    if not svg:
        return f'<div class="banner stub">graphviz not available at build time</div>{caption}'
    return f'<div class="graphwrap">{svg}</div>{caption}'


def sc_coverage(ctx: Ctx) -> str:
    ops = OPERATORS.get("operators") or []
    if not ops:
        return '<div class="banner stub">operators.yml not present yet — the coverage matrix will appear once it is.</div>'
    schemes = []
    for o in ops:
        for s in (o.get("schemes") or {}):
            if s not in schemes:
                schemes.append(s)
    head = "".join(
        f'<th><a href="{ctx.link(PAPERS[s].url)}">{E(PAPERS[s].name)}</a></th>'
        if s in PAPERS else f"<th>{E(s)}</th>"
        for s in schemes
    )
    rows = []
    for o in ops:
        cells = "".join(
            f'<td class="y">●</td>' if (o.get("schemes") or {}).get(s) else '<td class="n">○</td>'
            for s in schemes
        )
        oid = o.get("id")
        rows.append(
            f'<tr><th><a href="{ctx.link(f"zk-inference/operators/{oid}.html")}">{E(o.get("name",""))}</a>'
            f'<small>{E(str(o.get("group","")))}</small></th>{cells}</tr>'
        )
    return (
        '<div class="scrollx"><table class="cov"><thead><tr><th>Operator</th>'
        + head
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
        '<p style="font-size:13px;color:#6f7d86;margin-top:10px">● = the paper describes a protocol '
        "for this operator. ○ = it does not. An empty column is not a criticism — most systems are "
        "explicit about their scope — but an empty <em>row</em> is a gap in the field.</p>"
    )


# ---------------------------------------------------------------------------
# shell / nav
# ---------------------------------------------------------------------------
SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,300&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}vendor/katex/katex.min.css">
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<button class="burger" id="burger" aria-label="Toggle menu">☰</button>
<div class="shell">
  <aside class="sidebar" id="sidebar">
    <div class="brand">
      <a class="mark" href="{root}index.html" style="color:inherit"><i></i><span>zkSecurity Research</span></a>
      <h1><a href="{root}index.html" style="color:inherit">zk<em>AI</em></a></h1>
    </div>
    <div class="filter">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      <input id="filter" type="text" placeholder="filter pages…" autocomplete="off">
    </div>
    <nav id="nav">{nav}</nav>
  </aside>
  <main><div class="page">{body}</div></main>
</div>
<script src="{root}vendor/katex/katex.min.js"></script>
<script src="{root}vendor/katex/contrib/auto-render.min.js"></script>
<script>
renderMathInElement(document.body,{{delimiters:[
  {{left:"$$",right:"$$",display:true}},
  {{left:"$",right:"$",display:false}},
  {{left:"\\\\[",right:"\\\\]",display:true}},
  {{left:"\\\\(",right:"\\\\)",display:false}}],throwOnError:false}});
document.getElementById('burger').onclick=()=>document.getElementById('sidebar').classList.toggle('open');
const f=document.getElementById('filter');
f.oninput=()=>{{
  const q=f.value.toLowerCase().trim();
  document.querySelectorAll('#nav a.nav').forEach(a=>{{
    a.classList.toggle('nav-hidden', !!q && !a.textContent.toLowerCase().includes(q));
  }});
  document.querySelectorAll('#nav .navgroup').forEach(g=>{{
    let n=g.nextElementSibling, any=false;
    while(n && !n.classList.contains('navgroup')){{
      if(n.classList.contains('nav') && !n.classList.contains('nav-hidden')) any=true;
      n=n.nextElementSibling;
    }}
    g.classList.toggle('nav-hidden', !!q && !any);
  }});
}};
const t=document.getElementById('ptable-filter');
if(t){{t.oninput=()=>{{
  const q=t.value.toLowerCase().trim(); let n=0;
  document.querySelectorAll('#ptable tbody tr').forEach(r=>{{
    const hit=!q||r.textContent.toLowerCase().includes(q);
    r.classList.toggle('filtered',!hit); if(hit)n++;
  }});
  document.getElementById('ptable-count').textContent=n+' shown';
}};}}
</script>
</body>
</html>
"""


def build_nav(cur_url: str) -> str:
    out = []
    for s in SECTIONS:
        pages = PAGES_BY_SECTION.get(s["key"], [])
        d = s["dir"]
        idx_url = f"{d}/index.html" if d else "index.html"
        out.append(f'<div class="navgroup">{E(s["title"])}</div>')
        # every section has a landing page -- either its index.md or one we generate --
        # so it always gets a link. A section group with no link is a dead end in the nav.
        cls = "nav sec" + (" on" if cur_url == idx_url else "")
        n = len(sum((PAPERS_BY_CAT.get(c, []) for c in (s.get("papers_from") or [])), []))
        n += len(sum((STUBS.get(c, []) for c in (s.get("papers_from") or [])), []))
        cnt = f'<span class="cnt">{n}</span>' if n else ""
        label = "The map" if not d else "Overview"
        out.append(f'<a class="{cls}" href="{rel(cur_url, idx_url)}">{label}{cnt}</a>')
        for p in pages:
            if p.slug == "index" and d:
                continue
            cls = "nav" + (" sub" if d else "") + (" on" if cur_url == p.url else "")
            miss = '<span class="miss">draft</span>' if p.status == "draft" else ""
            out.append(f'<a class="{cls}" href="{rel(cur_url, p.url)}">{E(p.title)}{miss}</a>')
    out.append('<div class="navgroup">Index</div>')
    for g in GENERATED:
        u = f'{g["dir"]}/index.html'
        cls = "nav sec" + (" on" if cur_url == u else "")
        cnt = f'<span class="cnt">{len(PAPERS)}</span>' if g["key"] == "papers" else ""
        out.append(f'<a class="{cls}" href="{rel(cur_url, u)}">{E(g["title"])}{cnt}</a>')
    return "".join(out)


WRITTEN: list[str] = []


def emit(url: str, title: str, desc: str, body: str):
    p = DOCS / url
    p.parent.mkdir(parents=True, exist_ok=True)
    root = "../" * url.count("/")
    p.write_text(
        SHELL.format(title=E(title), desc=E(desc[:200]), root=root, nav=build_nav(url), body=body)
    )
    WRITTEN.append(url)


def crumb(*bits) -> str:
    return '<div class="crumb">' + " · ".join(bits) + "</div>"


def pager(cur: Page) -> str:
    """Prev/next across the whole site, in reading order."""
    flat = []
    for s in SECTIONS:
        flat.extend(PAGES_BY_SECTION.get(s["key"], []))
    try:
        i = flat.index(cur)
    except ValueError:
        return ""
    out = ['<div class="pager">']
    if i > 0:
        p = flat[i - 1]
        out.append(f'<a href="{rel(cur.url, p.url)}">← previous<span>{E(p.title)}</span></a>')
    if i + 1 < len(flat):
        p = flat[i + 1]
        out.append(f'<a class="next" href="{rel(cur.url, p.url)}">next →<span>{E(p.title)}</span></a>')
    out.append("</div>")
    return "".join(out)


# ---------------------------------------------------------------------------
# page emitters
# ---------------------------------------------------------------------------
def render_page(pg: Page):
    ctx = Ctx(pg.url)
    body_html = add_heading_ids(render_md(pg.body_md, ctx))
    sec = next(s for s in SECTIONS if s["key"] == pg.section)
    hs = headings_of(body_html)
    toc = ""
    if len(hs) > 2:
        toc = (
            '<div class="toc"><div>On this page</div>'
            + "".join(
                f'<a class="h{l}" href="#{sl}">{E(t)}</a>' for l, t, sl in hs
            )
            + "</div>"
        )
    rail = ""
    if pg.papers:
        links = "".join(
            f'<a href="{ctx.link(PAPERS[i].url)}">{E(PAPERS[i].name)}</a>'
            for i in pg.papers if i in PAPERS
        )
        rail = f'<div class="rail">{links}</div>'
    banner = '<div class="banner">Draft — not yet reviewed against the primary sources.</div>' if pg.status == "draft" else ""
    head = (
        crumb(f'<a href="{ctx.link((sec["dir"] + "/index.html") if sec["dir"] else "index.html")}">{E(sec["title"])}</a>', f"<b>{E(pg.title)}</b>")
        + f'<h2 class="ptitle">{E(pg.title)}</h2>'
        + (f'<p class="lede">{E(pg.lede)}</p>' if pg.lede else "")
        + rail
    )
    emit(pg.url, f"{pg.title} — zkAI", pg.lede or sec["blurb"], banner + head + toc + f'<div class="prose">{body_html}</div>' + pager(pg))


def render_section_index(s: dict):
    if not s["dir"]:
        return
    url = f'{s["dir"]}/index.html'
    ctx = Ctx(url)
    pages = [p for p in PAGES_BY_SECTION.get(s["key"], []) if p.slug != "index"]
    idx_page = next((p for p in PAGES_BY_SECTION.get(s["key"], []) if p.slug == "index"), None)
    if idx_page:  # an index.md exists -> it *is* the section landing page
        idx_page.slug = "index"
        render_page(idx_page)
        return
    cards = "".join(
        f'<div class="card {s["cell"]}"><div class="kicker">{i+1:02d}</div>'
        f'<h4><a href="{ctx.link(p.url)}">{E(p.title)}</a></h4><p>{E(p.lede)}</p></div>'
        for i, p in enumerate(pages)
    )
    # backlog stubs: entries with no id, i.e. known-of but not read
    stubs = sum((STUBS.get(c, []) for c in (s.get("papers_from") or [])), [])
    stub_tbl = ""
    if stubs:
        rows = ""
        for e in sorted(stubs, key=lambda x: str(x.get("date") or ""), reverse=True):
            t = str(e.get("title") or "—")
            u = e.get("url")
            name = f'<a href="{E(str(u))}">{E(t)}</a>' if u else E(t)
            rows += (
                f"<tr><th>{name}</th><td>{E(str(e.get('date') or '—'))}</td>"
                f"<td>{E(str(e.get('category') or '—'))}</td>"
                f"<td>{E(str(e.get('note') or ''))}</td></tr>"
            )
        stub_tbl = (
            '<h3 class="head">Known of, not read</h3>'
            '<p style="font-size:14px;color:#a8a89f;font-weight:300;max-width:72ch">These have no '
            "entry in the corpus proper — no benchmark numbers, no provenance, no page. They are "
            "listed so that the size of what we have <em>not</em> done stays visible.</p>"
            '<div class="scrollx"><table class="matrix"><thead><tr><th>Paper</th><th>Date</th>'
            "<th>Category</th><th>Note</th></tr></thead><tbody>" + rows + "</tbody></table></div>"
        )

    papers = sum((PAPERS_BY_CAT.get(c, []) for c in (s.get("papers_from") or [])), [])
    tbl = ""
    if papers:
        rows = "".join(
            f'<tr><th><a href="{ctx.link(p.url)}">{E(p.name)}</a> {prov_dot(p.provenance)}</th>'
            f'<td>{E(str(p.data.get("venue") or p.year or ""))}</td>'
            f'<td>{E(str(p.data.get("proof_system") or p.data.get("security_model") or "—"))}</td></tr>'
            for p in sorted(papers, key=lambda x: -(x.year or 0))
        )
        tbl = (
            '<h3 class="head">Papers in this section</h3><div class="scrollx"><table class="matrix">'
            "<thead><tr><th>Paper</th><th>Venue</th><th>Approach</th></tr></thead><tbody>"
            + rows
            + "</tbody></table></div>"
        )
    body = (
        crumb("<b>" + E(s["title"]) + "</b>")
        + f'<h2 class="ptitle">{E(s["title"])}</h2>'
        + f'<p class="lede">{E(s["blurb"])}</p>'
        + ('<div class="cards">' + cards + "</div>" if cards else
           ('<div class="banner stub">No prose written for this section yet — the papers below are '
            'indexed, but nobody has written the argument that connects them.</div>' if papers else ""))
        + tbl
        + stub_tbl
    )
    emit(url, f'{s["title"]} — zkAI', s["blurb"], body)


LONG_FIELDS = [
    ("approach", "Approach"),
    ("notes", "Notes"),
    ("security_model", "Security model"),
    ("terminology", "Terminology"),
    ("hardware_note", "On the hardware"),
    ("threat_model", "Threat model"),
    ("limitations", "Limitations"),
]
META_FIELDS = [
    ("venue", "Venue"), ("date", "Date"), ("affiliation", "Affiliation"),
    ("proof_system", "Proof system"), ("commitment_scheme", "Commitment"),
    ("hardware", "Hardware"), ("numbers_source", "Numbers from"),
    ("uses_zk", "Uses ZK"), ("verifiable", "Verifiable"), ("open_source", "Open source"),
]


def render_paper(p: Paper):
    ctx = Ctx(p.url)
    d = p.data
    sec = next((s for s in SECTIONS if s["key"] == p.section), None)

    meta = []
    for k, lbl in META_FIELDS:
        if d.get(k) is None:
            continue
        meta.append(f"<div><dt>{E(lbl)}</dt><dd>{fmt_num(d[k])}</dd></div>")
    for k, lbl in (("url", "Paper"), ("pdf", "PDF"), ("repo", "Code")):
        if d.get(k):
            meta.append(f'<div><dt>{E(lbl)}</dt><dd><a href="{E(str(d[k]))}">{E(str(d[k]))}</a></dd></div>')
    q = d.get("quantization") or {}
    if isinstance(q, dict) and "bits" in q:
        b = q["bits"]
        meta.append(
            f'<div><dt>Quantization</dt><dd>{fmt_num(b) if b is not None else "<span class=na>not stated</span>"}'
            + (" bits" if b is not None else "")
            + "</dd></div>"
        )

    authors = d.get("authors") or []
    ah = ""
    if authors:
        badge = "" if d.get("authors_verified") else '<span class="unver">unverified</span>'
        ah = f'<p class="authors">{E(", ".join(map(str, authors)))}{badge}</p>'

    # benchmarks
    bench = ""
    bs = [b for b in (d.get("benchmarks") or []) if isinstance(b, dict)]
    if bs:
        keys = []
        for b in bs:
            for k in b:
                if k not in keys and not k.endswith("_note") and not k.endswith("_source") and b[k] is not None:
                    keys.append(k)
        head = "".join(f'<th>{E(k.replace("_"," "))}</th>' for k in keys)
        rows = ""
        for b in bs:
            tds = "".join(
                f"<td>{fmt_params(b.get(k)) if k == 'params' else fmt_num(b.get(k))}</td>"
                for k in keys
            )
            rows += f"<tr>{tds}</tr>"
        notes = [
            f'<p style="font-size:13px;color:#6f7d86"><b>{E(k)}:</b> {E(str(v))}</p>'
            for b in bs for k, v in b.items() if k.endswith("_note") and v
        ]
        bench = (
            '<h3 class="head amber">Reported benchmarks</h3>'
            + '<div class="scrollx"><table class="matrix"><thead><tr>' + head
            + "</tr></thead><tbody>" + rows + "</tbody></table></div>"
            + "".join(notes)
        )

    # long-form fields from the YAML
    longs = ""
    for k, lbl in LONG_FIELDS:
        v = d.get(k)
        if not v:
            continue
        longs += f'<h3 class="head">{E(lbl)}</h3><div class="prose">{render_md(str(v), ctx)}</div>'

    # quantization deep block
    if isinstance(q, dict) and len(q) > 1:
        rows = "".join(
            f"<tr><th>{E(k)}</th><td><pre class='ascii' style='margin:0;border:0;padding:0;background:none'>"
            f"{E(yaml.safe_dump(v, sort_keys=False, allow_unicode=True).strip()) if isinstance(v,(dict,list)) else E(str(v))}"
            "</pre></td></tr>"
            for k, v in q.items()
        )
        longs += (
            '<h3 class="head">Quantization, in full</h3>'
            '<div class="scrollx"><table class="matrix"><tbody>' + rows + "</tbody></table></div>"
        )

    # citation neighbourhood
    def lst(ids):
        if not ids:
            return '<li class="none">none recorded</li>'
        out = []
        for i in sorted(set(ids)):
            if i in PAPERS:
                out.append(f'<li><a href="{ctx.link(PAPERS[i].url)}">{E(PAPERS[i].name)}</a></li>')
            else:
                out.append(f'<li>{E(EXTERNAL.get(i, i))} <span class="tag">external</span></li>')
        return "".join(out)

    cites = (
        '<h3 class="head">Citation neighbourhood</h3>'
        '<div class="cites">'
        f'<div><h5>Builds on</h5><ul>{lst(CITES.get(p.id, []))}</ul></div>'
        f'<div><h5>Cited by, in this corpus</h5><ul>{lst(CITED_BY.get(p.id, []))}</ul></div>'
        "</div>"
        f'<p style="font-size:13px;color:#6f7d86">Edges are a proxy: paper A\'s text mentions B '
        f'anywhere (body or bibliography). See the <a href="{ctx.link("graph/index.html")}">full graph</a>.</p>'
    )

    # our note
    note = ""
    n = PAPER_NOTES.get(p.id)
    if n:
        st = n["fm"].get("status", "draft")
        banner = "" if st == "reviewed" else '<div class="banner">Note is a draft — the PDF has not been fully read.</div>'
        note = (
            '<h3 class="head amber">Our reading</h3>' + banner
            + f'<div class="prose">{add_heading_ids(render_md(n["body"], ctx))}</div>'
        )
    else:
        note = (
            '<h3 class="head">Our reading</h3>'
            '<div class="banner stub">No deep-dive note yet. We have indexed this paper but not '
            "written up what to distrust about it.</div>"
        )

    disc = ""
    if DISCUSSED_IN.get(p.id):
        links = "".join(
            f'<a href="{ctx.link(g.url)}">{E(g.title)}</a>' for g in DISCUSSED_IN[p.id]
        )
        disc = f'<h3 class="head">Discussed in</h3><div class="rail">{links}</div>'

    # everything else, so nothing in the YAML is ever silently dropped
    shown = {"id", "name", "title", "authors", "authors_verified", "benchmarks", "quantization"}
    shown |= {k for k, _ in META_FIELDS} | {k for k, _ in LONG_FIELDS} | {"url", "pdf", "repo", "year"}
    rest = {k: v for k, v in d.items() if k not in shown}
    raw = ""
    if rest:
        raw = (
            "<details class='tbl'><summary>Other recorded fields</summary>"
            f"<pre class='ascii' style='margin:0'>{E(yaml.safe_dump(rest, sort_keys=False, allow_unicode=True))}</pre>"
            "</details>"
        )

    head = (
        crumb(
            f'<a href="{ctx.link("papers/index.html")}">Papers</a>',
            f'<a href="{ctx.link((sec["dir"] + "/index.html") if sec and sec["dir"] else "index.html")}">{E(sec["title"] if sec else "—")}</a>',
            f"<b>{E(p.name)}</b>",
        )
        + f'<h2 class="ptitle">{E(p.name)}</h2>'
        + f'<p class="psub">{E(str(d.get("title") or ""))}</p>'
        + ah
        + f'<div class="pmeta">{"".join(meta)}</div>'
    )
    emit(p.url, f"{p.name} — zkAI", str(d.get("title") or p.name), head + bench + longs + note + cites + disc + raw)


def render_papers_index():
    url = "papers/index.html"
    ctx = Ctx(url)
    rows = []
    for s in SECTIONS:
        for cat in s.get("papers_from") or []:
            for p in sorted(PAPERS_BY_CAT.get(cat, []), key=lambda x: -(x.year or 0)):
                val, _ = headline(p)
                note = "✓" if p.id in PAPER_NOTES else ""
                pdf = "✓" if p.data.get("pdf_available") or (ROOT / "references").rglob(f"{p.id}.pdf") and any((ROOT / "references").rglob(f"{p.id}.pdf")) else ""
                rows.append(
                    f'<tr><th><a href="{ctx.link(p.url)}">{E(p.name)}</a> {prov_dot(p.provenance)}</th>'
                    f'<td>{E(s["title"])}</td>'
                    f'<td>{E(str(p.year or "—"))}</td>'
                    f'<td>{E(str(p.data.get("venue") or "—"))}</td>'
                    f"<td>{E(val or '—')}</td>"
                    f'<td style="text-align:center">{pdf}</td>'
                    f'<td style="text-align:center">{note}</td></tr>'
                )
    body = (
        crumb("<b>Papers</b>")
        + '<h2 class="ptitle">Every <em>paper</em></h2>'
        + f'<p class="lede">All {len(PAPERS)} entries in <code>papers.yml</code>, across every cell. '
        '<b>PDF</b> means we hold the primary source; <b>Note</b> means someone has actually read it '
        "and written down what to distrust.</p>"
        + '<div class="ptools"><input id="ptable-filter" placeholder="filter by name, venue, section…">'
        f'<span class="count" id="ptable-count">{len(PAPERS)} shown</span></div>'
        + '<div class="scrollx"><table class="matrix" id="ptable"><thead><tr>'
        "<th>Paper</th><th>Section</th><th>Year</th><th>Venue</th><th>Headline</th><th>PDF</th><th>Note</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>" + PROV_KEY
    )
    emit(url, "Papers — zkAI", "Every paper in the zkAI corpus.", body)


_DOT_CACHE: dict[str, str] = {}


def render_dot(dot: str) -> str:
    """dot -> inline SVG. Cached: the graph page and the {{chart:citations}} shortcode
    both want it, and graphviz is the slowest thing in the build."""
    if dot in _DOT_CACHE:
        return _DOT_CACHE[dot]
    svg = ""
    if shutil.which("dot"):
        try:
            svg = subprocess.run(
                ["dot", "-Tsvg"], input=dot, capture_output=True, text=True, check=True
            ).stdout
            svg = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>", "", svg, flags=re.S).strip()
        except subprocess.CalledProcessError as exc:
            WARNINGS.append(f"graphviz failed: {exc.stderr[:200]}")
    if not svg:
        fallback = ROOT / "references" / "citation-graph.svg"
        if fallback.exists():
            svg = re.sub(
                r"<\?xml.*?\?>|<!DOCTYPE.*?>", "", fallback.read_text(), flags=re.S
            ).strip()
            WARNINGS.append(
                "graphviz (`dot`) not on PATH; embedded the committed "
                "references/citation-graph.svg instead, which may be stale"
            )
    _DOT_CACHE[dot] = svg
    return svg


def render_graph():
    url = "graph/index.html"
    ctx = Ctx(url)
    dot = build_dot()
    (DOCS / "graph").mkdir(parents=True, exist_ok=True)
    (DOCS / "graph" / "citation-graph.dot").write_text(dot)
    svg = render_dot(dot)

    n_edges = sum(len(v) for v in CITES.values())
    internal = {i for i in CITES} | {i for v in CITES.values() for i in v}
    crossing = crossing_edges()
    n_verify = sum(1 for i in internal if cell_of(i) == "verify")
    n_private = sum(1 for i in internal if cell_of(i) == "private")

    # The headline claim is falsifiable and re-checked on every build: if someone adds a
    # paper that DOES cite across the divide, this page must stop saying nobody does.
    if crossing:
        finding = (
            "<p>The two literatures are <strong>no longer fully disconnected</strong>: "
            f"{len(crossing)} edge(s) now join them — "
            + ", ".join(
                f"{E(PAPERS[a].name if a in PAPERS else a)} → {E(PAPERS[b].name if b in PAPERS else b)}"
                for a, b in crossing[:6]
            )
            + ". That is worth reading closely; it was zero when this corpus was first built.</p>"
        )
    else:
        finding = (
            "<p>The proving-inference cluster and the privacy-inference cluster are "
            "<strong>citation-disconnected</strong>. The zkML papers cite each other plus GKR, Lasso, "
            "zkCNN and Jolt. The MPC/HE papers cite each other plus Cheetah, SIRNN and THE-X. Not one "
            "edge crosses between them.</p>"
        )

    bridges = bridge_nodes()
    bridge_html = ""
    if bridges:
        items = ""
        for n, citers in bridges:
            nm = PAPERS[n].name if n in PAPERS else EXTERNAL.get(n, n)
            link = f'<a href="{ctx.link(PAPERS[n].url)}">{E(nm)}</a>' if n in PAPERS else E(nm)
            v = [a for a in citers if cell_of(a) == "verify"]
            p = [a for a in citers if cell_of(a) == "private"]
            fmt = lambda ids: ", ".join(
                E(PAPERS[i].name) if i in PAPERS else E(i) for i in ids
            )
            items += (
                f"<li>{link} — cited by <b>{fmt(v)}</b> on the verifiability side, and "
                f"<b>{fmt(p)}</b> on the privacy side.</li>"
            )
        bridge_html = (
            '<h3 class="head amber">Where the two literatures actually touch</h3>'
            '<div class="prose"><p>No edge runs directly between the two columns. But some papers '
            "are cited <em>by both</em> — and those are the real contact surface, more interesting "
            "than the absence of a direct edge:</p><ul>" + items + "</ul>"
            "<p>The pattern is that the contact happens at the <strong>numerics</strong> layer, not "
            "at the systems layer. Both communities are trying to do arithmetic on real numbers in a "
            "setting that only offers integers mod <em>p</em>, and both reach for the same small set "
            "of fixed-point, floating-point and truncation primitives to do it. They will read the "
            "same paper about rounding, and then not read each other's papers about GELU.</p>"
            f'<p style="font-size:13px">See <a href="{ctx.link("numerics/index.html")}">Numerics</a>, '
            "which is filed as a cross-cutting section for exactly this reason: it belongs to neither "
            "column, because it is underneath both.</p></div>"
        )

    body = (
        crumb("<b>Citation graph</b>")
        + '<h2 class="ptitle">Who builds on <em>whom</em></h2>'
        + '<p class="lede">Built by <code>pdftotext</code>-ing every PDF we hold and scanning each '
        "paper's text for mentions of the others. An edge A → B means <b>A's text mentions B</b> — "
        "a proxy for citation, not a hand-verified one.</p>"
        + '<div class="facts">'
        + f'<div class="fact"><b>{len(internal)}</b><span>nodes</span></div>'
        + f'<div class="fact"><b>{n_edges}</b><span>edges</span></div>'
        + f'<div class="fact"><b>{n_verify} · {n_private}</b><span>verifiability · privacy nodes</span></div>'
        + f'<div class="fact"><b>{len(crossing)}</b><span>edges between the two</span></div>'
        + f'<div class="fact"><b>{len(bridges)}</b><span>papers cited by both</span></div>'
        + "</div>"
        + f'<div class="graphwrap">{svg or "<p>graph unavailable</p>"}</div>'
        + '<h3 class="head">What the graph shows</h3>'
        + '<div class="prose">' + finding
        + "<p>They are working the two columns of the same 2×2, on the same "
        "operators — GELU, Softmax and LayerNorm are the expensive ones for both — with entirely "
        "different hammers, and they are not reading each other.</p>"
        '<p style="font-size:13px">Counted between the <em>verifiability</em> and <em>privacy</em> '
        "columns specifically. A survey citing zkGPT also crosses a section boundary, but says "
        "nothing about the two communities talking, so it is not counted here.</p></div>"
        + bridge_html
    )
    emit(url, "Citation graph — zkAI", "Who cites whom across the zkAI corpus.", body)


CELL_COLOR = {
    "verify-infer": "#d99a3f", "verify-train": "#a8c256",
    "private-infer": "#5fb0b7", "private-train": "#9b8bc4", "meta": "#6f7d86",
}


def build_dot() -> str:
    lines = [
        "digraph citations {",
        '  graph [bgcolor="#0a0c0e", rankdir=LR, splines=spline, nodesep=0.28, ranksep=1.0, pad=0.3];',
        '  node  [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11,'
        '         color="#28323a", fontcolor="#0a0c0e", penwidth=1];',
        '  edge  [color="#3b4750", arrowsize=0.6, penwidth=0.9];',
    ]
    nodes = {i for i in CITES} | {i for v in CITES.values() for i in v}
    for n in sorted(nodes):
        p = PAPERS.get(n)
        if p:
            sec = next((s for s in SECTIONS if s["key"] == p.section), None)
            col = CELL_COLOR.get(sec["cell"] if sec else "meta", "#6f7d86")
            lines.append(
                f'  "{n}" [label="{p.name}", fillcolor="{col}", URL="../papers/{n}.html", target="_top"];'
            )
        else:
            lines.append(
                f'  "{n}" [label="{EXTERNAL.get(n, n)}", shape=box, style="filled",'
                f' fillcolor="#1a2228", color="#3b4750", fontcolor="#a8a89f"];'
            )
    for a, ds in sorted(CITES.items()):
        for b in sorted(ds):
            lines.append(f'  "{a}" -> "{b}";')
    lines.append("}")
    return "\n".join(lines)


def render_home():
    ctx = Ctx("index.html")
    idx = next((p for p in PAGES_BY_SECTION.get("start", []) if p.slug == "index"), None)

    def cell_html(secs, cls, title, blurb):
        links = "".join(
            f'<a href="{ctx.link(SECTION_DIR[k] + "/index.html")}">{E(dict((s["key"], s["title"]) for s in SECTIONS)[k])}</a><br>'
            for k in secs if k in SECTION_DIR
        )
        n = sum(
            len(sum((PAPERS_BY_CAT.get(c, []) for c in (s.get("papers_from") or [])), []))
            for s in SECTIONS if s["key"] in secs
        )
        return (
            f'<div class="cell {cls}"><a class="ct" href="{ctx.link(SECTION_DIR[secs[0]] + "/index.html")}">{E(title)}</a>'
            f"<p>{E(blurb)}</p><div class=\"who\">{links}</div>"
            f'<div class="who" style="color:var(--muted)">{n} papers</div></div>'
        )

    the_map = (
        '<div class="map">'
        '<div class="mh"></div>'
        '<div class="mh col">Verifiability — prove it was done right</div>'
        '<div class="mh col">Privacy — hide the data or the model</div>'
        '<div class="mh row">Inference</div>'
        + cell_html(["zk-inference", "zk-testing"], "verify", "Proving inference",
                    "A checkable proof that a committed model produced this output on this input.")
        + cell_html(["private-inference"], "private", "Private inference",
                    "Confidentiality from the counterparty. Proves nothing about correctness.")
        + '<div class="mh row">Training</div>'
        + cell_html(["zk-training", "federated"], "verify", "Proving training",
                    "A proof that these weights are the result of correctly running this training procedure.")
        + cell_html(["private-training"], "private", "Private training",
                    "Train or fine-tune without revealing the data. Still no proof.")
        + "</div>"
    )

    def srow(s):
        cats = s.get("papers_from") or []
        n = len(sum((PAPERS_BY_CAT.get(c, []) for c in cats), []))
        n += len(sum((STUBS.get(c, []) for c in cats), []))
        pg = len([p for p in PAGES_BY_SECTION.get(s["key"], []) if p.slug != "index"])
        href = ctx.link((s["dir"] + "/index.html") if s["dir"] else "index.html")
        return (
            f'<a class="srow" href="{href}"><b>{E(s["title"])}</b><span>{E(s["blurb"])}</span>'
            f'<em>{n} papers · {pg} {"page" if pg == 1 else "pages"}</em></a>'
        )

    rows = "".join(srow(s) for s in SECTIONS if s["dir"])

    n_pdf = len({p.stem for p in (ROOT / "references").rglob("*.pdf")})
    n_notes = len(PAPER_NOTES)
    facts = (
        '<div class="facts">'
        f'<div class="fact"><b>{len(PAPERS)}</b><span>papers indexed</span></div>'
        f'<div class="fact"><b>{n_pdf}</b><span>PDFs actually read</span></div>'
        f'<div class="fact"><b>{n_notes}</b><span>with a written note</span></div>'
        f'<div class="fact"><b>{len(PAGES)}</b><span>essays</span></div>'
        "</div>"
    )

    intro = ""
    if idx:
        c2 = Ctx("index.html")
        intro = f'<div class="prose">{add_heading_ids(render_md(idx.body_md, c2))}</div>'

    body = (
        crumb("zkSecurity Research", "<b>Systematization of Knowledge</b>")
        + '<h2 class="ptitle">Verifiable <em>and</em> private AI</h2>'
        + '<p class="lede">The field is a <strong>2×2</strong> — which phase of the model\'s life you '
        "are protecting, and which property you want. Each cell is served by several different "
        "cryptographic approaches, with very different costs and very different guarantees. "
        "<strong>Most systems give you one property, not both.</strong></p>"
        + the_map
        + '<p style="font-size:13.5px;color:#6f7d86;max-width:74ch">The technique is not the axis. A cell '
        "can be filled by zero-knowledge proofs, secure multi-party computation, homomorphic encryption, "
        "trusted hardware, optimistic fraud proofs, or trace sampling — and the choice changes what you "
        "are trusting, not just what you are paying.</p>"
        + facts
        + intro
        + '<h3 class="head">Every section</h3><div class="seclist">' + rows + "</div>"
    )
    emit("index.html", "zkAI — Verifiable and private AI", "A systematization of knowledge on verifiable and private AI.", body)


def render_operators():
    """Operator atlas: index + one page per operator, from operators.yml."""
    ops = OPERATORS.get("operators") or []
    if not ops:
        return
    d = "zk-inference/operators"
    idx_url = f"{d}/index.html"
    ctx = Ctx(idx_url)
    groups = OPERATORS.get("groups") or sorted({o.get("group", "") for o in ops})
    cards = ""
    for g in groups:
        in_g = [o for o in ops if o.get("group") == g]
        if not in_g:
            continue
        cards += f'<h3 class="head">{E(str(g))}</h3><div class="cards">'
        for o in in_g:
            diff = o.get("difficulty", "mid")
            href = ctx.link("{}/{}.html".format(d, o["id"]))
            n_sch = len(o.get("schemes") or {})
            cards += (
                f'<div class="card meta"><div class="kicker">{E(str(o.get("difficulty_label") or diff))}</div>'
                f'<h4><a href="{href}">{E(o.get("name",""))}</a></h4>'
                f'<p>{E(str(o.get("sub") or ""))}</p>'
                f'<div class="foot">{n_sch} schemes address it</div></div>'
            )
        cards += "</div>"
    body = (
        crumb(f'<a href="{ctx.link("zk-inference/index.html")}">Proving inference</a>', "<b>Operator atlas</b>")
        + '<h2 class="ptitle">Operator <em>atlas</em></h2>'
        + '<p class="lede">Every algorithm inside an LLM forward pass that a zkSNARK must prove, and how '
        "each proving scheme handles it. Matmul is not the bottleneck; the nonlinearities are.</p>"
        + render_shortcode("coverage", "", ctx)
        + cards
    )
    emit(idx_url, "Operator atlas — zkAI", "Every operator in an LLM forward pass, and how each scheme proves it.", body)

    for i, o in enumerate(ops):
        url = "{}/{}.html".format(d, o["id"])
        c = Ctx(url)
        secs = ""
        if o.get("tex"):
            secs += f'<div class="math">$${o["tex"]}$$</div>'
        if o.get("what"):
            secs += '<h3 class="head">The algorithm</h3><div class="prose">' + render_md(str(o["what"]), c) + "</div>"
        if o.get("why"):
            secs += '<h3 class="head" style="color:var(--rose)">Why it resists a proof</h3><div class="prose">' + render_md(str(o["why"]), c) + "</div>"
        if o.get("kit"):
            secs += ('<h3 class="head" style="color:var(--cyan)">Cryptographic toolbox</h3><ul class="kit">'
                     + "".join(f"<li>{render_md(str(k), c)[3:-4]}</li>" for k in o["kit"]) + "</ul>")
        schemes = o.get("schemes") or {}
        secs += '<h3 class="head amber">How each scheme proves it</h3>'
        for pid in (OPERATORS.get("scheme_order") or list(schemes)):
            s = schemes.get(pid)
            nm = PAPERS[pid].name if pid in PAPERS else pid
            if not s:
                secs += (
                    f'<div class="gap"><span class="gm">{E(nm)} · gap</span><div class="gap-body">'
                    f"<p><b>Not addressed.</b> {E(nm)} describes no protocol for "
                    f'{E(str(o.get("name","")).lower())}.</p></div></div>'
                )
                continue
            head = (
                f'<div class="scheme-head"><span class="pname">'
                + (f'<a href="{c.link(PAPERS[pid].url)}" style="color:inherit">{E(nm)}</a>' if pid in PAPERS else E(nm))
                + "</span></div>"
            )
            inner = f'<p class="tldr">{render_md(str(s.get("tldr","")), c)[3:-4]}</p>' if s.get("tldr") else ""
            for qt in s.get("quotes") or []:
                inner += (
                    f'<blockquote class="q"><p>{E(str(qt.get("text","")))}</p>'
                    f'<cite><b>{E(str(qt.get("src","")))}</b> · {E(str(qt.get("sec","")))}</cite></blockquote>'
                )
            if s.get("bullets"):
                inner += "<ul>" + "".join(f"<li>{render_md(str(b), c)[3:-4]}</li>" for b in s["bullets"]) + "</ul>"
            for cb in s.get("code") or []:
                cap = f'<figcaption class="cap">{E(str(cb.get("caption","")))}</figcaption>' if cb.get("caption") else ""
                inner += (
                    f'<figure class="code"><figcaption>{E(str(cb.get("file","")))}'
                    + (f' · {E(str(cb["lines"]))}' if cb.get("lines") else "")
                    + f'</figcaption><pre class="src">{E(str(cb.get("src","")))}</pre>{cap}</figure>'
                )
            if s.get("audit"):
                inner += f'<div class="audit"><span class="audit-h">Audit surface</span>{render_md(str(s["audit"]), c)}</div>'
            if s.get("cost"):
                inner += f'<div class="cost">{render_md(str(s["cost"]), c)[3:-4]}</div>'
            secs += f'<div class="scheme" data-p="{E(pid)}">{head}<div class="scheme-body">{inner}</div></div>'

        prev_, next_ = (ops[i - 1] if i else None), (ops[i + 1] if i + 1 < len(ops) else None)
        pg = '<div class="pager">'
        if prev_:
            h = c.link("{}/{}.html".format(d, prev_["id"]))
            pg += f'<a href="{h}">← previous<span>{E(prev_.get("name",""))}</span></a>'
        if next_:
            h = c.link("{}/{}.html".format(d, next_["id"]))
            pg += f'<a class="next" href="{h}">next →<span>{E(next_.get("name",""))}</span></a>'
        pg += "</div>"

        body = (
            crumb(
                f'<a href="{c.link("zk-inference/index.html")}">Proving inference</a>',
                f'<a href="{c.link(idx_url)}">Operator atlas</a>',
                f'<b>{E(o.get("name",""))}</b>',
            )
            + f'<h2 class="ptitle">{E(o.get("name",""))}</h2>'
            + f'<p class="psub">{E(str(o.get("sub") or ""))}</p>'
            + secs + pg
        )
        emit(url, f'{o.get("name","")} — Operator atlas', str(o.get("sub") or ""), body)


# ---------------------------------------------------------------------------
MANIFEST = ".manifest"


def clean():
    """Delete only what a previous build emitted.

    Never `rm -rf docs/*`: docs/ is a git-tracked directory and a stray hand-written
    file in there (or a vendored asset) must not be destroyed by a build. We keep a
    manifest of what we wrote and remove exactly that.
    """
    mf = DOCS / MANIFEST
    if mf.exists():
        for line in mf.read_text().splitlines():
            f = DOCS / line.strip()
            if line.strip() and f.exists() and f.is_file():
                f.unlink()
        # prune directories that the removals left empty
        for d in sorted((p for p in DOCS.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
            if d.name != "vendor" and not any(d.iterdir()):
                d.rmdir()


def report_strays():
    """Files sitting in docs/ that this build did not produce. docs/ is generated output;
    anything else in there is either stale or a hand-written file that will be destroyed
    by the next build. Called after the build, so `written` is authoritative."""
    written = set(WRITTEN)
    for p in sorted(DOCS.rglob("*")):
        rel_p = str(p.relative_to(DOCS))
        if (
            p.is_file()
            and p.suffix in (".html", ".md", ".bak")
            and "vendor" not in p.parts
            and rel_p not in written
            and not rel_p.startswith(".")
        ):
            WARNINGS.append(
                f"docs/{rel_p} was not generated by this build. docs/ is generated output and "
                f"the next build may delete it -- move it to site/legacy/ or content/."
            )


def main():
    load()
    DOCS.mkdir(exist_ok=True)
    clean()
    shutil.copy(TPL / "style.css", DOCS / "style.css")
    (DOCS / ".nojekyll").write_text("")

    render_home()
    for s in SECTIONS:
        render_section_index(s)
    for pg in PAGES:
        if pg.section == "start" and pg.slug == "index":
            continue  # folded into the home page
        render_page(pg)
    render_operators()
    for p in PAPERS.values():
        render_paper(p)
    render_papers_index()
    render_graph()

    WRITTEN.extend(["style.css", ".nojekyll", "graph/citation-graph.dot"])
    (DOCS / MANIFEST).write_text("\n".join(sorted(set(WRITTEN))) + "\n")
    report_strays()

    print(f"built {len(WRITTEN)} files -> docs/")
    if WARNINGS:
        print(f"\n{len(WARNINGS)} warning(s):")
        for w in dict.fromkeys(WARNINGS):
            print("  ·", w)

    if "--serve" in sys.argv:
        import http.server, socketserver, os
        os.chdir(DOCS)
        print("serving http://localhost:8000/index.html")
        socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler).serve_forever()


if __name__ == "__main__":
    main()
