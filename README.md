# SPL2 Context7 Library

This repository is a Splunk SPL2 reference library for Context7-style retrieval and skill use. Its main deliverables are the packaged `spl2-context7` skill, the SPL2 scenario cookbook, and the developer tutorial.

## Outputs

- Context7 skill:
  `skills/spl2-context7/`
- Tutorial:
  `skills/spl2-context7/references/spl2-developer-tutorial.md`
- Scenario cookbook:
  `skills/spl2-context7/references/spl2-context7-cookbook.md`
- Fetcher:
  `scripts/fetch_spl2_docs.py`

## Primary Use

Use this repository when you want:

- SPL2 examples and snippets
- SPL to SPL2 migration guidance
- module, view, and namespace patterns
- command/function reference usage patterns
- a reusable skill package for SPL2-focused assistants

Start here:

- `skills/spl2-context7/SKILL.md`
- `skills/spl2-context7/references/spl2-context7-cookbook.md`
- `skills/spl2-context7/references/spl2-developer-tutorial.md`

## Source Maintenance

If you need to rebuild the local source corpus from Splunk Help:

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
