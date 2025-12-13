# Demo: Quick Start

30-second GIF showing ragd installation to first search.

## Details

| Attribute | Value |
|-----------|-------|
| Duration | 30 seconds |
| Format | GIF |
| Audience | New users |

## Storyboard

### Scene 1: Installation (5s)
```
pip install git+https://github.com/REPPL/ragd.git
```
- Show progress bar
- Annotation: "Install with pip"

### Scene 2: Initialisation (8s)
```
ragd init
```
- Show hardware detection
- Show model download progress
- Annotation: "Detects your hardware"

### Scene 3: Indexing (7s)
```
ragd index ~/Documents/sample.pdf
```
- Show indexing progress
- Annotation: "Index any document"

### Scene 4: Search (10s)
```
ragd search "key findings"
```
- Show search results
- Navigate results with j/k
- Annotation: "Search semantically"

## Recording Script

```bash
#!/bin/bash
# Record with: asciinema rec quick-start.cast

clear
echo "# Install ragd"
sleep 1
pip install git+https://github.com/REPPL/ragd.git

echo ""
echo "# Initialise"
sleep 1
ragd init

echo ""
echo "# Index a document"
sleep 1
ragd index ~/sample.pdf

echo ""
echo "# Search your knowledge"
sleep 1
ragd search "key findings"
```

## Recording Notes

- Use clean environment
- Pre-download models if needed
- Have sample PDF ready
- Clear terminal before starting
- Pause briefly between commands

---

## Related Demos

- [Search Tour](02-search-tour.md)
- [Chat Tour](03-chat-tour.md)
