"""Search functionality for ragd.

Provides both semantic search and hybrid search combining
semantic (vector) and keyword (BM25) search.
"""

from ragd.search.bm25 import BM25Index, BM25Result
from ragd.search.hybrid import (
    HybridSearcher,
    HybridSearchResult,
    SearchMode,
    hybrid_search,
    reciprocal_rank_fusion,
)
from ragd.search.searcher import SearchResult, SourceLocation, search

__all__ = [
    # Legacy semantic search
    "SearchResult",
    "SourceLocation",
    "search",
    # BM25 keyword search
    "BM25Index",
    "BM25Result",
    # Hybrid search
    "HybridSearcher",
    "HybridSearchResult",
    "SearchMode",
    "hybrid_search",
    "reciprocal_rank_fusion",
]
