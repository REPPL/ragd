# F-041: User Profile Management

## Overview

**Research**: [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md)
**Milestone**: v2.0-beta
**Priority**: P0

## Problem Statement

RAG systems treat all users identically, ignoring individual preferences, expertise levels, and interaction patterns. Without user profiles, ragd cannot:

1. Remember user preferences (output format, language, topic interests)
2. Adapt retrieval to user expertise level
3. Track interaction history for personalisation
4. Provide contextually relevant results based on past behaviour

PersonaRAG research demonstrates 5-10% accuracy improvements from user-centric retrieval.

## Design Approach

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER PROFILE SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │  EXPLICIT PROFILE   │    │     BEHAVIOURAL PROFILE         │ │
│  │  (User-Defined)     │    │     (Learned)                   │ │
│  ├─────────────────────┤    ├─────────────────────────────────┤ │
│  │ • Display name      │    │ • Search patterns               │ │
│  │ • Language prefs    │    │ • Topic interests               │ │
│  │ • Output format     │    │ • Time-of-day patterns          │ │
│  │ • Expertise level   │    │ • Query complexity              │ │
│  │ • Topic interests   │    │ • Result preferences            │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
│            │                              │                      │
│            └──────────┬───────────────────┘                      │
│                       ▼                                          │
│            ┌─────────────────────┐                               │
│            │   PROFILE STORE     │                               │
│            │   (Encrypted KV)    │                               │
│            └─────────────────────┘                               │
│                       │                                          │
│                       ▼                                          │
│            ┌─────────────────────┐                               │
│            │ PERSONALISED        │                               │
│            │ RETRIEVAL           │                               │
│            └─────────────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Profile Types

| Type | Source | Examples | Update Frequency |
|------|--------|----------|------------------|
| **Explicit** | User input | Name, language, format preferences | On user action |
| **Behavioural** | Interaction tracking | Search patterns, topic interests | Per session |
| **Contextual** | Current session | Active topic, recent queries | Real-time |

### Technologies

- **Pydantic**: Profile schema validation
- **SQLite**: Profile storage (encrypted via F-015)
- **F-040 Memory**: Behavioural pattern storage

## Implementation Tasks

### Core Infrastructure
- [ ] Design UserProfile Pydantic model
- [ ] Design BehaviouralProfile model
- [ ] Implement ProfileStore (encrypted SQLite)
- [ ] Create profile serialisation/deserialisation

### Explicit Profile Management
- [ ] Implement `ragd profile create`
- [ ] Implement `ragd profile edit`
- [ ] Implement `ragd profile show`
- [ ] Implement `ragd profile export/import`
- [ ] Add profile settings to configuration

### Behavioural Profile Learning
- [ ] Track query patterns (topics, complexity)
- [ ] Track result interactions (clicks, time spent)
- [ ] Track time-of-day patterns
- [ ] Implement pattern aggregation
- [ ] Store behavioural data in F-040 memory

### Profile-Enhanced Retrieval
- [ ] Apply language preferences to results
- [ ] Apply format preferences to output
- [ ] Boost results matching topic interests
- [ ] Adjust complexity based on expertise
- [ ] Integrate with F-042 Persona Agents

### Testing
- [ ] Unit tests for profile models
- [ ] Integration tests for profile storage
- [ ] Tests for behavioural learning
- [ ] Tests for retrieval personalisation

## Success Criteria

- [ ] User can create and manage explicit profile
- [ ] Behavioural patterns captured automatically
- [ ] Profile data encrypted at rest
- [ ] Retrieval quality improves with profile (measurable)
- [ ] Profile export/import works correctly
- [ ] Privacy: all data stays local

## Dependencies

### Required (P0)
- F-015 Database Encryption (v0.7)
- F-040 Long-Term Memory (v2.0-alpha)

### Optional
- F-042 Persona Agent System (v2.0-beta)

## Technical Notes

### Profile Schema

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ExpertiseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class OutputFormat(str, Enum):
    CONCISE = "concise"      # Brief answers
    DETAILED = "detailed"    # Full explanations
    TECHNICAL = "technical"  # Code-heavy, precise
    CONVERSATIONAL = "conversational"  # Natural language

class UserProfile(BaseModel):
    """Explicit user preferences."""
    id: str
    display_name: str | None = None
    created_at: datetime
    updated_at: datetime

    # Language preferences
    language: str = "en"
    use_british_english: bool = True

    # Output preferences
    output_format: OutputFormat = OutputFormat.DETAILED
    include_citations: bool = True
    max_results: int = 10

    # Expertise
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    expertise_domains: list[str] = []  # e.g., ["python", "machine-learning"]

    # Topic interests
    topic_interests: list[str] = []  # e.g., ["security", "performance"]
    topic_exclusions: list[str] = []  # Topics to deprioritise


class BehaviouralProfile(BaseModel):
    """Learned user behaviour."""
    user_id: str
    updated_at: datetime

    # Query patterns
    avg_query_length: float = 0.0
    common_topics: dict[str, float] = {}  # topic -> frequency
    query_complexity: float = 0.5  # 0=simple, 1=complex

    # Interaction patterns
    preferred_result_count: int = 5
    avg_time_to_first_click: float = 0.0
    click_position_distribution: list[float] = []

    # Temporal patterns
    active_hours: list[int] = []  # Hours of day (0-23)
    session_duration_avg: float = 0.0

    # Result preferences
    prefers_recent: bool = False
    prefers_authoritative: bool = True
```

### Profile Store

```python
import sqlite3
from pathlib import Path

class ProfileStore:
    """Encrypted profile storage."""

    def __init__(self, db_path: Path, encryption_key: bytes):
        self.db_path = db_path
        self.key = encryption_key
        self._init_db()

    def _init_db(self):
        """Initialise encrypted database."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def save_profile(self, profile: UserProfile | BehaviouralProfile) -> None:
        """Save profile to encrypted store."""
        profile_type = "user" if isinstance(profile, UserProfile) else "behavioural"
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO profiles
                   (id, type, data, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    profile.id if hasattr(profile, 'id') else profile.user_id,
                    profile_type,
                    profile.model_dump_json(),
                    profile.created_at.isoformat() if hasattr(profile, 'created_at') else datetime.utcnow().isoformat(),
                    profile.updated_at.isoformat()
                )
            )

    def get_user_profile(self, user_id: str) -> UserProfile | None:
        """Retrieve user profile."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM profiles WHERE id = ? AND type = 'user'",
                (user_id,)
            ).fetchone()
            if row:
                return UserProfile.model_validate_json(row[0])
            return None

    def get_behavioural_profile(self, user_id: str) -> BehaviouralProfile | None:
        """Retrieve behavioural profile."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM profiles WHERE id = ? AND type = 'behavioural'",
                (user_id,)
            ).fetchone()
            if row:
                return BehaviouralProfile.model_validate_json(row[0])
            return None
```

### Behavioural Learning

```python
class BehaviouralLearner:
    """Learn user behaviour from interactions."""

    def __init__(self, profile_store: ProfileStore, memory: MemoryLayer):
        self.store = profile_store
        self.memory = memory

    async def record_query(
        self,
        user_id: str,
        query: str,
        results: list[SearchResult],
        clicked_indices: list[int],
        session_id: str
    ) -> None:
        """Record query and interaction for learning."""
        # Extract topics from query
        topics = await self._extract_topics(query)

        # Update behavioural profile
        profile = self.store.get_behavioural_profile(user_id)
        if not profile:
            profile = BehaviouralProfile(user_id=user_id, updated_at=datetime.utcnow())

        # Update topic frequencies
        for topic in topics:
            profile.common_topics[topic] = profile.common_topics.get(topic, 0) + 1

        # Update click distribution
        if clicked_indices:
            self._update_click_distribution(profile, clicked_indices, len(results))

        # Save updated profile
        profile.updated_at = datetime.utcnow()
        self.store.save_profile(profile)

        # Store as episodic memory
        await self.memory.add_memory(
            content=f"Searched for: {query}",
            memory_type=MemoryType.EPISODIC,
            metadata={"topics": topics, "clicked": clicked_indices}
        )
```

### Profile-Enhanced Retrieval

```python
async def profile_enhanced_search(
    query: str,
    user_profile: UserProfile,
    behavioural_profile: BehaviouralProfile,
    k: int = 10
) -> list[SearchResult]:
    """Search with profile-based personalisation."""

    # Get base results
    results = await vector_search(query, k * 2)  # Get extra for filtering

    # Boost by topic interests
    for result in results:
        for topic in user_profile.topic_interests:
            if topic.lower() in result.content.lower():
                result.score *= 1.2  # 20% boost

    # Deprioritise excluded topics
    for result in results:
        for topic in user_profile.topic_exclusions:
            if topic.lower() in result.content.lower():
                result.score *= 0.5  # 50% penalty

    # Boost by behavioural patterns
    for result in results:
        for topic, freq in behavioural_profile.common_topics.items():
            if topic.lower() in result.content.lower():
                boost = min(1.1, 1 + (freq * 0.01))  # Up to 10% boost
                result.score *= boost

    # Sort by adjusted score
    results.sort(key=lambda r: r.score, reverse=True)

    # Return top k
    return results[:k]
```

### Configuration

```yaml
profile:
  enabled: true
  database: ~/.ragd/profiles.db

  # Default profile settings
  defaults:
    language: en
    british_english: true
    output_format: detailed
    expertise_level: intermediate

  # Behavioural learning
  learning:
    enabled: true
    track_queries: true
    track_clicks: true
    track_time: true
    min_interactions: 10  # Before influencing results

  # Privacy
  privacy:
    anonymise_logs: true
    retention_days: 365
```

### CLI Commands

```bash
# Create/edit profile
ragd profile create
ragd profile edit

# Show current profile
ragd profile show
# Output:
# User Profile
# ============
# Display Name: (not set)
# Language: English (British)
# Output Format: Detailed
# Expertise: Intermediate
# Topic Interests: security, python
# Topic Exclusions: javascript

# Show behavioural profile
ragd profile show --behavioural
# Output:
# Behavioural Profile
# ===================
# Common Topics: security (45%), python (32%), performance (15%)
# Avg Query Length: 5.2 words
# Preferred Results: 5
# Active Hours: 09:00-17:00

# Update preferences
ragd profile set language en-GB
ragd profile set output-format concise
ragd profile set expertise advanced

# Manage topic interests
ragd profile interests add "machine-learning"
ragd profile interests remove "javascript"

# Export/import
ragd profile export profile.json
ragd profile import profile.json

# Reset behavioural learning
ragd profile reset --behavioural
```

## Related Documentation

- [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md) - Research basis
- [F-040: Long-Term Memory](./F-040-long-term-memory.md) - Memory integration
- [F-042: Persona Agent System](./F-042-persona-agent-system.md) - Agent integration
- [F-015: Database Encryption](./F-015-database-encryption.md) - Security
- [v2.0.0 Milestone](../../milestones/v2.0.0.md) - Release planning

---

**Status**: Planned
