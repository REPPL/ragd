"""Boolean query parsing for ragd search.

This module provides boolean query parsing with user-friendly error
handling and graceful degradation for FTS5-based keyword search.

Supported syntax:
    - AND: Both terms required ("python AND testing")
    - OR: Either term matches ("ML OR machine learning")
    - NOT: Exclude term ("web NOT Django")
    - Parentheses: Group expressions ("(A OR B) AND C")
    - Phrases: Exact match ('"machine learning"')
    - Prefix: Wildcard match ("mach*")

Example:
    >>> from ragd.search.query import parse_query
    >>> fts5_query = parse_query('python AND "machine learning"')
    >>> # Returns: '("python" AND "machine learning")'

For detailed error handling:
    >>> from ragd.search.query import QueryParser, QueryParseError
    >>> parser = QueryParser()
    >>> try:
    ...     ast = parser.parse("AND python")
    ... except QueryParseError as e:
    ...     print(e.user_message())
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ragd.search.query.ast import (
    BinaryNode,
    BooleanOp,
    GroupNode,
    QueryNode,
    TermNode,
    UnaryNode,
)
from ragd.search.query.errors import (
    EmptyQueryError,
    InvalidOperatorError,
    InvalidPhraseError,
    QueryParseError,
    UnbalancedParenthesesError,
)
from ragd.search.query.parser import QueryParser
from ragd.search.query.transformer import FTS5Transformer
from ragd.search.query.validator import QueryValidator, ValidationResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

__all__ = [
    # Main API
    "parse_query",
    # Parser
    "QueryParser",
    # AST nodes
    "QueryNode",
    "TermNode",
    "BinaryNode",
    "UnaryNode",
    "GroupNode",
    "BooleanOp",
    # Transformer
    "FTS5Transformer",
    # Validator
    "QueryValidator",
    "ValidationResult",
    # Errors
    "QueryParseError",
    "UnbalancedParenthesesError",
    "EmptyQueryError",
    "InvalidOperatorError",
    "InvalidPhraseError",
]


def parse_query(query: str, validate: bool = True) -> str:
    """Parse user query and transform to FTS5 syntax.

    This is the main entry point for query parsing. It handles:
    1. Parsing the query into an AST
    2. Validating the query structure (optional warnings)
    3. Transforming the AST to FTS5 syntax

    Args:
        query: User search query string
        validate: Whether to run validation (logs warnings)

    Returns:
        FTS5-compatible query string

    Raises:
        QueryParseError: On invalid query syntax
        EmptyQueryError: On empty query
        UnbalancedParenthesesError: On mismatched parentheses
        InvalidOperatorError: On invalid operator usage

    Example:
        >>> parse_query("python AND testing")
        '("python" AND "testing")'

        >>> parse_query('"machine learning" OR ML')
        '("machine learning" OR "ML")'
    """
    parser = QueryParser()
    transformer = FTS5Transformer()
    validator = QueryValidator()

    # Parse to AST
    ast = parser.parse(query)

    # Optional validation (logs warnings)
    if validate:
        result = validator.validate(ast, query)
        for warning in result.warnings:
            logger.warning("Query warning: %s", warning)

    # Transform to FTS5
    return transformer.transform(ast)


def simple_escape(query: str) -> str:
    """Fallback escaping when parser fails.

    Provides safe escaping for FTS5 by quoting each word.
    This is the original ragd behaviour before boolean support.

    Args:
        query: Raw user query

    Returns:
        Safely escaped FTS5 query with quoted terms
    """
    words = query.split()
    escaped = []
    for word in words:
        # Keep only safe characters
        clean = "".join(c for c in word if c.isalnum() or c in "-_")
        if clean:
            escaped.append(f'"{clean}"')
    return " ".join(escaped)
