# Use Case: Financial Records

Managing tax documents, bank statements, and financial records with ragd.

## Scenario

You need to organise years of financial documents securely. You want to:
- Search across tax returns, bank statements, and investment records
- Keep sensitive data encrypted and access-controlled
- Maintain audit trails for compliance
- Securely delete old records when retention periods expire

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/finances
  encryption:
    enabled: true

chunking:
  strategy: recursive
  chunk_size: 512
  overlap: 50

search:
  mode: hybrid
  semantic_weight: 0.5
  keyword_weight: 0.5  # Important for account numbers, dates
```

### Initial Indexing

```bash
# Index tax documents
ragd index ~/Documents/Taxes --recursive

# Index bank statements
ragd index ~/Documents/Banking --recursive

# Index investment records
ragd index ~/Documents/Investments --recursive
```

### Set Sensitivity Tiers

```bash
# Tax returns contain sensitive data
ragd tier set tax-2023 sensitive

# Investment accounts may be critical
ragd tier set investment-portfolio critical
```

## Workflow

### Searching Financial Records

**Find specific transactions:**
```bash
ragd search "charitable donations 2024"
```

**Find by account or reference:**
```bash
ragd search "account ending 4532" --mode keyword
```

**Find deductible expenses:**
```bash
ragd search "business expenses deductible"
```

### Organising by Year and Type

**Tag documents systematically:**
```bash
ragd tag add doc-123 "year:2024" "type:tax-return"
ragd tag add doc-456 "year:2024" "type:bank-statement" "account:checking"
```

**Create collections for tax preparation:**
```bash
ragd collection create "2024 Tax Documents" --include-all "year:2024"
ragd collection create "Deductible Expenses" --include-all "type:receipt" "deductible:yes"
```

### Security and Compliance

**Check sensitivity tier distribution:**
```bash
ragd tier summary
```

**View audit trail:**
```bash
ragd audit list
ragd audit list --operation delete
```

**Securely delete expired records:**
```bash
# Standard deletion (removes from index)
ragd delete doc-old-2017

# Secure deletion (overwrites storage)
ragd delete doc-sensitive --secure

# Cryptographic erasure (for compliance)
ragd delete doc-critical --purge
```

### Preparing for Tax Season

```bash
ragd chat
> Summarise all deductible expenses from 2024
> What investment income do I need to report?
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "mortgage interest paid 2024" | Tax deduction research |
| "quarterly estimated payments" | Tax payment tracking |
| "capital gains transactions" | Investment reporting |
| "healthcare expenses FSA" | Medical deductions |
| "business mileage records" | Self-employment deductions |

## Tips

1. **Enable encryption** - Financial data should always be encrypted at rest
2. **Use sensitivity tiers** - Mark tax returns as SENSITIVE, investment accounts as CRITICAL
3. **Audit regularly** - Review `ragd audit list` periodically
4. **Keyword for numbers** - Use `--mode keyword` when searching account numbers or dates
5. **Secure deletion** - Use `--secure` or `--purge` for compliance with data retention policies
6. **Year-based tags** - Always tag with `year:YYYY` for easy filtering

## Sample Tax Preparation Session

```bash
# Find all 2024 documents
ragd search "2024" --tag "year:2024"

# Find charitable contributions
ragd search "donation receipt charity"

# Export for accountant
ragd export ~/tax-2024-docs.tar.gz --tag "year:2024"

# Check what's been deleted
ragd audit list --operation delete

# Verify tier compliance
ragd tier summary
```

---

## Related Documentation

- [F-015: Database Encryption](../development/features/completed/F-015-database-encryption.md)
- [F-017: Secure Deletion](../development/features/completed/F-017-secure-deletion.md)
- [F-018: Data Sensitivity Tiers](../development/features/completed/F-018-data-sensitivity-tiers.md)

## Related Use Cases

- [Personal Notes](personal-notes.md) - General document management
- [Meeting Notes](meeting-notes.md) - Work document organisation
