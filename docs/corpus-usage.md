# Using The Local SPL2 Corpus

This page explains how to work with the generated `research/` corpus after running the fetcher.

## Prerequisites

Build the corpus first:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_spl2_docs.py
```

Expected output directories:

- `research/raw/`
  Original HTML pages downloaded from Splunk Help.
- `research/extracted/`
  Structured JSON documents parsed from the HTML pages.
- `research/index/manifest.json`
  Lightweight index of the extracted corpus.
- `research/index/summary.md`
  Human-readable count summary by section.

## Search The Corpus From The CLI

Search all extracted documents for a keyword:

```bash
rg "timechart" research/extracted
```

Search only titles or metadata-like fields:

```bash
rg '"title"|\"section\"|\"url\"' research/extracted
```

Search for documents in a specific SPL2 section:

```bash
rg '"section": "spl2-search-reference"' research/extracted
```

Search for a command name:

```bash
rg '"title": ".*stats command' research/extracted
```

Preview manifest entries quickly:

```bash
python3 - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path("research/index/manifest.json").read_text())
for item in manifest[:10]:
    print(item["section"], "|", item["title"], "|", item["url"])
PY
```

## Query The Corpus From Python

Load all extracted documents:

```python
import json
from pathlib import Path

docs = [
    json.loads(path.read_text())
    for path in Path("research/extracted").glob("*.json")
]

print(f"Loaded {len(docs)} documents")
```

Find documents by title:

```python
matches = [doc for doc in docs if "timechart" in doc["title"].lower()]
for doc in matches:
    print(doc["title"], doc["url"])
```

Find documents by body text:

```python
matches = [doc for doc in docs if "lookup" in doc["text"].lower()]
for doc in matches[:5]:
    print(doc["title"])
```

Filter by section:

```python
reference_docs = [doc for doc in docs if doc["section"] == "spl2-search-reference"]
print(len(reference_docs))
```

Show headings for a specific page:

```python
doc = next(doc for doc in docs if "what is spl2" in doc["title"].lower())
for heading in doc["headings"]:
    print(heading["level"], heading["text"])
```

## Extracted Document Shape

Each file in `research/extracted/` contains a JSON object like:

```json
{
  "url": "https://help.splunk.com/...",
  "title": "What is SPL2?",
  "description": "Page description",
  "last_modified_iso": "2026-01-16T18:25:41.632Z",
  "content_type": "Concept",
  "section": "spl2-overview",
  "breadcrumbs": ["Splunk Cloud Platform", "Search", "SPL2 Overview"],
  "headings": [
    {"level": "h1", "id": "ariaid-title1", "text": "What is SPL2?"}
  ],
  "related_links": [
    {"text": "Why use SPL2?", "url": "https://help.splunk.com/..."}
  ],
  "text": "# What is SPL2?\n..."
}
```

Useful fields:

- `title`
  Best for exact page matching.
- `section`
  Useful for narrowing results to overview, manual, or reference content.
- `headings`
  Useful for section-aware indexing or chunking.
- `related_links`
  Useful for graph-style traversal or “read next” flows.
- `text`
  Main search surface for full-text retrieval.

## Offline Use

Once the corpus has been built, the minimum useful offline set is:

- `research/extracted/`
- `research/index/manifest.json`
- `research/index/summary.md`

Include `research/raw/` as well if you want the original HTML snapshots for debugging extraction or reprocessing.

## Team Workflow

The repository intentionally ignores `research/` in git. Recommended team pattern:

1. Commit only the fetcher, requirements, docs, and skill files.
2. Regenerate `research/` locally on each machine.
3. Keep developers on the same branch and Python dependency set.
4. If reproducibility matters, compare `research/index/manifest.json` outputs after refreshes.

This keeps the repo small while still allowing each developer to maintain a local searchable corpus.
