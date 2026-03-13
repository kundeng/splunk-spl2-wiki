---
name: spl2-context7
description: SPL2 guidance for Splunk search, migration, and reusable query authoring. Use this whenever the user asks about Splunk SPL2 syntax, converting SPL to SPL2, `search` versus `from`, quoting rules, eval/stats expressions, modules, views, namespaces, compatibility profiles, or wants working SPL2 examples and snippets. Also use it when the user wants scenario-based SPL2 answers instead of long prose.
---

# SPL2 Context7 Skill

Use this skill to answer SPL2 questions with concise, practical guidance grounded in Splunk documentation.

## What This Skill Covers

- SPL2 syntax and mental model
- `search` versus `from`
- SPL to SPL2 migration
- quoting, lists, option ordering, and expression rules
- `eval`, `where`, `stats`, `timechart`, `spath`, `lookup`, `join`, and other common commands
- modules, branching, views, and namespaces
- compatibility profiles across `splunkd`, `edgeProcessor`, and `ingestProcessor`

## Strong Defaults

Before answering:

1. Identify the runtime context:
   Search bar, module editor, app development, Edge Processor, or Ingest Processor.
2. Check whether portability matters.
3. Prefer the smallest snippet that solves the user's task.

When writing SPL2:

- Prefer `search` for SPL-style searches and `from` for SQL-style searches.
- In modules, use explicit generating commands and named searches.
- Use double quotes for string literals.
- Use single quotes for field names that contain spaces, dashes, wildcards, dots, or start with non-letters.
- Use comma-separated field lists.
- Put command options before command arguments.
- Treat `spl1` as a migration bridge, not the default design.

## Answer Shape

Default answer format:

1. One-line scenario framing.
2. One or more SPL2 snippets.
3. Short caveat section:
   compatibility, Search bar versus module editor, quoting, or migration gotchas.

Prefer examples over abstract explanation unless the user asks for concepts first.

## Reference Files

Read only the reference file that matches the user's need.

- `references/spl2-context7-cookbook.md`
  Use for scenario-first answers, snippets, and command examples.
- `references/spl2-developer-tutorial.md`
  Use for deeper explanations, architecture, migration rationale, modules/views/namespaces, expression semantics, and broader developer guidance.
- `references/spl2-grammar-and-functions-reference.md`
  Use for language lookup: grammar primitives, query forms, expression forms, and built-in function examples by family.

## Selection Guide

Use the cookbook first when the user asks:

- "How do I write ..."
- "Show me an example of ..."
- "Convert this to SPL2"
- "What is the SPL2 version of ..."
- "Give me a snippet for ..."

Use the tutorial first when the user asks:

- "What changed in SPL2?"
- "How should we structure SPL2 in a project?"
- "When should I use modules or views?"
- "How do compatibility profiles affect design?"

Use the grammar/functions reference first when the user asks:

- "Show me the syntax for ..."
- "What functions exist for ..."
- "Give me an example of every ... function"
- "How do arrays/objects/lambdas/templates work in SPL2?"

Use both when the user wants explanation plus code.

## Review Rules

When reviewing SPL2, look for these issues first:

- Search bar syntax used incorrectly inside a module
- unsupported command/function for the target profile
- missing commas in field lists
- incorrect quote type
- option ordering that still reflects SPL habits
- `eval` assigning Boolean results directly
- overuse of wildcards
- unnecessary `spl1` usage where direct SPL2 exists

## If You Need More Detail

If the reference docs in this skill are insufficient, consult the underlying Splunk Help sources captured by this repository's fetch process rather than inventing syntax.
