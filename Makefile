.PHONY: site check serve graph clean all

all: site check

## build docs/ from papers.yml + operators.yml + content/
site:
	@python3 site/build.py

## integrity checks: drift between data and prose, provenance discipline, unread PDFs
check:
	@python3 site/validate.py

## build + serve on :8000
serve:
	@python3 site/build.py --serve

## re-extract the citation graph by scanning the PDFs in references/
graph:
	@python3 site/citegraph.py
	@dot -Tsvg references/citation-graph.dot -o references/citation-graph.svg 2>/dev/null || true

## remove generated output
clean:
	@python3 - <<'PY'
	from pathlib import Path
	d = Path("docs"); mf = d / ".manifest"
	if mf.exists():
	    for line in mf.read_text().split():
	        f = d / line
	        if f.is_file(): f.unlink()
	    mf.unlink()
	    print("cleaned docs/ (vendor/ kept)")
	PY

## deps
setup:
	@python3 -m pip install --user "markdown>=3.5" pyyaml
