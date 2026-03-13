# SPL2 Research Workspace

This repo contains SPL2 writing artifacts and a fetcher that can build a local documentation corpus from Splunk Help.

## Outputs

- Tutorial:
  `docs/spl2-developer-tutorial.md`
- Scenario cookbook:
  `docs/spl2-context7-cookbook.md`
- Context7 skill:
  `skills/spl2-context7/`
- Fetcher:
  `scripts/fetch_spl2_docs.py`

## Refresh The Corpus

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_spl2_docs.py
```

The fetcher downloads SPL2 overview, search manual, and search reference pages from `help.splunk.com`, extracts article content and metadata, and writes a local corpus under `research/`.

`research/` is intentionally gitignored so the repository stays small and only tracks the durable source files.

## Skill Layout

The repository also includes a skill package for Context7-style use:

- `skills/spl2-context7/SKILL.md`
- `skills/spl2-context7/references/spl2-context7-cookbook.md`
- `skills/spl2-context7/references/spl2-developer-tutorial.md`
