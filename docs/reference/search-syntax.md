# Search Syntax Reference

Complete specification of ragd search query syntax.

## Synopsis

```bash
ragd search "<query>" [OPTIONS]
```

## Query Types

### Simple Queries

```bash
# Single word
ragd search "python"

# Multiple words (implicit AND in keyword mode)
ragd search "python tutorial"

# Natural language (works best in hybrid/semantic mode)
ragd search "how does authentication work"
```

### Boolean Queries

Boolean operators are most effective with `--mode keyword`.

## Boolean Operators

| Operator | Syntax | Description | Example |
|----------|--------|-------------|---------|
| **AND** | `term1 AND term2` | Both terms required | `python AND testing` |
| **OR** | `term1 OR term2` | Either term matches | `ML OR "machine learning"` |
| **NOT** | `term1 NOT term2` | Exclude term | `Python NOT Django` |

### AND Operator

Requires both terms to appear in the same document chunk.

```bash
ragd search "Python AND web" --mode keyword
ragd search "machine AND learning AND tutorial" --mode keyword
```

**Note:** Adjacent terms are connected with implicit AND:
- `python testing` = `python AND testing`

### OR Operator

Matches documents containing either term (or both).

```bash
ragd search "Python OR JavaScript" --mode keyword
ragd search "ML OR AI OR \"machine learning\"" --mode keyword
```

**Use cases:**
- Synonyms: `colour OR color`
- Abbreviations: `ML OR "machine learning"`
- Alternatives: `Python OR Java OR Go`

### NOT Operator

Excludes documents containing the specified term.

```bash
ragd search "Python NOT snake" --mode keyword
ragd search "web NOT Django NOT Flask" --mode keyword
```

**Limitations:**
- Cannot use NOT alone (e.g., `NOT python` won't work)
- Must have a positive term before NOT

## Operator Precedence

From highest to lowest:

1. **Parentheses** `()`
2. **NOT**
3. **AND**
4. **OR**

**Examples:**
```bash
# Evaluates as: A OR (B AND C)
ragd search "A OR B AND C" --mode keyword

# Evaluates as: (A OR B) AND C
ragd search "(A OR B) AND C" --mode keyword
```

## Grouping with Parentheses

Use parentheses to control evaluation order.

```bash
ragd search "(Python OR Java) AND web" --mode keyword
ragd search "machine AND (learning OR intelligence)" --mode keyword
ragd search "((A OR B) AND C) NOT deprecated" --mode keyword
```

## Phrase Search

Use double quotes for exact phrase matching.

```bash
ragd search '"machine learning"' --mode keyword
ragd search '"error code E1234"' --mode keyword
ragd search '"Python web framework"' --mode keyword
```

**Shell quoting:** Use single quotes around the entire query when it contains double quotes.

## Prefix Search

Use asterisk `*` for prefix matching.

```bash
ragd search "program*" --mode keyword    # program, programming, programmer
ragd search "auth*" --mode keyword       # authentication, authorisation
ragd search "config*" --mode keyword     # config, configuration, configure
```

**Note:** The asterisk must be at the end of the word.

## Case Sensitivity

- **Operators:** Case-insensitive (`AND`, `and`, `And` all work)
- **Search terms:** Case-insensitive (FTS5 default)

## Search Modes

| Mode | Description | Boolean Support |
|------|-------------|-----------------|
| `hybrid` | Semantic + keyword (default) | Partial (keyword component) |
| `semantic` | Vector similarity only | No |
| `keyword` | BM25 keyword only | Full |

```bash
ragd search "query" --mode hybrid    # Default
ragd search "query" --mode semantic  # Meaning-based
ragd search "query" --mode keyword   # Boolean operators work best here
```

## Examples

### Basic Boolean

```bash
# AND - both terms required
ragd search "python AND testing" --mode keyword

# OR - either term
ragd search "python OR javascript" --mode keyword

# NOT - exclusion
ragd search "python NOT snake" --mode keyword
```

### Phrases and Prefixes

```bash
# Exact phrase
ragd search '"machine learning"' --mode keyword

# Prefix match
ragd search "mach*" --mode keyword

# Phrase with operator
ragd search '"machine learning" AND tutorial' --mode keyword
```

### Complex Queries

```bash
# Grouped OR with AND
ragd search "(Python OR Java) AND API" --mode keyword

# Multiple operators
ragd search "(ML OR AI) AND tutorial NOT beginner" --mode keyword

# Nested groups
ragd search "((Python OR Go) AND web) NOT deprecated" --mode keyword

# Everything combined
ragd search '(Python OR Java) AND "API design" NOT legacy' --mode keyword
```

### Combined with Options

```bash
# With result limit
ragd search "Python AND web" --mode keyword --limit 5

# With minimum score
ragd search "machine learning" --mode keyword --min-score 0.5

# With citation style
ragd search "authentication" --mode keyword --cite apa

# JSON output
ragd search "API" --mode keyword --output-format json
```

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Query cannot start with AND/OR" | Leading operator | Add a search term before the operator |
| "Query cannot end with operator" | Trailing operator | Add a search term after the operator |
| "Unbalanced parentheses" | Missing `(` or `)` | Check parentheses match |
| "Query cannot be empty" | Empty query string | Provide search terms |

## Limitations

1. **Standalone NOT:** `NOT term` alone doesn't work in FTS5
2. **Keyword mode only:** Boolean operators are most effective in `--mode keyword`
3. **Chunk-level matching:** AND requires both terms in the same chunk, not just the same document

---

## Related Documentation

- [Powerful Searching Tutorial](../tutorials/powerful-searching.md)
- [CLI Reference](./cli-reference.md)

---

**Status**: Complete
