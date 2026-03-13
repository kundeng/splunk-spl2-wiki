# SPL2 Scenario Cookbook

This document is designed for repository ingestion and retrieval-oriented use. It favors short scenarios, compact explanations, and concrete SPL2 snippets over long narrative.

Primary sources were downloaded from Splunk Help into this repo under:

- `research/extracted/`
- `research/raw/`
- `research/index/manifest.json`

## How To Use This File

- Start with the scenario that matches the task.
- Copy the snippet and adapt dataset names, field names, and time filters.
- Check compatibility before reuse across products.

## Compatibility First

SPL2 is documented as product-agnostic, but command and function availability depends on compatibility profiles.

Check these before assuming a snippet is portable:

- `splunkd`
- `edgeProcessor`
- `ingestProcessor`

Key sources:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references/compatibility-quick-reference-for-spl2-commands
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl2-compatibility-profiles-and-quick-references/compatibility-quick-reference-for-spl2-evaluation-functions

## Scenario: Start A Basic Search

Use `search` for SPL-style syntax.

```spl
search index=main
```

Use `from` for SQL-style syntax.

```spl
FROM main
SELECT *
```

When using the Search bar, `search` can be implied for `index=<name>` style queries.

```spl
index=main status=200
```

In a module, be explicit and name the search.

```spl
$base = search index=main status=200
```

## Scenario: Filter Events By Field Values

SPL-style:

```spl
search index=main status=200 host=www2
| fields _time, host, status, productId
```

SQL-style:

```spl
FROM main
WHERE status=200 AND host="www2"
SELECT _time, host, status, productId
```

## Scenario: Search Raw Terms

If the search starts with raw terms instead of `index=<name>`, include `search`.

```spl
search 404 index=main
```

Using a search literal in `WHERE`:

```spl
FROM main
WHERE `invalid user sshd[5258]`
SELECT _time, source, host
```

## Scenario: Aggregate Counts By Field

```spl
search index=main status=200
| stats count() AS event_count by host
```

```spl
FROM main
WHERE status=200
GROUP BY host
SELECT host, count() AS event_count
```

## Scenario: Sum A Numeric Field

```spl
search index=main sourcetype="access_*"
| stats sum(bytes) AS total_bytes by clientip
```

```spl
FROM main
WHERE sourcetype="access_*"
GROUP BY clientip
SELECT clientip, sum(bytes) AS total_bytes
```

## Scenario: Compute A Derived Field

Use `eval` to create or overwrite fields.

```spl
search index=main
| eval kb=bytes/1024
| fields _time, host, bytes, kb
```

Multiple expressions can be chained left to right:

```spl
search index=main
| eval kb=bytes/1024, mb=kb/1024, tier=if(mb > 10, "large", "small")
```

## Scenario: Filter With `where`

```spl
search index=main
| where status IN ("400", "401", "403", "404")
```

```spl
search index=main
| where like(uri_path, "/api/%")
```

## Scenario: Use `from` Clauses In Order

The `from` command supports optional clauses, but ordering matters.

```spl
FROM main
WHERE earliest=-15m@m AND sourcetype="access_*"
GROUP BY host
SELECT host, sum(bytes) AS total_bytes
ORDER BY total_bytes DESC
LIMIT 20
```

Equivalent form starting with `SELECT`:

```spl
SELECT host, sum(bytes) AS total_bytes
FROM main
WHERE earliest=-15m@m AND sourcetype="access_*"
GROUP BY host
ORDER BY total_bytes DESC
LIMIT 20
```

## Scenario: Rename Output Fields

Field aliases that contain spaces or special characters need single quotes.

```spl
search index=main
| stats sum(bytes) AS 'Sum of bytes' by host
```

```spl
FROM main
GROUP BY host
SELECT host, sum(bytes) AS 'Sum of bytes'
```

## Scenario: Quote Field Names Correctly

Use single quotes around field names that:

- contain spaces
- contain dashes
- contain wildcard characters
- start with a non-letter

Examples:

```spl
... | eval 'low-category' = lower(categoryId)
... | stats max(size) AS 'max.size'
FROM main WHERE '5minutes'="late"
SELECT 'host*' FROM main
```

## Scenario: Quote String Values Correctly

In SPL2, string literals generally use double quotes.

```spl
FROM main
WHERE sourcetype="access_*" AND host="www2"
SELECT _time, host, sourcetype
```

## Scenario: Use Wildcards

In `where` and `eval`, use `like()` patterns with `%` and `_`.

```spl
... | where like(source, "license%")
```

In many other commands, use `*`.

```spl
search sourcetype="access_*"
```

Avoid unbounded wildcards:

```spl
search *
```

That is valid but usually inefficient.

## Scenario: Escape Special Characters

Use backslash escapes when necessary:

```spl
FROM main
WHERE message="path C:\\windows\\temp"
SELECT _time, message
```

Prefer search literals when the goal is term search:

```spl
FROM main
WHERE `user "ladron" from 192.0.2.0/24`
SELECT _time, host, source
```

## Scenario: Concatenate Strings

SPL2 uses `+`, not `.`.

```spl
search index=main
| eval full_name=first_name + " " + last_name
```

## Scenario: Use Boolean Logic Safely In `eval`

The docs note that `eval` cannot directly assign a Boolean value. Wrap Boolean expressions in a function such as `if()`.

```spl
search index=main
| eval is_server_error=if(status IN ("500", "503"), "true", "false")
```

## Scenario: Count Matching Conditions Inside `stats`

```spl
search index=main
| stats count(status="404") AS count_404 by host
```

```spl
search index=main
| stats count(method="GET") AS get_requests by endpoint
```

## Scenario: Sort Results

```spl
search index=main status=500
| stats count() AS errors by host
| sort - errors
```

## Scenario: Remove Duplicate Rows

Lists are comma-separated in SPL2.

```spl
search index=main
| dedup 2 source, host
```

## Scenario: Keep Only A Few Fields

```spl
search index=main status=200
| fields _time, host, action, productId
```

## Scenario: Build A Time Series

```spl
search index=main sourcetype="access_*"
| timechart count() by status
```

```spl
search index=main sourcetype="access_*"
| timechart sum(bytes) AS total_bytes
```

## Scenario: Compute Running Statistics

```spl
search index=main
| sort _time
| streamstats window=3 avg(bytes) AS moving_avg_bytes
```

```spl
search index=main
| streamstats sum(bytes) AS running_total
```

## Scenario: Parse JSON-Like Structures

Create array and object literals:

```spl
... | eval arr=["low", "medium", "high"]
```

```spl
... | eval meta={env: "prod", owner: "payments"}
```

Use arrays with expressions:

```spl
... | eval a=10, value=[[1,2,3], a+2]
```

## Scenario: Format Output With String Templates

```spl
... | eval summary="status=${status} action=${action} host=${host}"
```

Useful when formatting messages without long `+` chains.

## Scenario: Generate Dynamic Field Names

Use field templates sparingly.

```spl
SELECT * FROM [{city: "Seattle", Seattle: 123}]
| eval '${city}' = 456
```

This is powerful, but stable schemas are usually easier to maintain.

## Scenario: Filter With Predicates

Examples of common predicate forms:

```spl
... | where count > 15
```

```spl
... | where customer_name IS string
```

```spl
... | where host IS NULL
```

```spl
... | where ipaddress LIKE "198.%"
```

```spl
FROM main
HAVING ipaddress BETWEEN "192.0.2.0" AND "192.0.2.255"
SELECT host, ipaddress, count() AS c
GROUP BY host, ipaddress
```

## Scenario: Create A Reusable Base Search In A Module

```spl
$base = search index=main sourcetype="access_*"
$errors = from $base | where status >= 500 AND status < 600
$top_hosts = from $errors | stats count() AS errors by host | sort - errors
```

This is one of the main SPL2 improvements over repeated one-off pipelines.

## Scenario: Branch Searches For Investigation

```spl
$base_search = from main where status=200
$child1 = from $base_search
where categoryId LIKE("S%") AND host="www3"
select _time, action, productId, categoryId
$child2 = from $child1 where action!="NULL"
$child3 = from $child2
| stats count() by categoryId
```

Use this pattern when you want to inspect the state of data at multiple narrowing stages.

## Scenario: Export A View

Conceptually, a view is a named exported search that other modules can reuse.

Base example:

```spl
$countByHost = from main | stats count() by host
$tophosts = from $countByHost | sort - count | head 3
```

Use views when a search result shape should become shared infrastructure instead of local logic.

## Scenario: Use Namespaces And Imports

Namespaces matter when:

- multiple teams share modules
- names can collide
- app-packaged SPL2 resources need clear ownership

Rule of thumb:

- local exploration: keep resources in one module
- shared usage: move common resources into stable namespaces and import them explicitly

See:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/export-import-and-namespaces/understanding-spl2-namespaces

## Scenario: Migrate An SPL Search To SPL2

Original SPL-style pattern:

```spl
index=main sourcetype=access_* status=200
| stats count by host
```

SPL2 Search bar form:

```spl
index=main sourcetype="access_*" status=200
| stats count() by host
```

SPL2 module form:

```spl
$count_by_host = search index=main sourcetype="access_*" status=200
| stats count() by host
```

SPL2 SQL-style form:

```spl
FROM main
WHERE sourcetype="access_*" AND status=200
GROUP BY host
SELECT host, count() AS count
```

Migration checks:

- add commas in lists
- normalize quoting
- replace `.` concatenation with `+`
- review Boolean expressions in `eval`
- confirm target profile compatibility

## Scenario: Use `spl1` For Unsupported SPL

If a needed SPL command is not directly supported in SPL2, `spl1` can embed SPL in eligible contexts.

Example pattern:

```spl
from main
| append [search action="purchase" | `top 1 clientip BY categoryId`]
```

Use this as a bridge during migration, not as the first design choice.

See:

- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/using-spl-commands-in-spl2-searches
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/spl1-command

## Scenario: Choose Between Search Bar And Module Editor

Use Search bar for:

- ad hoc exploration
- one statement
- disposable work

Use Module editor for:

- named searches
- branching
- reusable logic
- custom functions
- custom data types
- imports and exports
- shared views

## Scenario: Common Syntax Fixes During Review

Fix missing commas:

```spl
... | dedup 2 source, host
```

Fix option order:

```spl
... | bin bins=10 size as bin_size
```

Fix field quoting:

```spl
... | eval 'low-user' = lower(username)
```

Fix string quoting:

```spl
FROM main WHERE user="ladron"
```

Fix concatenation:

```spl
... | eval full_name=first_name + " " + last_name
```

## Scenario: Review Checklist For Production SPL2

- Is the runtime target known?
- Does the query use commands supported in that compatibility profile?
- Is Search bar syntax being incorrectly reused in a module?
- Are string literals double-quoted?
- Are special field names single-quoted?
- Are field lists comma-separated?
- Are search names stable and readable?
- Would a base search plus branches improve maintainability?
- Should shared logic become a view?
- Is `spl1` being used only where necessary?

## More Command Examples

This section surfaces additional command-specific examples from the SPL2 Search Reference example pages.

### Append rows from a subsearch

```spl
from <dataset>
| where action="purchase"
| sort clientip
| stats dc(clientip) BY categoryId
| append [search action="purchase" | `top 1 clientip BY categoryId`]
```

### Append columns from a subsearch

```spl
from main
| fields host
| appendcols [search 404]
```

### Append subtotal rows inline

```spl
from main
| stats count() AS user_count BY action, clientip
| appendpipe [stats sum(user_count) AS 'User Count' BY action | eval user="TOTAL - USER COUNT"]
| sort action
```

### Bin values into time buckets

```spl
... | bin span=5m _time | stats avg(thruput) by _time, host
```

Alternative:

```spl
... | stats avg(thruput) by span(_time, 5m), host
```

### Bin values into fixed numeric buckets

```spl
... | bin bins=10 size AS bin_size | stats count(_raw) BY bin_size
```

### Branch data into multiple outputs

```spl
from cities
| branch
  [ where population < 10000 | stats count() BY name | into villages ],
  [ where population >= 10000 AND population <= 1000000 | stats count() by name | into towns ],
  [ where population > 1000000 | stats count() by name | into cities ]
```

### Add aggregate context to every row with `eventstats`

```spl
... | eventstats avg(duration) AS avgdur
```

Grouped version:

```spl
... | eventstats avg(duration) AS avgdur BY date_minute
```

### Detect spikes against an average

```spl
search eventtype="error"
| eventstats avg(status) AS avg
| where status > avg
```

### Remove fields

```spl
... | fields - host, ip
```

Remove internal fields:

```spl
... | fields host, ip | fields - '_*'
```

### Fill missing values

```spl
... | fillnull
```

```spl
... | fillnull value="NULL"
```

```spl
... | fillnull value="unknown" host, kbps
```

### Flatten an object field

```spl
FROM [{}]
SELECT _time, {name: "Helix Bridge", length: 918, country: "Singapore"} AS bridges
| flatten bridges
```

### Limit rows with `head`

```spl
... | head keeplast=true 123 while (timestamp > 2020 AND error == 1.2)
```

```spl
... | head while (isnull(host) OR host="localhost") 50
```

### Join datasets on matching field names

```spl
... | join left=L right=R where L.product_id=R.product_id [from vendors]
```

### Join datasets on different field names

```spl
... | join left=L right=R where L.product_id=R.pid [from ~/'search'/lookups/suppliers]
```

Return all matches from the right side:

```spl
... | join max=0 left=L right=R where L.vendor_id=R.vid [from products]
```

### Enrich events from a lookup

```spl
... | lookup users uid OUTPUTNEW username, department
```

Map different field names:

```spl
... | lookup addresses CustID AS cid OUTPUT CustAddress AS cAddress
```

### Expand multivalue fields

```spl
... | mvexpand c
```

Limit the expansion:

```spl
... | mvexpand limit=10 my_mvfield
```

Pipeline-style extraction plus expansion:

```spl
$pipeline = from $source
| rex field=_raw max_match=0 /(?P<iplist>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/
| mvexpand iplist
| into $destination
```

### Rename fields

```spl
... | rename usr AS username
```

```spl
... | rename 'ip-add' AS IPAddress
```

```spl
... | rename usr AS username, dpt AS department
```

Wildcard rename:

```spl
... | rename 'u*' AS 'user*'
```

### Replace values

Replace across all fields:

```spl
... | replace str="*localhost" replacement="localhost"
```

Replace in a specific field:

```spl
... | replace str="127.0.0.1" replacement="localhost" host
```

Replace in multiple fields:

```spl
... | replace str="aug" replacement="August" start_month, end_month
```

### Extract with regex

Mask card numbers:

```spl
... | rex field=ccnumber mode=sed "s/(\\d{4}-){3}/XXXX-XXXX-XXXX-/g"
```

Named capture with escaped backslashes:

```spl
... | rex field=clientip "(?<ipclass>\\d+)"
```

Named capture with slash delimiters:

```spl
... | rex field=clientip /(?<ipclass>\d+)/
```

Pipeline extraction:

```spl
$pipeline = from $source
rex field=_raw /(?P<httpcode>[1-5][0-9][0-9])/
| into $destination
```

### Sort with mixed directions

```spl
... | sort lastname, -firstname
```

Limit sorted output:

```spl
... | sort 100 -size, +source
```

Typed sort:

```spl
... | sort ip(ipaddress), -str(url)
```

### Extract nested JSON or XML with `spath`

```spl
... | spath output=myfield path="server.name"
```

```spl
... | spath output=commit_author path="commits{}.author.name"
```

```spl
... | spath output="locDesc.locale" path="vendorProductSet.product.desc.locDesc{@locale}"
```

### Build output tables

```spl
... | table host, action
```

```spl
... | table host, action, "source*"
```

### Build timecharts

```spl
... | timechart span=1h count() by host
```

```spl
... | timechart span=1m avg(CPU) BY host
```

```spl
... | timechart span=1m eval(avg(CPU) * avg(MEM)) BY host
```

```spl
... | timechart eval(round(avg(cpu_seconds), 2)) BY processor
```

### Compare periods with `timewrap`

```spl
... | timechart count span=1d | timewrap 1week
```

### Use `tstats` on indexed or accelerated data

```spl
| tstats aggregates=[count()]
```

```spl
| tstats aggregates=[min(_time) AS min] predicate=(index=myindex)
```

```spl
| tstats aggregates=[count()] datamodel_name='NetworkTraffic.emea'
```

```spl
| tstats aggregates=[avg(bytes)] predicate=(index=sample_events AND host="www3")
```

### Merge datasets with `union`

```spl
union customers, orders, vendors_lookup
```

Embedded in `FROM`:

```spl
FROM [union customers, orders, vendors_lookup] WHERE ...
```

Union incoming results with another dataset:

```spl
from mysecurityview
| fields _time, clientip
| union customers
```

### Convert tabular results back to rows

```spl
from main
where status=200
| stats count() by host, status
| untable host, label, data
```

## High-Value Reference Pages

- What is SPL2?
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/what-is-spl2
- Specific differences between SPL and SPL2
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/specific-differences-between-spl-and-spl2
- Understanding SPL2 syntax
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/introduction/understanding-spl2-syntax
- Start searching data using SPL2
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/getting-started/quick-start-write-and-run-a-basic-spl2-search/start-searching-data-using-spl2
- `from` command overview
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/from-command/from-command-overview
- `search` command overview
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/search-command/search-command-overview-and-syntax
- `eval` command overview and usage
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/eval-command/eval-command-overview-and-syntax
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/eval-command/eval-command-usage
- `stats` command overview
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/stats-command/stats-command-overview-syntax-and-usage
- Modules and branching
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/spl2-modules-and-statements
  https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/branching-spl2-searches
