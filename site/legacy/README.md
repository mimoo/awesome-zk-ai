# Legacy source

The hand-built single-page "Operator Atlas" that the generated site replaces.

- `operator-atlas.html` — the original `docs/index.html`. Its `OPERATORS`, `CHALLENGES`
  and `AUDIT` JS arrays were the source for `operators.yml`. Kept because it is the
  provenance for that extraction, and because the extraction may need re-checking.
- `jolt-atlas-from-source.md` — code-grounded read of the Jolt Atlas repo @b20cdce.
  Folded into `content/papers/jolt-atlas.md`.

Nothing here is built. `docs/` is generated output and is wiped on every build; these
files live here so they cannot be destroyed by it.
