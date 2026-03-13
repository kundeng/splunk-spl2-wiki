# SPL2 for Developers

This guide is the architectural and language-level reference for the `spl2-context7` skill. It is written for engineers who need to author SPL2 deliberately, review it rigorously, and structure reusable SPL2 assets instead of treating queries as one-off search bar fragments.

The tutorial is self-contained on purpose. It explains the SPL2 model, the grammar choices that matter in practice, the expression system, reuse mechanisms, compatibility constraints, and the migration traps that routinely break otherwise competent SPL authors.

## 1. Start With The Real Execution Context

The first SPL2 design question is not syntax. It is runtime.

SPL2 appears in different products and authoring surfaces:

- Search bar for ad hoc searches
- SPL2 module editor for named, reusable statements
- App development on the `splunkd` profile
- Edge Processor and Ingest Processor with narrower compatibility profiles

Those contexts are not interchangeable.

### 1.1 Search bar

Use the search bar when you are writing a single disposable statement. The search bar is the least structured environment and preserves some convenience behavior:

- `index=main status=200` can imply `search`
- raw-term-first searches still require `search`
- there is no module packaging, import/export, or branching structure

```spl
index=main status=200
```

```spl
search 404 index=main
```

### 1.2 Module editor

Use a module when the query needs a name, branching, export, imports, custom functions, custom data types, or code review.

Module rules matter:

- search statements are named
- generating commands are explicit
- branching is first-class
- views and reusable resources become possible

```spl
$base = search index=main status=200
$errors = from $base where status >= 400
```

### 1.3 Compatibility profile

Before you optimize for elegance, verify what actually runs:

- `splunkd`
- `edgeProcessor`
- `ingestProcessor`

The same SPL2 surface is not available everywhere. A review that ignores profile compatibility is incomplete even if the syntax is otherwise valid.

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/where-can-i-use-spl2
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references

## 2. SPL2 Is A Language Family, Not Just “New SPL”

SPL2 is easiest to reason about when you separate four layers:

1. Dataset layer: where the data comes from
2. Search layer: how records are filtered, transformed, and aggregated
3. Expression layer: how values are computed
4. Reuse layer: how searches, functions, views, and types are packaged

Traditional SPL users often focus only on the search layer. That is why many migrations feel awkward. SPL2 adds a real expression language and a real reuse model.

### 2.1 Dataset model

In SPL2, a dataset can be:

- an index
- a lookup
- a view
- a named search result
- a dataset literal
- a dataset function such as `repeat()`

That model is why `from` is central. It treats the data source explicitly.

### 2.2 Bimodal query style

SPL2 supports both pipeline-heavy SPL-style authoring and clause-oriented SQL-style authoring.

SPL-style:

```spl
search index=main status=200
| eval kb=bytes/1024
| stats avg(kb) AS avg_kb by host
```

SQL-style:

```spl
FROM main
WHERE status=200
GROUP BY host
SELECT host, avg(bytes/1024) AS avg_kb
```

Hybrid style is normal:

```spl
FROM main
WHERE sourcetype="access_*"
SELECT _time, host, status, bytes
| eval kb=round(bytes/1024, 2)
| stats avg(kb) AS avg_kb by host, status
```

The right question is not “which style is more correct?” It is “which style makes the intent obvious for this team and this runtime?”

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/introduction/understanding-spl2-syntax
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/from-command/from-command-overview

## 3. Grammar Rules That Matter In Real Reviews

Most SPL2 bugs are not exotic. They come from repeatedly missing a small set of grammar rules.

### 3.1 Strings use double quotes

```spl
FROM main
WHERE host="www2" AND sourcetype="access_*"
SELECT _time, host
```

### 3.2 Field names with special characters use single quotes

Use single quotes around field names that contain spaces, dots, dashes, wildcards, or leading non-letters.

```spl
... | eval 'low-category' = lower(categoryId)
... | stats max(size) AS 'max.size' by host
FROM main WHERE '5minutes'="late"
```

### 3.3 Search literals use backticks

Search literals are not just decoration. They let you embed term-style searching or unsupported SPL fragments where expressions are allowed.

```spl
FROM main
WHERE `invalid user sshd[5258]`
SELECT _time, source, host
```

```spl
$top_referrers = from main where host="www3" | `top limit=20 referer`
```

### 3.4 Lists are comma-separated

SPL2 is stricter and more regular about lists than SPL.

```spl
search index=main
| fields _time, host, status
| stats count() by host, status
```

### 3.5 Command options come before command arguments

This is a habitual SPL migration failure.

```spl
... | bin span=5m _time
```

### 3.6 Wildcards depend on context

- `like()` with `%` and `_` in `where` and expression contexts
- `*` in many command arguments

```spl
... | where like(uri_path, "/api/%")
search sourcetype="access_*"
```

### 3.7 `search` has different syntax rules from expression contexts

This distinction is easy to miss:

- `where`, `eval`, `SELECT`, and `HAVING` use expression rules
- `search` uses search syntax

That is why code that works in `search` often cannot simply be pasted into `where` unchanged.

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/wildcards-quotes-and-escape-characters/quotation-marks
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/types-of-expressions

## 4. Expressions Are The Real Core Of SPL2

If you only remember one thing about SPL2, remember this: the language is expression-driven.

Expressions produce values. They are used in:

- `eval`
- `where`
- `SELECT`
- `GROUP BY span(...)`
- function arguments
- templates
- object and array construction

### 4.1 Literal types you should actively use

SPL2 supports more than simple string and numeric literals:

- strings: `"hello"`
- raw strings: `@"C:\windows\temp"`
- numbers: `42`, `3.14`
- booleans: `true`, `false`
- null
- arrays: `["a", "b", 3]`
- objects: `{host:"www1", status:200}`

Example:

```spl
FROM repeat({}, 1)
SELECT
  "hello" AS s,
  @"C:\windows\temp" AS raw_path,
  [1,2,3] AS nums,
  {host:"www1", status:200} AS obj
```

### 4.2 Predicate expressions

Predicates are boolean expressions used for filtering.

```spl
... | where status in("400", "401", "403", "404")
... | where bytes > 1024 AND like(uri_path, "/api/%")
FROM main WHERE host="www2" OR host="www3" SELECT *
```

Predicate operators you should expect in reviews:

- relational: `=`, `!=`, `<`, `>`, `<=`, `>=`
- logical: `AND`, `OR`, `NOT`, `XOR`
- conditional/pattern functions: `in`, `like`, `match`, `searchmatch`, `cidrmatch`

### 4.3 Arrays and objects

Arrays and objects are not edge features. They are central to JSON-heavy data handling and reusable computed structures.

```spl
... | eval dims=["region", "host", "service"]
... | eval record={host:host, status:status, kb:round(bytes/1024, 2)}
```

### 4.4 Access expressions

Use `[]` for array access and `.` or `[]` for object access.

```spl
... | eval third_game=games[2]
... | eval owner=record.host
... | eval severity=alert["level"]
```

### 4.5 String templates

Use string templates when concatenation would make the intent harder to read.

```spl
... | eval status_info="${host} returned ${status} for ${action}"
```

### 4.6 Field templates

Field templates generate field names dynamically. They are powerful and easy to misuse. Keep them constrained and obvious.

```spl
SELECT * FROM [{city:"Seattle", Seattle:123}]
| eval '${city}' = 456
```

### 4.7 Lambda expressions

Lambdas show up primarily in JSON functions such as `map`, `filter`, `all`, `any`, and `reduce`.

```spl
... | eval numbers=json_array(1,2,3,4)
... | eval doubled=map(numbers, x -> x * 2)
... | eval evens=filter(numbers, x -> x % 2 = 0)
```

If you use block-style lambdas, keep them short:

```spl
... | eval total=reduce(numbers, (acc, x) -> { return acc + x })
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/types-of-expressions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/lambda-expressions

## 5. Choose `search` And `from` Deliberately

Many weak SPL2 codebases bounce randomly between `search` and `from`. Treat them as different tools.

### 5.1 Prefer `search` when

- you are migrating classic SPL
- you want raw search semantics
- the team already reasons in pipelines
- the search is mostly command chaining

```spl
search index=main status=200 host=www2
| fields _time, host, status, bytes
| where bytes > 4096
| stats sum(bytes) AS total_bytes by host
```

### 5.2 Prefer `from` when

- the dataset should be explicit
- the query reads better as clauses
- you want `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`, `HAVING`, `SELECT`
- the team has SQL instincts

```spl
FROM main
WHERE status=200 AND host="www2"
GROUP BY host
SELECT host, sum(bytes) AS total_bytes
ORDER BY total_bytes DESC
LIMIT 20
```

### 5.3 `from` clause order matters

The common mental model is:

1. dataset
2. filtering
3. grouping
4. projection
5. ordering
6. limiting

```spl
FROM main
WHERE earliest=-15m@m AND sourcetype="access_*"
GROUP BY host
SELECT host, avg(bytes) AS avg_bytes
ORDER BY avg_bytes DESC
LIMIT 10
```

### 5.4 Hybrid queries are often the most maintainable

```spl
FROM main
WHERE sourcetype="access_*"
SELECT _time, host, status, bytes
| eval kb=round(bytes/1024, 2)
| eventstats avg(kb) AS global_avg
| where kb > global_avg
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/from-command/from-command-syntax
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/search-command/search-command-overview-and-syntax

## 6. Understand Command Families, Not Just Single Commands

SPL2 reviews get stronger when you recognize command roles.

### 6.1 Generating commands

These create the starting dataset.

- `search`
- `from`
- `join`
- `union`
- dataset functions such as `repeat()`

### 6.2 Filtering commands

- `where`
- `WHERE` clause
- search literals

### 6.3 Evaluation and shaping

- `eval`
- `fields`
- `rename`
- `replace`
- `spath`
- `rex`

### 6.4 Aggregation and charting

- `stats`
- `eventstats`
- `streamstats`
- `timechart`

### 6.5 External enrichment and composition

- `lookup`
- `join`
- `append`
- `appendcols`
- `appendpipe`
- `union`

That family-level framing is more useful than memorizing commands one at a time.

## 7. Aggregation In SPL2 Is Richer Than Basic `stats`

Most SPL2 content stops at `count()` and `sum()`. That is not enough for developers.

### 7.1 Aggregate functions

You should be comfortable with:

- `avg`, `sum`, `min`, `max`, `range`
- `count`, `distinct_count`, `estdc`
- `median`, `mode`, `perc`, `upperperc`
- `stdev`, `stdevp`, `var`, `varp`

```spl
search index=main
| stats count() AS events, distinct_count(host) AS hosts, avg(bytes) AS avg_bytes by sourcetype
```

### 7.2 Eval inside statistical functions

This is a high-value SPL2 idiom:

```spl
... | stats count(eval(status="404")) AS not_found by sourcetype
```

Instead of precomputing a field, you can embed the expression directly.

### 7.3 Time functions for aggregation

Use chart/time functions deliberately:

```spl
... | timechart span=5m sum(bytes) BY host
... | stats earliest(_time) AS first_seen, latest(_time) AS last_seen by user
```

### 7.4 Event-order functions

`first()` and `last()` are not the same as min/max. They depend on event order.

```spl
... | streamstats first(status) AS first_status, last(status) AS last_status by session_id
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/statistical-and-charting-functions/overview-of-spl2-stats-and-chart-functions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/stats-command/stats-command-overview-syntax-and-usage

## 8. Modules, Branching, Views, Namespaces

This is the part of SPL2 that makes it suitable for real engineering work.

### 8.1 Modules are the unit of reuse

A module can contain:

- imports
- named searches
- custom functions
- custom data types
- exports

Treat a module like a source file, not a notebook cell.

### 8.2 Branching replaces copy-paste pipelines

```spl
$base = from main where sourcetype="access_*"

$errors = from $base where status >= 400
$success = from $base where status < 400

$error_summary = from $errors group by host select host, count() AS errors
$success_summary = from $success group by host select host, count() AS successes
```

This is structurally better than repeating the same initial filter in four separate searches.

### 8.3 Views expose stable search interfaces

Views are exported named searches. They are a good boundary when:

- raw indexes are too noisy
- business logic should be centralized
- teams need curated datasets

### 8.4 Namespaces matter for packaging

Namespaces solve two problems:

- naming collisions
- reusable imports across apps and teams

If you expect a search, function, or view to be shared, design the namespace story early rather than retrofitting it after duplication spreads.

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/spl2-modules-and-statements
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/export-import-and-namespaces/understanding-spl2-namespaces

## 9. Custom Functions And Custom Data Types

Most teams never reach this layer, but it is where SPL2 becomes a language platform rather than a query syntax.

### 9.1 Custom functions

Reach for a custom function when:

- the same expression logic repeats across modules
- the logic is domain-specific
- inline `eval` expressions are becoming unreadable

Do not use custom functions as a reflex. They should reduce duplication or sharpen domain meaning.

### 9.2 Built-in vs custom

The safe order is:

1. built-in function
2. clear inline expression
3. custom function

If built-ins already express the logic clearly, wrapping them can hurt readability.

### 9.3 Custom data types

Custom data types matter when:

- your data has a schema worth naming
- you want stronger, documented field expectations
- modules share structured objects

This is one of the least-used but most architecture-relevant SPL2 features.

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/functions/built-in-and-custom-functions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/data-types/custom-data-types

## 10. Compatibility And Portability Strategy

Portability is not free. If the query may run outside `splunkd`, review it with this checklist:

- Does every command exist in the target profile?
- Does every function exist in the target profile?
- Are modules/views supported in the same way?
- Is the query relying on `spl1` as a bridge?
- Is there a simpler, more portable expression alternative?

### 10.1 `spl1` is a bridge, not a destination

If a migration temporarily needs unsupported SPL:

```spl
$legacy = from main where host="www3" | `top limit=20 referer`
```

That can be acceptable during migration. It should not become the default authoring style.

### 10.2 Prefer portable idioms

Prefer:

- explicit quoting
- `where` predicates over ambiguous search syntax
- built-in functions over opaque search literals
- simpler aggregates over clever but brittle one-liners

## 11. Migration Patterns That Actually Matter

The highest-value migration changes are structural, not cosmetic.

### 11.1 Replace SPL habits that no longer fit

- space-separated lists -> comma-separated lists
- bare single-quoted strings -> double-quoted strings
- ad hoc field quoting -> deliberate single-quoted field names
- implicit search-bar behavior -> explicit module statements

### 11.2 Re-evaluate old pipeline structure

A good SPL2 rewrite often:

- moves filtering into `WHERE`
- moves shaping into `SELECT`
- introduces a base named search
- uses branching instead of duplicate pipelines

### 11.3 Do not port ambiguity

If the original SPL relies on parser tolerance, undocumented shortcuts, or positional weirdness, treat that as technical debt to remove during migration.

## 12. Code Review Checklist For SPL2

Use this checklist in reviews:

- Is the runtime context correct: search bar, module editor, or another profile?
- Is `search` vs `from` a deliberate choice?
- Are strings double-quoted and special field names single-quoted?
- Are lists comma-separated?
- Are command options before command arguments?
- Are expression contexts separated correctly from search syntax contexts?
- Are search literals used only where they clarify intent or bridge missing support?
- Is branching used where repeated pipelines share the same base dataset?
- Are functions/profile compatibility constraints respected?
- Is the query readable enough that another engineer could safely extend it?

## 13. Recommended Reading Order Inside This Skill

Use this guide for mental models and design choices.

Then use:

- `spl2-context7-cookbook.md` for scenario-first snippets
- `spl2-grammar-and-functions-reference.md` for lookup-style grammar and function examples

The cookbook tells you how to solve common tasks. The grammar/functions reference tells you what the language surface actually is.
