# Privacy-Preserving Local Personal Assistant - State-of-the-Art

Security architecture for a local-only personal assistant handling highly sensitive data.

## Executive Summary

A privacy-first personal assistant with access to very personal information (medical, financial, journals, credentials) requires multiple layers of protection. The threat model assumes an attacker may gain physical access to the device or code, but the system remains single-user.

This analysis covers:
1. Threat modelling
2. Data protection layers
3. Vector database security (critical for RAG)
4. Authentication and access control
5. Secure data lifecycle
6. Implementation recommendations

---

## 1. Threat Model

**Primary Threats:**

| Threat | Description | Severity |
|--------|-------------|----------|
| **Physical access** | Someone finds/steals the device | Critical |
| **Code access** | Someone accesses database files directly | Critical |
| **Memory attacks** | Cold boot, swap file analysis | High |
| **Embedding inversion** | Extracting text from vector embeddings | High |
| **Shoulder surfing** | Someone sees screen during use | Medium |
| **Malware** | Keyloggers, screen capture | High |

**Attack Scenarios:**
1. **Stolen laptop**: Attacker boots the device or removes the drive
2. **Shared device**: Family member or colleague browses files
3. **Compromised system**: Malware targets the knowledge base
4. **Forensic analysis**: Device inspected after being discarded

**What We're NOT Protecting Against:**
- Sophisticated state actors with unlimited resources
- Hardware implants
- Active attacks while the user is authenticated (trusted session)

---

## 2. Data Protection Layers

### Layer 1: Encryption at Rest

**Database Encryption (SQLCipher)**

[SQLCipher](https://www.zetetic.net/sqlcipher/) provides transparent 256-bit AES encryption of SQLite databases with only 5-15% performance overhead.

```
User Password → [Argon2id KDF] → Master Key → [AES-256] → Encrypted Database
```

**Vector Database Encryption**

ChromaDB uses SQLite internally. Options:
1. **SQLCipher backend**: Encrypt the underlying SQLite ([ChromaDB Privacy Strategies](https://cookbook.chromadb.dev/strategies/privacy/))
2. **Client-side encryption**: Encrypt documents before embedding, store encrypted chunks
3. **Encrypted embeddings**: Homomorphic encryption (performance trade-off)

**Source**: [PrivateGPT Discussion #481](https://github.com/zylon-ai/private-gpt/discussions/481)

### Layer 2: Key Derivation

**Argon2id (Recommended)**

[Argon2id](https://en.wikipedia.org/wiki/Argon2) is the winner of the 2015 Password Hashing Competition, designed to resist both GPU and side-channel attacks.

```
Password + Salt → [Argon2id: 64MB memory, 3 iterations, 4 threads] → 256-bit Key
```

**Key Architecture:**
```
User Password → [Argon2id] → Master Key
                                ↓
              ┌─────────────────┼─────────────────┐
              ↓                 ↓                 ↓
         Database Key    Embedding Key     Config Key
```

**Source**: [Bitwarden KDF Algorithms](https://bitwarden.com/help/kdf-algorithms/)

### Layer 3: Memory Protection

**Challenge**: Python doesn't natively support secure memory handling.

**Mitigations:**
1. **mlock()**: Prevent memory from swapping to disk ([Stack Overflow](https://stackoverflow.com/questions/32820862/mlock-a-variable-in-python))
2. **Disable core dumps**: `ulimit -c 0`
3. **Encrypted swap**: Use LUKS-encrypted swap partition
4. **Clear sensitive data**: Overwrite buffers after use (limited in Python)

**Source**: [Secure Programs HOWTO](https://dwheeler.com/secure-programs/Secure-Programs-HOWTO/protect-secrets.html)

**Recommendation**: For the most sensitive operations, consider a Rust or C extension module.

---

## 3. Vector Database Security (Critical for RAG)

### Embedding Inversion Attacks

**The Risk**: Attackers can reconstruct original text from embeddings with up to 92% accuracy.

"In the paper with the best results so far, attackers were able to recover the exact inputs in 92% of cases including full names and health diagnoses."

**Source**: [IronCore Labs: Text Embedding Privacy Risks](https://ironcorelabs.com/blog/2024/text-embedding-privacy-risks/)

**OWASP LLM Top 10**: [LLM08: Vector and Embedding Weaknesses](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

### Defence Mechanisms

**Option 1: Encrypted Embeddings (Homomorphic Encryption)**

[Apple's PNNS](https://machinelearning.apple.com/research/homomorphic-encryption) demonstrates private nearest neighbour search using BFV homomorphic encryption scheme.

```
Query → [Encrypt] → Ciphertext → [HE Similarity Search] → Encrypted Results → [Decrypt]
```

**Trade-off**: 10-100x performance overhead for fully homomorphic operations.

**Source**: [Apple ML Research: Homomorphic Encryption](https://machinelearning.apple.com/research/homomorphic-encryption)

**Option 2: Additive Homomorphic Encryption (AHE)**

More practical than FHE, supports cosine similarity on encrypted vectors.

**Source**: [Javelin Blog: Secure AI Embeddings](https://www.getjavelin.com/blogs/secure-your-ai-embeddings-with-homomorphic-encryption)

**Option 3: Eguard Defense**

Transforms embeddings to resist inversion while preserving utility (95% token protection).

**Source**: [arXiv:2411.05034](https://arxiv.org/abs/2411.05034)

**Option 4: Encrypted Chunk Storage + Unencrypted Embeddings**

Pragmatic approach: Encrypt the original text chunks, leave embeddings unencrypted. Risk: embeddings can still leak semantic information.

### Private Information Retrieval (PIR)

PIR allows querying without revealing the query itself.

"The client sends a request vector which contains encryptions of 0 or 1, and the server multiplies each database element with its corresponding vector entry."

**Source**: [Cryptowiki: PIR](https://cryptowiki.tm.kit.edu/index.php/Private_Information_Retrieval)

**For local-only**: PIR is less relevant since you're querying your own data, but useful if ever extending to multi-device sync.

---

## 4. Authentication and Access Control

### Session Management

**Auto-Lock Timeout:**
```
Last Activity → [Timeout: 5 min] → Lock Screen → [Re-auth Required]
```

**Lock Behaviour:**
- Clear decryption keys from memory
- Require password/biometric to unlock
- Option: Wipe keys after N failed attempts

### Authentication Options (Tiered)

| Level | Method | Security | Convenience |
|-------|--------|----------|-------------|
| 1 | Password only | Medium | High |
| 2 | Password + FIDO2 key | High | Medium |
| 3 | Hardware key required | Very High | Low |
| 4 | Biometric + password | High | High |

**FIDO2/Passkeys**: Hardware security keys (YubiKey, SoloKey) provide phishing-resistant authentication.

**Source**: [Microsoft: FIDO2 Sign-in](https://learn.microsoft.com/en-us/entra/identity/authentication/howto-authentication-passwordless-security-key-windows)

### Data Compartmentalisation

**Sensitivity Tiers:**

| Tier | Data Type | Access Control | Encryption |
|------|-----------|----------------|------------|
| **Public** | General notes, bookmarks | Always accessible | Database encryption |
| **Personal** | Personal notes, preferences | Password unlock | + per-tier key |
| **Sensitive** | Financial, medical | Biometric + password | + additional passphrase |
| **Critical** | Credentials, legal docs | Hardware key required | + time-limited access |

**Implementation:**
```
ragd search "my bank details" --tier sensitive
[Biometric prompt]
[Results displayed]
[Auto-clear after 30 seconds]
```

**Source**: [NIST Compartmentalisation Definition](https://csrc.nist.gov/glossary/term/compartmentalization)

---

## 5. Secure Data Lifecycle

### Secure Deletion Challenges

**SSD Problem**: Traditional overwrite doesn't work due to wear-levelling and TRIM.

"Even after a drive has been wiped, fragments of sensitive data can still remain in hidden areas."

**Source**: [MakeUseOf: SSD Secure Delete](https://www.makeuseof.com/tag/ssd-secure-delete-data/)

### Recommended Approaches

**For File-Level:**
1. **Encrypt-then-delete**: All sensitive data encrypted from creation
2. **Key destruction**: Destroying the key renders data unrecoverable

**For Full Database:**
1. **ATA Secure Erase**: Hardware-level command
2. **Cryptographic Erase**: For self-encrypting drives
3. **Physical destruction**: For end-of-life

**Implementation:**
```
# Secure deletion workflow
ragd purge --document <id>
  1. Remove from vector index
  2. Remove encrypted chunks
  3. Overwrite metadata
  4. Note: Full recovery impossible only with key destruction
```

**Source**: [EFF: How to Delete Data Securely](https://ssd.eff.org/module/how-delete-your-data-securely-windows)

---

## 6. Advanced Techniques

### Hardware Security (Future Enhancement)

**Intel SGX / ARM TrustZone:**

Secure enclaves provide hardware-isolated execution environments.

"Data is encrypted when outside the CPU, only decrypting within the secure enclave."

**Source**: [PatSnap: Secure Enclaves](https://eureka.patsnap.com/article/secure-enclaves-in-modern-cpus-intel-sgx-arm-trustzone)

**Challenge**: Intel deprecated consumer SGX; ARM TrustZone requires specific SoC support.

**Apple Secure Enclave**: Available on Apple Silicon, handles biometric key storage.

### Differential Privacy for RAG

Add calibrated noise to queries/responses to prevent information leakage.

"A straightforward approach to DP RAG is to generate synthetic documents with differential privacy out of the private knowledge base."

**Source**: [arXiv:2412.19291](https://arxiv.org/abs/2412.19291)

**Use Case**: If ever adding any analytics or telemetry (opt-in), differential privacy protects individual data points.

---

## 7. Implementation Recommendations for ragd

### Phase 1: Foundation (v0.7 - Privacy & Security)

Already planned in ragd roadmap. Enhance with:

| Feature | Implementation | Priority |
|---------|----------------|----------|
| **Database encryption** | SQLCipher backend for ChromaDB | Critical |
| **Key derivation** | Argon2id (64MB, 3 iterations) | Critical |
| **Session lock** | Auto-lock after 5 min inactivity | High |
| **Password auth** | Master password for unlock | Critical |

### Phase 2: Enhanced Protection (v0.7+)

| Feature | Implementation | Priority |
|---------|----------------|----------|
| **Encrypted chunks** | AES-256 for document storage | High |
| **Memory protection** | mlock for key material | Medium |
| **Audit logging** | Track all data access | Medium |
| **FIDO2 support** | Optional hardware key | Medium |

### Phase 3: Advanced (v0.9+)

| Feature | Implementation | Priority |
|---------|----------------|----------|
| **Data tiers** | Compartmentalised access | Medium |
| **Embedding protection** | Eguard-style transformation | Medium |
| **Biometric unlock** | System biometric integration | Low |
| **Secure deletion** | Key destruction workflow | Medium |

### Configuration Example

```yaml
# ~/.ragd/config.yaml
security:
  encryption:
    algorithm: AES-256-GCM
    kdf: argon2id
    kdf_memory_mb: 64
    kdf_iterations: 3

  session:
    auto_lock_minutes: 5
    failed_attempts_lockout: 5
    clear_clipboard_seconds: 30

  authentication:
    require_password: true
    allow_biometric: true
    require_hardware_key: false  # Optional

  tiers:
    enabled: false  # Future feature
    sensitive_requires: [password, biometric]
    critical_requires: [password, hardware_key]
```

---

## 8. Trade-Off Summary

| Approach | Security | Performance | Usability | Complexity |
|----------|----------|-------------|-----------|------------|
| **No encryption** | None | Best | Best | None |
| **Database encryption (SQLCipher)** | Good | 5-15% overhead | Good | Low |
| **+ Encrypted chunks** | Better | 10-20% overhead | Good | Medium |
| **+ Embedding encryption (HE)** | Best | 10-100x overhead | Poor | High |
| **Hardware enclave** | Excellent | Minimal | Medium | Very High |

**Recommended**: Database encryption + encrypted chunks + session lock + auto-lock timeout. This provides strong protection against physical access without significant usability impact.

---

## 9. Research Sources

| Topic | Source | Date |
|-------|--------|------|
| Embedding Inversion Attacks | [ACL 2024](https://aclanthology.org/2024.acl-long.230/) | Jun 2024 |
| Eguard Defense | [arXiv:2411.05034](https://arxiv.org/abs/2411.05034) | Nov 2024 |
| RAG Differential Privacy | [arXiv:2412.19291](https://arxiv.org/abs/2412.19291) | Dec 2024 |
| RemoteRAG Privacy | [ACL 2025](https://aclanthology.org/2025.findings-acl.197/) | 2025 |
| Apple HE for ML | [Apple Research](https://machinelearning.apple.com/research/homomorphic-encryption) | 2024 |
| SQLCipher | [Zetetic](https://www.zetetic.net/sqlcipher/) | Ongoing |
| Argon2 | [RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106) | 2021 |
| Secure Memory | [Secure Programs HOWTO](https://dwheeler.com/secure-programs/Secure-Programs-HOWTO/protect-secrets.html) | Ongoing |
| OWASP LLM Top 10 | [OWASP](https://owasp.org/www-project-top-10-for-large-language-model-applications/) | 2024 |

---

## Related Documentation

- [State-of-the-Art RAG Techniques](./state-of-the-art-rag.md)
- [Feature Roadmap](../features/)
- [Security Feature Specs](../features/planned/) (when created)
- [ADRs](../decisions/adrs/)

---

**Status:** Research complete

