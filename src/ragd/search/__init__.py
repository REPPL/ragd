"""Search functionality for ragd.

Provides both semantic search and hybrid search combining
semantic (vector) and keyword (BM25) search, plus multi-modal
image search using vision embeddings.

v0.8.2 additions:
- Cross-encoder reranking for improved precision
- Query decomposition for complex multi-part queries
"""

from ragd.search.bm25 import BM25Index, BM25Result
from ragd.search.decompose import (
    AggregationMethod,
    DecomposedResult,
    DecomposerConfig,
    DecompositionStrategy,
    QueryDecomposer,
    ResultAggregator,
    SubQuery,
    decompose_query,
    get_decomposer,
)
from ragd.search.hybrid import (
    HybridSearcher,
    HybridSearchResult,
    SearchMode,
    hybrid_search,
    reciprocal_rank_fusion,
)
from ragd.search.multimodal import (
    ImageSearchResult,
    check_multimodal_search_available,
    search_images,
    search_images_by_bytes,
    search_similar_images,
)
from ragd.search.rerank import (
    CrossEncoderReranker,
    RerankResult,
    RerankerConfig,
    get_reranker,
    rerank,
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
    # Reranking (F-065)
    "CrossEncoderReranker",
    "RerankResult",
    "RerankerConfig",
    "get_reranker",
    "rerank",
    # Query Decomposition (F-066)
    "QueryDecomposer",
    "DecomposerConfig",
    "DecompositionStrategy",
    "AggregationMethod",
    "SubQuery",
    "DecomposedResult",
    "ResultAggregator",
    "decompose_query",
    "get_decomposer",
    # Multi-modal image search
    "ImageSearchResult",
    "search_images",
    "search_similar_images",
    "search_images_by_bytes",
    "check_multimodal_search_available",
]
