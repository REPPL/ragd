# Troubleshooting Guide

Common issues and solutions for ragd.

---

## Installation Issues

### "ragd: command not found"

**Cause:** ragd is not installed or not in your PATH.

**Solutions:**
1. Verify installation: `pip show ragd`
2. If not installed: `pip install ragd`
3. If installed but not found, try: `python -m ragd --help`
4. Ensure your Python scripts directory is in PATH

### "Model download failed"

**Cause:** Network issue during embedding model download.

**Solutions:**
1. Check your internet connection
2. Verify sufficient disk space (~500MB for default model)
3. Try again - downloads resume from where they stopped
4. If behind a proxy, configure your environment variables

---

## Indexing Issues

### "File not found" when indexing

**Cause:** Invalid file path or file doesn't exist.

**Solutions:**
1. Verify the file exists: `ls <path>`
2. Use absolute paths to avoid ambiguity
3. Check for typos in the filename

### "Unsupported file type"

**Cause:** ragd doesn't support this file format in the current version.

**Supported formats (v1.0.0):**
- PDF (`.pdf`)
- Plain text (`.txt`)
- Markdown (`.md`)
- HTML (`.html`, `.htm`)

**Solutions:**
1. Convert the file to a supported format
2. For Word documents, export as PDF or copy text to `.txt`

### "Failed to extract text from PDF"

**Cause:** PDF may be scanned, encrypted, or corrupted.

**Solutions:**
1. Try opening the PDF in a viewer to verify it's valid
2. For scanned PDFs, wait for v0.2 (OCR support)
3. For encrypted PDFs, remove the password first

### "No chunks created"

**Cause:** Document is too short or contains no extractable text.

**Solutions:**
1. Verify the document has readable text content
2. For PDFs, ensure text is selectable (not scanned images)
3. Check the file isn't empty

---

## Search Issues

### "No results found"

**Cause:** No indexed documents match the query.

**Solutions:**
1. Check you have indexed documents: `ragd info`
2. Try broader or different search terms
3. Verify the topic exists in your indexed documents
4. Use keywords that appear in your documents

### "Results seem irrelevant"

**Cause:** Semantic search interpretation differs from expectation.

**Solutions:**
1. Try more specific queries
2. Include key terms from the documents you expect to find
3. Use different phrasing for your query

### "Search is slow"

**Cause:** Large knowledge base or limited system resources.

**Solutions:**
1. Check system resources (memory, CPU)
2. Close other resource-intensive applications
3. For very large collections, consider indexing subsets

---

## Status/Health Issues

### "Health check fails: Storage"

**Cause:** ChromaDB database is inaccessible or corrupted.

**Solutions:**
1. Check the data directory exists: `ls ~/.ragd/`
2. Verify permissions on the directory
3. If corrupted, backup and recreate: `rm -rf ~/.ragd/chroma/`

### "Health check fails: Embedding"

**Cause:** Embedding model failed to load.

**Solutions:**
1. Check available memory (model requires ~500MB RAM)
2. Re-download the model by deleting cache: `rm -rf ~/.cache/torch/`
3. Check for disk space issues

### "Health check fails: Configuration"

**Cause:** Invalid configuration file.

**Solutions:**
1. Check config file syntax: `cat ~/.ragd/config.yaml`
2. Remove invalid settings or restore defaults
3. Delete config and let ragd recreate: `rm ~/.ragd/config.yaml`

---

## Performance Issues

### "Indexing is very slow"

**Cause:** Large files, limited CPU, or many documents.

**Solutions:**
1. Index smaller batches of documents
2. Close other applications to free resources
3. Consider a machine with more CPU cores

### "High memory usage"

**Cause:** Large embedding model or many documents loaded.

**Solutions:**
1. Close and restart ragd between large operations
2. Index documents in smaller batches
3. Consider a lighter embedding model (future feature)

---

## Getting More Help

### Check the logs

ragd logs are stored at `~/.ragd/logs/ragd.log`. Check recent entries for error details:

```bash
tail -50 ~/.ragd/logs/ragd.log
```

### Report an issue

If you've tried the solutions above and still have problems:

1. Gather information:
   - ragd version: `ragd --version`
   - Operating system and version
   - Full error message
   - Steps to reproduce

2. Search existing issues to see if it's known

3. Report via the project's issue tracker

---

## Related Documentation

- [Getting Started Tutorial](../tutorials/01-getting-started.md)
- [Reference Documentation](../reference/)

