# Use Case: Technical Manuals

Searching equipment manuals, product documentation, and technical guides with ragd.

## Scenario

You have manuals for appliances, vehicles, tools, and electronics scattered across drawers and folders. You want to:
- Find troubleshooting steps for error codes
- Look up specifications and part numbers
- Search installation and maintenance procedures
- Handle scanned manuals with OCR

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/manuals

chunking:
  strategy: recursive
  chunk_size: 512
  overlap: 50

search:
  mode: hybrid
  semantic_weight: 0.4
  keyword_weight: 0.6  # Higher for part numbers and error codes
```

### Initial Indexing

```bash
# Index all manuals
ragd index ~/Manuals --recursive
```

ragd automatically detects scanned PDFs and applies OCR.

### Check Extraction Quality

```bash
# Verify OCR quality on scanned manuals
ragd quality
ragd quality --below 0.7  # Find low-quality extractions
```

## Workflow

### Troubleshooting Issues

**Search by error code:**
```bash
ragd search "error code E45" --mode keyword
```

**Find troubleshooting steps:**
```bash
ragd search "dishwasher not draining troubleshooting"
```

**Search for symptoms:**
```bash
ragd search "washing machine making loud noise during spin"
```

### Finding Specifications

**Look up part numbers:**
```bash
ragd search "replacement filter part number" --mode keyword
```

**Find dimensions:**
```bash
ragd search "installation clearance dimensions"
```

**Check compatibility:**
```bash
ragd search "compatible accessories model X500"
```

### Maintenance Procedures

**Find maintenance schedules:**
```bash
ragd search "recommended maintenance schedule"
```

**Look up procedures:**
```bash
ragd search "how to replace drive belt"
```

### Organising Your Manual Library

**Tag by category:**
```bash
ragd tag add manual-123 "category:appliance" "brand:samsung" "type:washing-machine"
ragd tag add manual-456 "category:vehicle" "brand:honda" "model:civic"
```

**Create collections by location:**
```bash
ragd collection create "Kitchen Appliances" --include-all "location:kitchen"
ragd collection create "Garage Equipment" --include-all "location:garage"
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "error F21 troubleshooting" | Decode error codes |
| "oil change procedure" | Maintenance steps |
| "wifi setup instructions" | Configuration help |
| "warranty coverage" | Terms and conditions |
| "replacement parts list" | Ordering parts |
| "safety warnings" | Important precautions |

## Tips

1. **Keyword for codes** - Use `--mode keyword` for error codes and part numbers
2. **Check quality** - Run `ragd quality --below 0.7` to find poorly scanned manuals
3. **Tag by location** - Where is the equipment? Kitchen, garage, office?
4. **Brand tags** - Tag by brand for warranty lookups
5. **Reindex after rescan** - If quality is low, rescan and reindex

## Sample Troubleshooting Session

```bash
# Error appeared on dishwasher
ragd search "error E24 bosch dishwasher" --mode keyword

# Need to find the manual
ragd list --tag "brand:bosch" --tag "type:dishwasher"

# Look up the fix
ragd search "drain pump cleaning instructions"

# Find part number if needed
ragd search "drain pump replacement part" --mode keyword

# Check all manuals quality
ragd quality --type pdf
```

---

## Related Documentation

- [Tutorial: Processing Difficult PDFs](../tutorials/processing-difficult-pdfs.md)
- [F-025: PDF Quality Detection](../development/features/completed/F-025-pdf-quality-detection.md)
- [F-027: OCR Pipeline](../development/features/completed/F-027-ocr-pipeline.md)
- [F-028: Table Extraction](../development/features/completed/F-028-table-extraction.md)

## Related Use Cases

- [Code Documentation](code-documentation.md) - Technical documentation
- [Research Papers](research-papers.md) - PDF-heavy collections
