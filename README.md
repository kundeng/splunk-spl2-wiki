# SPL2 Context7 Library

This repository is primarily a Splunk SPL2 reference library for Context7-style retrieval and skill use. Its main deliverables are the SPL2 scenario cookbook, the developer tutorial, and the packaged `spl2-context7` skill.

The fetcher and local corpus tooling exist to maintain those references against Splunk's primary documentation. They are supporting infrastructure, not the main product of the repository.

## Outputs

- Context7 skill:
  `skills/spl2-context7/`
- Tutorial:
  `docs/spl2-developer-tutorial.md`
- Scenario cookbook:
  `docs/spl2-context7-cookbook.md`
- Corpus usage guide:
  `docs/corpus-usage.md`
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
- `docs/spl2-context7-cookbook.md`
- `docs/spl2-developer-tutorial.md`

## Source Maintenance

If you need to rebuild the local source corpus from Splunk Help:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_spl2_docs.py
```

The fetcher downloads SPL2 overview, search manual, and search reference pages from `help.splunk.com`, extracts article content and metadata, and writes a local corpus under `research/`.

`research/` is intentionally gitignored so the repository stays small and only tracks the durable source files.

## Local Corpus Usage

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
