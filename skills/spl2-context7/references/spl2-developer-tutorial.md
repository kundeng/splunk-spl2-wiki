<!-- Generated file. Do not edit directly. -->
<!-- Source of truth lives under /docs. Run `python3 scripts/sync_skill_references.py` after changes. -->

# SPL2 for Developers

This tutorial is a developer-oriented guide to Splunk SPL2 based on a locally downloaded corpus of Splunk primary documentation. The corpus in this repo contains 282 SPL2 documents captured on March 13, 2026:

- `research/index/manifest.json`
- `research/index/summary.md`

The goal here is not to restate the product docs page-by-page. It is to turn them into a coherent mental model for engineers who need to write, migrate, review, and reuse SPL2 in real projects.

## Scope

This guide focuses on SPL2 as documented for:

- Splunk Cloud Platform Search
- Splunk Enterprise Search
- SPL2-based app development on the `splunkd` profile
- Cross-product concepts that also affect Edge Processor and Ingest Processor

Primary source sets:

- SPL2 Overview:
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/what-is-spl2
- SPL2 Search Manual:
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/getting-started/searching-data-using-spl2
- SPL2 Search Reference:
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/introduction/introduction

## 1. What SPL2 Is

SPL2 is Splunk's newer Search Processing Language. It is intended to unify search and data preparation across multiple Splunk products, while supporting both SPL-like and SQL-like styles. That matters for developers because SPL2 is not just "SPL with a few syntax changes". It introduces:

- A bimodal query style: SPL-style pipelines and SQL-style `FROM` / `SELECT`
- Reusable modules, views, and namespaces
- Compatibility profiles across products
- Structured expression features such as arrays, objects, lambdas, templates, and richer function behavior
- A path for embedding unsupported SPL fragments with `spl1`

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/what-is-spl2
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/what-is-new-and-different-in-spl2-

## 2. Where You Can Use SPL2

SPL2 is exposed through several interfaces:

- Search & Reporting app
- Pipeline editor
- Splunk Extension for VS Code
- REST API interfaces

In the Search & Reporting app, there are two distinct authoring modes:

- The Search bar for standalone, ad hoc SPL2 statements
- The SPL2 module editor for reusable, multi-statement work

Use the Search bar when the search is disposable. Use the module editor when the search should be named, branched, reused, exported, shared, or combined with custom functions or types.

Important environment note from the docs:

- On Splunk Enterprise, SPL2 support in Search & Reporting is documented only for Unix and Linux systems.

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/where-can-i-use-spl2
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/standalone-searches-in-the-search-bar/run-an-spl2-search-in-the-search-bar
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/getting-started/search-page-overview-for-spl2

## 3. SPL2 Mental Model

If you already know SPL, the biggest upgrade is not syntax. It is the resource model.

### 3.1 Datasets

A dataset is any collection of data you can query or feed into later search stages. Common examples include:

- Indexes
- Metric indexes
- Lookups
- Jobs
- Views
- Search results from a prior named statement

This is why `from` is so central in SPL2. It treats data sources more uniformly.

### 3.2 Modules

A module is a file that contains one or more related SPL2 statements. A module can hold:

- Search statements
- Custom functions
- Custom data types
- Import and export statements

This is the right abstraction for code review, collaboration, and reuse. A serious SPL2 codebase should think in modules, not only pasted searches.

### 3.3 Statements

Statements are the top-level units inside a module. Search statements are only one kind of statement.

### 3.4 Search Names

Inside a module, searches have names such as `$base_search`. Those names act like variables referring to result datasets. That enables search branching and chained workflows.

Naming rules documented by Splunk include:

- Search names start with `$`
- The first character after `$` must be lowercase
- Remaining characters can be lowercase letters, digits, or `_`
- Names must be unique within the module

### 3.5 Branching

Branching is one of the most useful SPL2 developer features. You can:

- Create cascading child searches
- Create parallel branches from the same base search
- Reuse the output of one named search as the dataset for another

That is a material improvement over repeatedly retyping or copy-pasting large SPL pipelines.

### 3.6 Views

An SPL2 view is a named SPL2 search exported from a module. A view gives you a reusable abstraction layer over raw datasets, which is useful for:

- Shared business logic
- Reusable filtering
- Data masking
- Team-facing curated datasets

### 3.7 Namespaces

Namespaces are the packaging and identity system for SPL2 resources. They are closer to logical containers than filesystem directories. They matter when you want to:

- Import shared resources
- Avoid naming conflicts
- Package SPL2 resources with apps
- Reuse custom functions, types, modules, and views across teams

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/spl2-modules-and-statements
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/branching-spl2-searches
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/spl2-views
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/export-import-and-namespaces/understanding-spl2-namespaces

## 4. SPL2 Has Two Query Styles

Splunk explicitly documents SPL2 as supporting both SPL and SQL syntax patterns.

### 4.1 SPL-style searches

Use SPL-style syntax when you want:

- Familiar search pipelines
- Search literals and keyword-heavy filtering
- Straightforward migration from existing SPL

Example:

```spl
search index=main status=200 host=www2
| fields _time, productId, categoryId
| stats count() by categoryId
```

### 4.2 SQL-style searches

Use SQL-style syntax when you want:

- A `FROM`/`WHERE`/`GROUP BY`/`SELECT` mental model
- Cleaner clause-oriented reads
- Easier onboarding for SQL-heavy developers

Example:

```spl
FROM main
WHERE status=200 AND host="www2"
GROUP BY categoryId
SELECT _time, categoryId, count() AS event_count
```

### 4.3 Mixed style is allowed

Splunk documents that you can start with SQL-like syntax and continue with SPL2 commands in a pipeline. In practice, many effective SPL2 queries are hybrid:

```spl
FROM main
WHERE sourcetype="access_*"
SELECT _time, host, status, bytes
| eval kb=bytes/1024
| stats avg(kb) AS avg_kb by host, status
```

### 4.4 Choosing between `search` and `from`

The Search Manual recommends thinking first about the generating command:

- `search` when you want SPL-style search semantics
- `from` when you want SQL-like clauses and more explicit dataset handling

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/introduction/understanding-spl2-syntax
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/getting-started/quick-start-write-and-run-a-basic-spl2-search/start-searching-data-using-spl2
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/from-command/from-command-overview

## 5. Search Bar Versus Module Editor

This distinction is easy to miss and causes real confusion.

### 5.1 Search bar behavior

The Search bar is for one standalone statement. It supports SPL2, but it also preserves some convenience behavior:

- If the first expression is `index=<index_name>`, `search` can be implied
- If the first expression is not an index expression, you must write `search` explicitly

Example:

```spl
index=main status=404
```

But this must be written explicitly:

```spl
search 404 index=main
```

### 5.2 Module editor behavior

In modules:

- You explicitly write the generating command
- You must name each search
- Reuse, branching, views, and imports become available

Example:

```spl
$errors = search index=main status=404
```

That difference matters for migration. A query that works in the Search bar as implicit `search` might need an explicit command and a name in a module.

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/standalone-searches-in-the-search-bar/run-an-spl2-search-in-the-search-bar
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/getting-started/quick-start-write-and-run-a-basic-spl2-search/start-searching-data-using-spl2

## 6. Syntax Rules That Trip Up SPL Users

This is the section most migration work needs.

### 6.1 Lists are comma-separated

In SPL2, lists are consistently comma-separated.

Instead of:

```spl
... | dedup 2 source host
```

Use:

```spl
... | dedup 2 source, host
```

### 6.2 Command options come before command arguments

SPL2 standardizes option placement. For example:

```spl
... | bin bins=10 size as bin_size
```

### 6.3 Field names may require single quotes

If a field name:

- starts with something other than a letter or `_`
- or contains spaces, dashes, wildcards, or other special characters

then single-quote it.

Examples:

```spl
... | eval 'low-category' = lower(categoryId)
... | stats sum(bytes) AS 'Sum of bytes'
FROM main WHERE '5minutes'="late"
SELECT 'host*' FROM main
```

### 6.4 String values use double quotes

String literals in SPL2 are generally written with double quotes:

```spl
FROM main WHERE sourcetype="access_*"
```

The documented exception is the `search` command, which preserves backward-compatible field-value behavior.

### 6.5 Search literals use backticks

Use backticks when you want one or more raw search terms embedded as a search literal:

```spl
FROM main
WHERE `user "ladron" from 192.0.2.0/24`
```

### 6.6 Concatenation uses `+`

SPL used `.` for concatenation. SPL2 uses `+`.

```spl
... | eval full_name = first_name + " " + last_name
```

### 6.7 Boolean handling in `eval` is stricter

The docs explicitly note that `eval` cannot directly assign a Boolean value. If a function returns Boolean, wrap it in a function such as `if(...)` when you need an assignable result.

Example:

```spl
... | eval is_error = if(status in("500", "503"), "true", "false")
```

### 6.8 Stats expressions are simplified

SPL often used `count(eval(...))`. SPL2 documents direct eval-expression support in stats functions.

Example migration:

```spl
... | stats count(status="404") AS count_404 by host
```

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/specific-differences-between-spl-and-spl2
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/wildcards-quotes-and-escape-characters/quotation-marks
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/wildcards-quotes-and-escape-characters/when-to-escape-characters
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/eval-command/eval-command-usage
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/statistical-and-charting-functions/overview-of-spl2-stats-and-chart-functions

## 7. Expressions: The Real Power Center

Developers should treat expressions as the core language, not as a side feature.

Splunk documents expression support for:

- Literals
- Fields
- Assignments
- Function calls
- Predicates
- Unary and binary operations
- Arrays
- Objects
- Search literals
- Parameters
- Lambdas
- Templates

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/types-of-expressions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/predicate-expressions

### 7.1 Predicate expressions

Predicates are used in:

- `where`
- `WHERE`
- `HAVING`

Operators and predicate forms documented by Splunk include:

- Relational operators such as `=`, `!=`, `>`, `<`
- Logical operators such as `AND`, `OR`, `NOT`, `XOR`
- Pattern and conditional forms such as `IN`, `LIKE`, `BETWEEN`, `IS NULL`, `EXISTS`

Example:

```spl
FROM main
WHERE status IN ("400", "401", "403", "404")
SELECT _time, host, status
```

### 7.2 Arrays and objects

SPL2 supports structured literals directly.

Example array:

```spl
... | eval severities=["low", "medium", "high"]
```

Example object:

```spl
... | eval meta={env: "prod", owner: "payments", critical: true}
```

This makes SPL2 much more useful for JSON-heavy work than classic SPL.

### 7.3 String templates

String templates embed expressions inside strings:

```spl
... | eval message="status=${status} host=${host}"
```

They are cleaner than manual concatenation for formatted values.

### 7.4 Field templates

Field templates let you compute field names dynamically:

```spl
SELECT * FROM [{city: "Seattle", Seattle: 123}]
| eval '${city}' = 456
```

This is powerful, but it also raises readability and schema-discipline concerns. Use it intentionally.

### 7.5 Lambdas

SPL2 includes lambda expressions, which is unusual if your mental model is "just a search language". That is one of the clearest signals that SPL2 is a richer programming surface than SPL.

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/array-and-object-literals-in-expressions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/string-templates-in-expressions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/field-templates-in-expressions

## 8. Quoting, Wildcards, and Escaping

The quickest way to write invalid SPL2 is to carry over SPL quoting habits without adjustment.

### 8.1 Single quotes

Use single quotes for field names that need quoting:

```spl
'status-code'
'host*'
'Sum of bytes'
```

### 8.2 Double quotes

Use double quotes for string literals:

```spl
host="www2"
sourcetype="access_*"
```

### 8.3 Backticks

Use backticks for search literals:

```spl
WHERE `invalid user sshd[5258]`
```

### 8.4 Wildcard behavior depends on context

Splunk documents different wildcard behavior by command family:

- `LIKE` with `%` and `_` in `where`, `WHERE`, and `eval`
- `*` in many other commands

Examples:

```spl
WHERE like(source, "license%")
search sourcetype="access_*"
```

### 8.5 Escaping

Use backslash escaping when needed, but prefer cleaner alternatives where possible:

- Search literals
- Raw string literals

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/wildcards-quotes-and-escape-characters/quotation-marks
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/wildcards-quotes-and-escape-characters/when-to-escape-characters
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/wildcards-quotes-and-escape-characters/wildcards

## 9. The Core Command Set You Will Actually Use

You do not need all 189 reference pages before becoming productive. You need a strong foundation in a smaller set:

- `search`
- `from`
- `where`
- `eval`
- `fields`
- `stats`
- `sort`
- `dedup`
- `lookup`
- `spath`
- `timechart`
- `streamstats`
- `join` and `union` when necessary

The SPL2 command quick reference and compatibility tables are the fastest way to see:

- what exists
- what each command does
- whether a product profile supports it

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/quick-reference-for-spl2-commands
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references/compatibility-quick-reference-for-spl2-commands

### 9.1 `from`

Use `from` when you want clause-driven search construction:

```spl
FROM main
WHERE earliest=-15m@m AND sourcetype="access_*"
GROUP BY host
SELECT host, sum(bytes) AS total_bytes
ORDER BY total_bytes DESC
LIMIT 20
```

The docs emphasize that `FROM` and `SELECT` are flexible entry points, but clause ordering still matters.

### 9.2 `search`

Use `search` when you want SPL-style filtering or keyword-centric semantics:

```spl
search index=main status=500 host=www1
| fields _time, host, uri_path, status
```

### 9.3 `where`

Use `where` for Boolean filtering over prior results:

```spl
... | where status IN ("500", "503") AND like(uri_path, "/api/%")
```

### 9.4 `eval`

Use `eval` to compute fields and normalize values:

```spl
... | eval kb=bytes/1024, tier=if(bytes > 1048576, "large", "small")
```

### 9.5 `stats`

Use `stats` for aggregation:

```spl
... | stats count() AS requests, avg(bytes) AS avg_bytes by host, status
```

### 9.6 `spath`, arrays, and JSON

Use structured expressions together with JSON-aware functions and commands when working with nested payloads. This is one of SPL2's better developer stories.

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/from-command/from-command-overview
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/search-command/search-command-overview-and-syntax
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/search-command/search-command-usage
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/where-command/where-command-overview-syntax-and-usage
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/eval-command/eval-command-overview-and-syntax
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/eval-command/eval-command-usage
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/stats-command/stats-command-overview-syntax-and-usage

## 10. Eval Functions and Stats Functions

SPL2's function library is broad enough that it is worth studying by category.

### 10.1 Eval function categories

Splunk documents categories including:

- Comparison and conditional
- Conversion
- Cryptographic
- Date and time
- Informational
- JSON
- Mathematical
- Multivalue
- Statistical eval
- Text
- Trigonometric and hyperbolic

### 10.2 Stats and charting categories

Documented categories include:

- Aggregate functions
- Event order functions
- Multivalue and array functions
- Time functions

The important developer takeaway is that SPL2 is not only command-driven. A large part of expressiveness comes from combining:

- `eval`
- `where`
- `from ... SELECT`
- stats-family functions
- JSON-aware functions

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/evaluation-functions/overview-of-spl2-eval-functions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/statistical-and-charting-functions/overview-of-spl2-stats-and-chart-functions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references/compatibility-quick-reference-for-spl2-evaluation-functions

## 11. Compatibility Profiles Matter

This is a major operational point.

SPL2 is described as product-agnostic, but products only implement subsets through compatibility profiles. Splunk documents at least these profiles:

- `splunkd`
- `edgeProcessor`
- `ingestProcessor`

Do not assume that because a command exists in the SPL2 reference it is available in every SPL2-capable product surface.

Examples from the docs:

- `spl1` is documented for search contexts, not pipelines
- some commands exist only in `splunkd`
- commands such as `branch`, `eval`, `fields`, `from`, `into`, and `timewrap` vary by profile support

For developer work, that means:

1. identify the target runtime first
2. check the compatibility quick references second
3. only then finalize query design

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references/compatibility-quick-reference-for-spl2-commands
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references/compatibility-quick-reference-for-spl2-evaluation-functions

## 12. Migration from SPL to SPL2

Splunk provides conversion tools in the Search bar and module editor. Use them, but do not treat them as the end of migration.

### 12.1 What the converter is good for

- Rapid first-pass syntax translation
- Learning equivalent SPL2 forms
- Bootstrapping existing searches into module-friendly form

### 12.2 What still requires human review

- Search bar versus module context
- Implicit versus explicit `search`
- Comma-separated lists
- Quoting rules
- Boolean handling in `eval`
- Direct stats expressions
- Product-profile compatibility

### 12.3 Practical migration checklist

1. Determine target runtime:
   Search bar, module editor, app, Edge Processor, or Ingest Processor.
2. Convert the original SPL using Splunk's tooling when available.
3. Normalize syntax:
   commas, option order, quoting, concatenation, explicit `search` where needed.
4. Re-evaluate command support:
   if a command is unsupported directly, see whether `spl1` is acceptable.
5. Refactor into named searches if the query will be reused.
6. Extract shared logic into views or module-local helpers if the search is growing.

### 12.4 `spl1` as a bridge, not a destination

Splunk documents `spl1` as the way to embed SPL commands that SPL2 does not directly support. That is useful during migration, but it should usually be treated as transitional unless:

- the command is genuinely unavailable in SPL2
- the target profile supports `spl1`
- portability is not a priority

Relevant sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/using-spl-commands-in-spl2-searches
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/converting-spl-to-spl2/convert-a-search-from-spl-to-spl2
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl1-command

## 13. Practical Development Patterns

### 13.1 Pattern: Start ad hoc, then promote to module

Start in the Search bar when exploring:

```spl
search index=main status=500
| stats count() by host
```

Promote to a module when it becomes reusable:

```spl
$error_events = search index=main status=500
$error_counts = from $error_events
| stats count() AS error_count by host
```

### 13.2 Pattern: Use a base search for investigation trees

```spl
$base = search index=main sourcetype="access_*"
$http_4xx = from $base | where status >= 400 AND status < 500
$http_5xx = from $base | where status >= 500 AND status < 600
$by_host = from $http_5xx | stats count() AS errors by host
```

This is cleaner than repeatedly cloning pipelines.

### 13.3 Pattern: Prefer views for shared curation layers

Use views when multiple teams need a stable, reviewed data abstraction over the same raw source.

### 13.4 Pattern: Keep dynamic field generation rare

Field templates are powerful, but they increase downstream ambiguity. Prefer stable schemas unless dynamic fields are the point.

### 13.5 Pattern: Treat compatibility as part of design

A query is not "done" when it parses. It is done when it is valid in the intended SPL2 profile.

## 14. Anti-Patterns

- Writing module code as though it were Search bar code
- Assuming all string-like values can stay unquoted
- Assuming all fields can stay unquoted
- Using `spl1` as a permanent replacement for learning SPL2
- Ignoring compatibility profiles
- Overusing wildcards, especially broad raw-event scans
- Building unreadable queries when modules and named searches would simplify them
- Generating dynamic field names where stable schema would be better

## 15. A Short SPL2 Starter Kit

If you are onboarding a developer to SPL2, these are the pages to read first in order:

1. What is SPL2?
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/what-is-spl2
2. What is new and different in SPL2?
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/what-is-new-and-different-in-spl2-
3. Specific differences between SPL and SPL2
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/specific-differences-between-spl-and-spl2
4. Understanding SPL2 syntax
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/introduction/understanding-spl2-syntax
5. Start searching data using SPL2
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/getting-started/quick-start-write-and-run-a-basic-spl2-search/start-searching-data-using-spl2
6. `from` command overview
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/from-command/from-command-overview
7. `eval` command overview and usage
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/eval-command/eval-command-overview-and-syntax
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/eval-command/eval-command-usage
8. `stats` command overview
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/stats-command/stats-command-overview-syntax-and-usage
9. Modules and branching
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/spl2-modules-and-statements
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/branching-spl2-searches
10. Compatibility profiles
   https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references

## 16. Final Takeaways

SPL2 is best understood as a language family with a resource model, not merely as "new SPL syntax".

For developers, the main changes that matter are:

- think in datasets and modules
- choose `search` versus `from` deliberately
- learn the quoting and expression rules early
- treat compatibility profiles as hard constraints
- use branching and views to avoid copy-paste query design
- use `spl1` tactically, not as the default path

If you adopt those habits, SPL2 becomes much easier to reason about, review, and reuse than a large body of one-off SPL.
