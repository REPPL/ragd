# Use Case: Recipe Collection

Organising recipes from cookbooks, websites, and family traditions with ragd.

## Scenario

Your recipes are scattered everywhere: cookbook PDFs, screenshots, printed pages, and family recipes. You want to:
- Search by ingredient, cuisine, or cooking technique
- Find recipes for dietary restrictions
- Organise for meal planning
- Auto-index new recipes as you save them

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/recipes

chunking:
  strategy: sentence
  chunk_size: 512
  overlap: 50

search:
  mode: hybrid
  semantic_weight: 0.7
```

### Initial Indexing

```bash
# Index cookbook PDFs
ragd index ~/Cookbooks --recursive

# Index saved recipes
ragd index ~/Recipes --recursive
```

### Watch Folder for New Recipes

```bash
# Auto-index new recipes as you save them
ragd watch start ~/Recipes
```

## Workflow

### Finding Recipes

**Search by ingredient:**
```bash
ragd search "chicken thighs garlic lemon"
```

**Search by technique:**
```bash
ragd search "slow braised one pot"
```

**Search by cuisine:**
```bash
ragd search "authentic Thai curry"
```

**Find quick meals:**
```bash
ragd search "30 minute weeknight dinner"
```

### Organising Your Collection

**Tag by cuisine and diet:**
```bash
ragd tag add recipe-123 "cuisine:italian" "diet:vegetarian"
ragd tag add recipe-456 "cuisine:mexican" "time:quick" "difficulty:easy"
```

**Create meal planning collections:**
```bash
ragd collection create "Weeknight Dinners" --include-all "time:quick"
ragd collection create "Vegetarian" --include-all "diet:vegetarian"
ragd collection create "Holiday Favourites" --include-all "occasion:holiday"
ragd collection create "Kid-Friendly" --include-all "audience:kids"
```

### Meal Planning with Chat

```bash
ragd chat
> Suggest 5 vegetarian dinners I can make this week
> What can I make with chicken, rice, and vegetables?
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "dairy-free dessert chocolate" | Dietary restriction search |
| "grilling summer vegetables" | Seasonal cooking |
| "make-ahead freezer meals" | Batch cooking |
| "substitution for butter" | Ingredient swaps |
| "grandmother's apple pie" | Family recipes |

## Tips

1. **Watch folder** - Set up `ragd watch` for your recipe save folder
2. **Consistent tags** - Use `cuisine:`, `diet:`, `time:`, `difficulty:` prefixes
3. **Semantic search** - "comfort food for cold weather" works great
4. **Collections for planning** - Weekly meal planning becomes easy
5. **Screenshot recipes** - ragd can OCR images from PDFs

## Sample Cooking Session

```bash
# What to make with what's in the fridge
ragd search "salmon asparagus lemon"

# Find something quick
ragd search "15 minute pasta" --tag "time:quick"

# Get ideas for the week
ragd chat
> Plan 5 balanced dinners using seasonal autumn ingredients

# Save a new recipe (auto-indexed if watch is running)
# Just save the PDF to ~/Recipes and it's automatically indexed
ragd watch status
```

---

## Related Documentation

- [Tutorial: Getting Started](../tutorials/01-getting-started.md)
- [F-037: Watch Folder](../development/features/completed/F-037-watch-folder.md)
- [F-027: OCR Pipeline](../development/features/completed/F-027-ocr-pipeline.md)

## Related Use Cases

- [Personal Notes](personal-notes.md) - General organisation
- [E-book Library](ebook-library.md) - Book collection management
