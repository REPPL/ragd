# Powerful Searching with ragd

Learn to find exactly what you need using natural language AND precise boolean operators.

**Time:** 15-20 minutes
**Prerequisites:** ragd installed, some documents indexed

## What You'll Learn

1. When to use simple search vs boolean operators
2. The three boolean operators (AND, OR, NOT)
3. How to combine operators effectively
4. Common search patterns for everyday use

---

## Step 1: Simple Search Is Often Enough

ragd uses **hybrid search** by default, combining semantic understanding with keyword matching. This means you can often just type what you're looking for:

```bash
ragd search "how does authentication work"
```

ragd understands meaning, not just keywords. It will find documents about "login", "authorisation", and "access control" even if they don't use the exact word "authentication".

**When simple search works best:**
- Exploring a topic
- Looking for concepts, not specific terms
- You're not sure exactly what you're looking for

---

## Step 2: When You Need More Precision

Sometimes you need more control. Boolean operators let you be precise about exactly what you want (and don't want).

**Use boolean operators when:**
- You're getting too many irrelevant results
- You need to find documents with specific term combinations
- You want to exclude certain topics
- You're searching for exact phrases or technical identifiers

**Important:** Boolean operators work best with `--mode keyword`:

```bash
ragd search "your query" --mode keyword
```

---

## Step 3: AND - Narrowing Your Search

**AND** requires both terms to appear in the same document chunk.

```bash
ragd search "Python AND web" --mode keyword
```

This finds documents that discuss BOTH Python AND web development together - like "Python web frameworks" or "building web apps with Python".

**Visual explanation:**

```
   Python           web
  ┌─────────┐   ┌─────────┐
  │         │   │         │
  │    ┌────┼───┼────┐    │
  │    │  ▓▓▓▓▓▓▓▓  │    │
  │    └────┼───┼────┘    │
  │         │   │         │
  └─────────┘   └─────────┘

  ▓▓ = Results (overlap - both terms)
```

**Try it yourself:**
```bash
ragd search "machine AND learning" --mode keyword
ragd search "API AND security" --mode keyword
```

---

## Step 4: OR - Broadening Your Search

**OR** finds documents containing either term (or both).

```bash
ragd search "ML OR AI" --mode keyword
```

This is perfect for:
- Synonyms: `"colour OR color"`
- Abbreviations: `"ML OR machine learning"`
- Alternatives: `"Python OR JavaScript"`

**Visual explanation:**

```
   Python           Java
  ┌─────────┐   ┌─────────┐
  │  ▓▓▓▓   │   │   ▓▓▓▓  │
  │  ▓▓▓▓───┼───┼───▓▓▓▓  │
  │  ▓▓▓▓   │   │   ▓▓▓▓  │
  └─────────┘   └─────────┘

  ▓▓ = Results (union - either term)
```

**Try it yourself:**
```bash
ragd search "Python OR JavaScript" --mode keyword
ragd search '"machine learning" OR ML OR AI' --mode keyword
```

---

## Step 5: NOT - Excluding Results

**NOT** excludes documents containing a specific term.

```bash
ragd search "Python NOT snake" --mode keyword
```

This finds documents about the Python programming language while excluding documents about Python snakes.

**Visual explanation:**

```
   Python           snake
  ┌─────────┐   ┌─────────┐
  │  ▓▓▓▓   │   │         │
  │  ▓▓▓▓───┼───┼─────    │
  │  ▓▓▓▓   │   │         │
  └─────────┘   └─────────┘

  ▓▓ = Results (Python minus snake)
```

**Warning:** Use NOT sparingly - it may exclude relevant documents that happen to mention the excluded term.

**Try it yourself:**
```bash
ragd search "web NOT Django" --mode keyword
ragd search "API NOT deprecated" --mode keyword
```

---

## Step 6: Combining Operators

Use **parentheses** to control how operators are evaluated.

```bash
ragd search "(Python OR Java) AND web" --mode keyword
```

This finds web-related documents that discuss either Python OR Java.

Without parentheses, the query would be evaluated differently:
- `Python OR Java AND web` = `Python OR (Java AND web)`
- `(Python OR Java) AND web` = documents with (Python OR Java) that ALSO have web

**Operator precedence (highest to lowest):**
1. Parentheses `()`
2. NOT
3. AND
4. OR

**Complex example:**
```bash
ragd search '(Python OR JavaScript) AND API NOT deprecated' --mode keyword
```

This finds: API documentation for Python OR JavaScript, excluding anything marked deprecated.

---

## Step 7: Exact Phrases and Prefixes

### Exact Phrases

Use double quotes for exact phrase matching:

```bash
ragd search '"machine learning"' --mode keyword
```

This finds the exact phrase "machine learning", not documents that just happen to contain both words separately.

**Note:** In bash, use single quotes around the entire query when it contains double quotes.

### Prefix Matching

Use asterisk `*` to match word prefixes:

```bash
ragd search "program*" --mode keyword
```

This matches: program, programming, programmer, programmable, etc.

**Try it yourself:**
```bash
ragd search "auth*" --mode keyword    # authentication, authorisation, author
ragd search "config*" --mode keyword  # config, configuration, configure
```

---

## Common Search Patterns

| Use Case | Query Pattern | Example |
|----------|---------------|---------|
| Find both topics | `topic1 AND topic2` | `Python AND testing` |
| Find alternatives | `topic1 OR topic2` | `ML OR "machine learning"` |
| Exclude something | `topic1 NOT exclude` | `Python NOT 2.7` |
| Exact phrase | `"exact words"` | `"error code E1234"` |
| Word variations | `prefix*` | `config*` |
| Complex query | `(A OR B) AND C` | `(Python OR Java) AND web` |
| Technical ID | `"ID" AND context` | `"E1234" AND authentication` |

---

## Tips and Best Practices

1. **Start simple** - Try natural language first, add operators if needed
2. **Use keyword mode** - Boolean operators work best with `--mode keyword`
3. **Operators are UPPERCASE** - `AND` not `and` (though lowercase works too)
4. **Quote phrases** - `"machine learning"` not `machine learning`
5. **Test incrementally** - Build complex queries step by step
6. **NOT is risky** - May exclude relevant documents unintentionally

---

## What You Learned

- **AND** narrows results to documents with all terms
- **OR** broadens results to documents with any term
- **NOT** excludes documents with specific terms
- **Parentheses** control operator precedence
- **Quotes** match exact phrases
- **Asterisk** matches word prefixes

---

## Next Steps

- [Search Syntax Reference](../reference/search-syntax.md) - Complete syntax specification
- [CLI Reference](../reference/cli-reference.md) - All search command options

---

**Status**: Complete
