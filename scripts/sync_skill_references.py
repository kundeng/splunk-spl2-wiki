#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DOCS = {
    ROOT / "docs" / "spl2-context7-cookbook.md": ROOT
    / "skills"
    / "spl2-context7"
    / "references"
    / "spl2-context7-cookbook.md",
    ROOT / "docs" / "spl2-developer-tutorial.md": ROOT
    / "skills"
    / "spl2-context7"
    / "references"
    / "spl2-developer-tutorial.md",
}

HEADER = (
    "<!-- Generated file. Do not edit directly. -->\n"
    "<!-- Source of truth lives under /docs. Run "
    "`python3 scripts/sync_skill_references.py` after changes. -->\n\n"
)


def main() -> int:
    for source, target in SOURCE_DOCS.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        body = source.read_text(encoding="utf-8")
        target.write_text(HEADER + body, encoding="utf-8")
        print(f"synced {source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
