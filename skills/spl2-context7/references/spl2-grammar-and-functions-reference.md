# SPL2 Grammar And Functions Reference

This document is the lookup-oriented language reference for the `spl2-context7` skill. It is intentionally compact, self-contained, and example-heavy. Use it when you need the shape of SPL2 syntax or a quick example of a built-in function family.

This file is organized by language surface:

1. grammar primitives
2. query forms
3. expression forms
4. module-level constructs
5. function catalog by family

## 1. Core Grammar Primitives

### 1.1 Query styles

SPL2 supports two primary entry forms:

```spl
search index=main status=200
```

```spl
FROM main
WHERE status=200
SELECT *
```

Hybrid form is valid:

```spl
FROM main
WHERE status=200
SELECT host, bytes
| eval kb=round(bytes/1024, 2)
| stats avg(kb) by host
```

### 1.2 Lists

Use commas in field lists, argument lists, and grouping lists.

```spl
... | fields _time, host, status
... | stats count() by host, status
```

### 1.3 Quotes

- string literal: `"www2"`
- special field name: `'low-category'`
- search literal: `` `invalid user sshd[5258]` ``

```spl
FROM main WHERE host="www2" SELECT 'host*'
```

### 1.4 Wildcards

- `*` in many command arguments
- `%` and `_` inside `like()`

```spl
search sourcetype="access_*"
... | where like(uri_path, "/api/%")
```

### 1.5 Grouped and repeating arguments

Representative patterns:

```spl
... | bin span=5m _time
... | rename host AS src_host, source AS src_file
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/introduction/understanding-spl2-syntax
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/wildcards-quotes-and-escape-characters/quotation-marks

## 2. Query Grammar

### 2.1 `search`

Search syntax is best for classic SPL-style pipelines.

```spl
search index=main status=200 host=www2
| fields _time, host, status
| stats count() by host
```

Search bar convenience:

```spl
index=main status=200
```

Raw-term-first form must be explicit:

```spl
search 404 index=main
```

### 2.2 `from`

Clause-oriented form:

```spl
FROM main
WHERE sourcetype="access_*"
GROUP BY host
SELECT host, avg(bytes) AS avg_bytes
ORDER BY avg_bytes DESC
LIMIT 20
```

Equivalent `SELECT`-first form:

```spl
SELECT host, avg(bytes) AS avg_bytes
FROM main
WHERE sourcetype="access_*"
GROUP BY host
ORDER BY avg_bytes DESC
LIMIT 20
```

### 2.3 `where`

Expression-driven filtering:

```spl
... | where status in("400", "401", "403", "404")
... | where bytes > 1024 AND like(uri_path, "/api/%")
... | where cidrmatch("10.0.0.0/8", clientip)
```

### 2.4 `eval`

Compute or overwrite fields:

```spl
... | eval kb=bytes/1024
... | eval kb=bytes/1024, mb=kb/1024, tier=if(mb > 10, "large", "small")
```

### 2.5 `stats`, `eventstats`, `streamstats`, `timechart`

```spl
... | stats count() AS events by host
... | eventstats avg(bytes) AS global_avg
... | streamstats count() AS row_number by host
... | timechart span=5m sum(bytes) BY host
```

### 2.6 Composition commands

```spl
... | append [ search index=secondary ]
... | appendcols [ search index=secondary | stats count() AS other_count ]
... | appendpipe [ stats count() AS subtotal by host ]
... | union [ search index=west ] [ search index=east ]
```

### 2.7 Enrichment and extraction

```spl
... | lookup geo_by_ip clientip OUTPUT country, region
... | rex field=_raw "user=(?<user>\\w+)"
... | spath input=payload path=event.user output=user
... | rename host AS server_name
... | replace "404" WITH "not_found" IN status
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/search-command/search-command-overview-and-syntax
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/from-command/from-command-syntax

## 3. Expression Grammar

### 3.1 Scalar literals

```spl
"hello"
@"C:\windows\temp"
42
3.14
true
false
null
```

### 3.2 Array literals

```spl
... | eval dims=["region", "host", "service"]
... | eval nested=[[1,2,3], 4, "x"]
```

### 3.3 Object literals

```spl
... | eval obj={host:host, status:status, metrics:{kb:round(bytes/1024, 2)}}
```

### 3.4 Access expressions

```spl
... | eval city=locations[0]
... | eval owner=record.owner
... | eval severity=alert["level"]
... | eval coop=games.category.boardgames.cooperative[1]
```

### 3.5 Predicate expressions

```spl
status = 200
status != 404
bytes > 1024
host="www2" AND status >= 500
status in("400", "401", "403", "404")
like(uri_path, "/api/%")
match(_raw, "error\\s+\\d+")
searchmatch("timeout")
```

### 3.6 Search literals

```spl
FROM main WHERE `500`
FROM main WHERE `user "ladron" from 192.0.2.0/24`
... | `top limit=20 referer`
```

### 3.7 String templates

```spl
... | eval summary="${host} returned ${status} for ${action}"
... | stats pivot("${status} with ${action}", count())
```

### 3.8 Field templates

```spl
SELECT * FROM [{city:"Seattle", Seattle:123}]
| eval '${city}' = 456
```

### 3.9 Lambda expressions

```spl
x -> x * 2
(x, y) -> x + y
(acc, x) -> { return acc + x }
```

Used with JSON functions:

```spl
... | eval nums=json_array(1,2,3,4)
... | eval doubled=map(nums, x -> x * 2)
... | eval evens=filter(nums, x -> x % 2 = 0)
... | eval has_large=any(nums, x -> x > 3)
... | eval total=reduce(nums, (acc, x) -> acc + x)
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/types-of-expressions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/expressions-and-predicates/lambda-expressions

## 4. Module-Level Grammar

### 4.1 Named searches

```spl
$base = from main where sourcetype="access_*"
$errors = from $base where status >= 400
```

### 4.2 Branching

```spl
$base = search index=main
$auth = from $base where source="/var/log/auth.log"
$web = from $base where sourcetype="access_*"
```

### 4.3 Views

Use exported named searches as stable reusable datasets.

```spl
$errors = from main where status >= 400
export $errors
```

### 4.4 Imports

Conceptually:

```spl
import my_namespace.security.$errors
```

### 4.5 Custom functions

Representative form:

```spl
function normalize_host($host: string) { return lower(trim($host)) }
```

### 4.6 Custom data types

Representative form:

```spl
type endpoint = { host: string, ip: string, status: int }
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/modules-statements-and-views/spl2-modules-and-statements
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/data-types/custom-data-types

## 5. Dataset Functions

### `repeat`

Create a temporary dataset, similar in spirit to `makeresults`.

```spl
FROM repeat({}, 3)
SELECT *
```

With seeded content:

```spl
FROM repeat({status:200, host:"www1"}, 2)
SELECT status, host
```

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/dataset-functions/overview-of-spl2-dataset-functions

## 6. Evaluation Functions

The examples below are intentionally small. Use them as syntax anchors.

### 6.1 Comparison And Conditional

- `case`: `... | eval severity=case(status>=500, "critical", status>=400, "error", true, "ok")`
- `cidrmatch`: `... | eval is_internal=cidrmatch("10.0.0.0/8", clientip)`
- `coalesce`: `... | eval user=coalesce(user, username, principal, "unknown")`
- `if`: `... | eval tier=if(bytes > 1048576, "large", "small")`
- `in`: `... | where status in("400", "401", "403", "404")`
- `like`: `... | where like(uri_path, "/api/%")`
- `match`: `... | eval has_error=match(_raw, "error\\s+\\d+")`
- `nullif`: `... | eval cleaned=nullif(user, "unknown")`
- `searchmatch`: `FROM main WHERE searchmatch("timeout") SELECT *`
- `validate`: `... | eval validation=validate(isnull(user), "missing user", status>=500, "server error")`

### 6.2 Conversion

- `ipmask`: `... | eval subnet=ipmask("255.255.255.0", clientip)`
- `object_to_array`: `... | eval pairs=object_to_array({host:host, status:status})`
- `object_to_xml`: `... | eval xml=object_to_xml({host:host, status:status})`
- `printf`: `... | eval msg=printf("%s:%s", host, status)`
- `to_ocsf`: `... | eval ocsf=to_ocsf(payload)`
- `toarray`: `... | eval arr=toarray(json_field)`
- `tobool`: `... | eval enabled=tobool(enabled_string)`
- `todouble`: `... | eval cpu=todouble(cpu_pct)`
- `toint`: `... | eval status_code=toint(status)`
- `tojson`: `... | eval payload_json=tojson(payload)`
- `tomv`: `... | eval mv=tomv(csv_values)`
- `tonumber`: `... | eval amount=tonumber(price)`
- `toobject`: `... | eval obj=toobject(payload_json)`
- `tostring`: `... | eval status_text=tostring(status)`
- `xml_to_object`: `... | eval obj=xml_to_object(xml_payload)`

### 6.3 Cryptographic

- `md5`: `... | eval digest=md5(user)`
- `sha1`: `... | eval digest=sha1(user)`
- `sha256`: `... | eval digest=sha256(user)`
- `sha512`: `... | eval digest=sha512(user)`

### 6.4 Date And Time

- `now`: `... | eval query_time=now()`
- `relative_time`: `... | eval next_hour=relative_time(_time, "+1h@h")`
- `strftime`: `... | eval day=strftime(_time, "%Y-%m-%d")`
- `strptime`: `... | eval parsed=strptime("2026-03-13 10:00:00", "%Y-%m-%d %H:%M:%S")`
- `time`: `... | eval unix_time=time()`

### 6.5 Informational

- `cluster`: `... | eval cluster_id=cluster(_raw)`
- `getfields`: `... | eval fields=getfields()`
- `isarray`: `... | eval ok=isarray(payload)`
- `isbool`: `... | eval ok=isbool(flag)`
- `isdouble`: `... | eval ok=isdouble(ratio)`
- `isint`: `... | eval ok=isint(status)`
- `ismv`: `... | eval ok=ismv(tags)`
- `isnotnull`: `... | eval ok=isnotnull(user)`
- `isnull`: `... | eval ok=isnull(error_code)`
- `isnum`: `... | eval ok=isnum(bytes)`
- `isobject`: `... | eval ok=isobject(payload)`
- `isstr`: `... | eval ok=isstr(host)`
- `typeof`: `... | eval kind=typeof(payload)`

### 6.6 JSON

- `json_object`: `... | eval obj=json_object("host", host, "status", status)`
- `json`: `... | eval parsed=json(payload)`
- `json_append`: `... | eval obj=json_append(obj, "tags", json_array("new"))`
- `json_array`: `... | eval arr=json_array(host, status, bytes)`
- `json_array_to_mv`: `... | eval mv=json_array_to_mv(arr)`
- `json_delete`: `... | eval trimmed=json_delete(obj, "debug")`
- `json_entries`: `... | eval entries=json_entries(obj)`
- `json_extend`: `... | eval ext=json_extend(obj, json_array("extra"))`
- `json_extract`: `... | eval user=json_extract(obj, "user")`
- `json_extract_exact`: `... | eval values=json_extract_exact(_raw, "user", "status")`
- `json_has_key_exact`: `... | eval has_user=json_has_key_exact(obj, "user")`
- `json_keys`: `... | eval keys=json_keys(obj)`
- `json_set`: `... | eval updated=json_set(obj, "status", 500)`
- `json_set_exact`: `... | eval updated=json_set_exact(obj, "status", 500)`
- `json_valid`: `... | eval ok=json_valid(payload)`
- `all`: `... | eval ok=all(arr, x -> x > 0)`
- `any`: `... | eval ok=any(arr, x -> x > 100)`
- `filter`: `... | eval evens=filter(arr, x -> x % 2 = 0)`
- `map`: `... | eval doubled=map(arr, x -> x * 2)`
- `reduce`: `... | eval total=reduce(arr, (acc, x) -> acc + x)`

### 6.7 Mathematical

- `abs`: `... | eval delta=abs(change)`
- `ceiling`: `... | eval ceil_val=ceiling(duration)`
- `exact`: `... | eval precise=exact(value)`
- `exp`: `... | eval e_power=exp(score)`
- `floor`: `... | eval floor_val=floor(duration)`
- `ln`: `... | eval natural_log=ln(value)`
- `log`: `... | eval base10=log(value)`
- `pi`: `... | eval circumference=2 * pi() * radius`
- `pow`: `... | eval squared=pow(value, 2)`
- `round`: `... | eval rounded=round(cpu_pct, 2)`
- `sigfig`: `... | eval sf=sigfig(value * rate)`
- `sqrt`: `... | eval root=sqrt(value)`

### 6.8 Multivalue Eval

- `mvappend`: `... | eval values=mvappend(host, source, sourcetype)`
- `mvcount`: `... | eval value_count=mvcount(tags)`
- `mvdedup`: `... | eval uniq=mvdedup(tags)`
- `mvfilter`: `... | eval api_tags=mvfilter(match(tags, "^api"))`
- `mvfind`: `... | eval pos=mvfind(tags, "prod")`
- `mvindex`: `... | eval first_tag=mvindex(tags, 0)`
- `mvjoin`: `... | eval joined=mvjoin(tags, "|")`
- `mvmap`: `... | eval lowered=mvmap(tags, lower(tags))`
- `mvrange`: `... | eval buckets=mvrange(0, 10, 2)`
- `mvsort`: `... | eval sorted=mvsort(tags)`
- `mvzip`: `... | eval paired=mvzip(keys, values, "=")`
- `mv_to_json_array`: `... | eval arr=mv_to_json_array(tags)`
- `split`: `... | eval parts=split(uri_path, "/")`

### 6.9 Statistical Eval

- `max`: `... | eval hi=max(cpu_user, cpu_system)`
- `min`: `... | eval lo=min(response_a, response_b)`
- `random`: `... | eval sample_id=random()`

### 6.10 Text

- `len`: `... | eval name_len=len(user)`
- `lower`: `... | eval user_lc=lower(user)`
- `ltrim`: `... | eval cleaned=ltrim(message, " ")`
- `replace`: `... | eval normalized=replace(uri_path, "/v[0-9]+/", "/vN/")`
- `rtrim`: `... | eval cleaned=rtrim(message, " ")`
- `spath`: `... | eval user=spath(payload, "event.user")`
- `substr`: `... | eval prefix=substr(session_id, 1, 8)`
- `trim`: `... | eval user_clean=trim(user)`
- `upper`: `... | eval env_uc=upper(env)`
- `urldecode`: `... | eval q=urldecode(query_string)`

### 6.11 Trig And Hyperbolic

- `acos`: `... | eval angle=acos(value)`
- `acosh`: `... | eval angle=acosh(value)`
- `asin`: `... | eval angle=asin(value)`
- `asinh`: `... | eval angle=asinh(value)`
- `atan`: `... | eval angle=atan(value)`
- `atan2`: `... | eval angle=atan2(y, x)`
- `atanh`: `... | eval angle=atanh(value)`
- `cos`: `... | eval c=cos(theta)`
- `cosh`: `... | eval c=cosh(theta)`
- `hypot`: `... | eval h=hypot(x, y)`
- `sin`: `... | eval s=sin(theta)`
- `sinh`: `... | eval s=sinh(theta)`
- `tan`: `... | eval t=tan(theta)`
- `tanh`: `... | eval t=tanh(theta)`

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/evaluation-functions/overview-of-spl2-eval-functions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/evaluation-functions/json-functions

## 7. Statistical And Charting Functions

### 7.1 Aggregate

- `avg`: `... | stats avg(bytes) AS avg_bytes by host`
- `count`: `... | stats count() AS events by host`
- `distinct_count`: `... | stats distinct_count(user) AS users by host`
- `estdc`: `... | stats estdc(session_id) AS approx_sessions by host`
- `estdc_error`: `... | stats estdc_error(session_id) AS error by host`
- `exactperc`: `... | stats exactperc(bytes, 95) AS p95 by host`
- `max`: `... | stats max(bytes) AS max_bytes by host`
- `mean`: `... | stats mean(bytes) AS mean_bytes by host`
- `median`: `... | stats median(bytes) AS median_bytes by host`
- `min`: `... | stats min(bytes) AS min_bytes by host`
- `mode`: `... | stats mode(status) AS common_status by host`
- `perc`: `... | stats perc(bytes, 95) AS p95 by host`
- `range`: `... | stats range(bytes) AS spread by host`
- `stdev`: `... | stats stdev(bytes) AS stddev by host`
- `stdevp`: `... | stats stdevp(bytes) AS stddev_population by host`
- `sum`: `... | stats sum(bytes) AS total_bytes by host`
- `sumsq`: `... | stats sumsq(bytes) AS sum_of_squares by host`
- `upperperc`: `... | stats upperperc(bytes, 95) AS upper_p95 by host`
- `var`: `... | stats var(bytes) AS variance by host`
- `varp`: `... | stats varp(bytes) AS variance_population by host`

### 7.2 Event Order

- `first`: `... | streamstats first(status) AS first_status by session_id`
- `last`: `... | streamstats last(status) AS last_status by session_id`

### 7.3 Multivalue And Array

- `dataset`: `... | stats dataset(host, status, bytes) AS rows by sourcetype`
- `list`: `... | stats list(uri_path) AS paths by host`
- `pivot`: `... | stats pivot("${status} with ${action}", count())`
- `unpivot`: `... | stats unpivot(metrics) AS entries by host`
- `values`: `... | stats values(status) AS unique_statuses by host`

### 7.4 Time

- `earliest`: `... | stats earliest(_time) AS first_seen by host`
- `earliest_time`: `... | stats earliest_time(_time) AS first_time by host`
- `latest`: `... | stats latest(_time) AS last_seen by host`
- `latest_time`: `... | stats latest_time(_time) AS last_time by host`
- `per_day`: `... | timechart per_day(sum(bytes))`
- `per_hour`: `... | timechart per_hour(sum(bytes))`
- `per_minute`: `... | timechart per_minute(sum(bytes))`
- `per_second`: `... | timechart per_second(sum(bytes))`
- `rate`: `... | timechart rate(sum(bytes))`
- `span`: `... | FROM main GROUP BY span(_time, 5m) SELECT count() AS events`
- `sparkline`: `... | stats sparkline(sum(bytes), 1h) AS trend by host`

Canonical docs:
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/statistical-and-charting-functions/overview-of-spl2-stats-and-chart-functions
- https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/statistical-and-charting-functions/aggregate-functions

## 8. Review Notes For Function Usage

When reviewing function-heavy SPL2, check these first:

- Is the function valid in the target compatibility profile?
- Is the function in an expression context versus a stats/chart context?
- Are string arguments double-quoted?
- Are aliases single-quoted only when needed?
- Would a clearer built-in function beat a search literal or a custom wrapper?
- Is the query doing too much inline when a named search or custom function would clarify it?

## 9. How To Use This Reference

Use this file for:

- grammar lookup
- expression syntax
- function family discovery
- quick example scaffolding

Use the companion files for:

- `spl2-developer-tutorial.md`: design, architecture, migration, modules, review strategy
- `spl2-context7-cookbook.md`: scenario-first problem solving
