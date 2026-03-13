# SPL2 Research Workspace

This repo contains SPL2 writing artifacts and a fetcher that can build a local documentation corpus from Splunk Help.

## Outputs

- Tutorial:
  `docs/spl2-developer-tutorial.md`
- Scenario cookbook:
  `docs/spl2-context7-cookbook.md`
- Corpus usage guide:
  `docs/corpus-usage.md`
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

## Use The Corpus

After generating `research/`, see:

- `docs/corpus-usage.md`

That guide covers:

- searching the extracted corpus with shell tools
- loading and querying the extracted JSON from Python
- understanding the extracted document structure
- offline and team-local usage patterns

## Skill Layout

The repository also includes a skill package for Context7-style use:

- `skills/spl2-context7/SKILL.md`
- `skills/spl2-context7/references/spl2-context7-cookbook.md`
- `skills/spl2-context7/references/spl2-developer-tutorial.md`

The files under `docs/` are the authoring source of truth. Sync them into the skill package with:

```bash
python3 scripts/sync_skill_references.py
```
