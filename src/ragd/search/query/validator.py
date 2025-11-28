"""Query validation with warnings for complex or problematic queries.

Validates parsed queries and provides warnings (not errors) for
patterns that may indicate issues or performance concerns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ragd.search.query.ast import (
    BinaryNode,
    BooleanOp,
    GroupNode,
    QueryNode,
    TermNode,
    UnaryNode,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of query validation.

    Attributes:
        is_valid: Whether the query is valid (always True if parsing succeeded)
        warnings: List of warning messages for the user
        term_count: Number of terms in the query
        max_depth: Maximum nesting depth
    """

    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)
    term_count: int = 0
    max_depth: int = 0


class QueryValidator:
    """Validate query AST and provide warnings.

    Checks for patterns that may cause issues:
    - Deeply nested expressions (> 5 levels)
    - Double negation (NOT NOT)
    - High term count (> 20 terms)
    - Single NOT query (FTS5 limitation)
    """

    # Thresholds for warnings
    MAX_DEPTH_WARNING = 5
    MAX_TERMS_WARNING = 20

    def validate(self, node: QueryNode, original_query: str) -> ValidationResult:
        """Validate query AST and collect warnings.

        Args:
            node: Parsed query AST
            original_query: Original user query string (for context)

        Returns:
            ValidationResult with warnings and metrics
        """
        warnings: list[str] = []

        # Calculate metrics
        depth = self._max_depth(node)
        term_count = self._count_terms(node)

        # Check for deeply nested expressions
        if depth > self.MAX_DEPTH_WARNING:
            warnings.append(
                f"Query has {depth} levels of nesting. "
                "Consider simplifying for better readability."
            )

        # Check for double negation
        if self._has_double_negation(node):
            warnings.append(
                "Double negation detected. "
                "Consider removing redundant NOT operators."
            )

        # Check for high term count
        if term_count > self.MAX_TERMS_WARNING:
            warnings.append(
                f"Query has {term_count} terms. "
                "Very complex queries may have slower performance."
            )

        # Check for standalone NOT (FTS5 limitation)
        if self._is_standalone_not(node):
            warnings.append(
                "Standalone NOT queries have limited support in FTS5. "
                "Consider adding a positive term: 'term1 NOT term2'."
            )

        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            term_count=term_count,
            max_depth=depth,
        )

    def _max_depth(self, node: QueryNode, current: int = 0) -> int:
        """Calculate maximum nesting depth.

        Args:
            node: Current node
            current: Current depth level

        Returns:
            Maximum depth found
        """
        if isinstance(node, TermNode):
            return current
        elif isinstance(node, BinaryNode):
            return max(
                self._max_depth(node.left, current + 1),
                self._max_depth(node.right, current + 1),
            )
        elif isinstance(node, UnaryNode):
            return self._max_depth(node.operand, current + 1)
        elif isinstance(node, GroupNode):
            return self._max_depth(node.child, current + 1)
        return current

    def _has_double_negation(self, node: QueryNode) -> bool:
        """Check for NOT NOT patterns.

        Args:
            node: Current node

        Returns:
            True if double negation found
        """
        if isinstance(node, UnaryNode):
            if isinstance(node.operand, UnaryNode):
                return True
            return self._has_double_negation(node.operand)
        elif isinstance(node, BinaryNode):
            return self._has_double_negation(node.left) or self._has_double_negation(
                node.right
            )
        elif isinstance(node, GroupNode):
            return self._has_double_negation(node.child)
        return False

    def _count_terms(self, node: QueryNode) -> int:
        """Count total terms in query.

        Args:
            node: Current node

        Returns:
            Number of term nodes
        """
        if isinstance(node, TermNode):
            return 1
        elif isinstance(node, BinaryNode):
            return self._count_terms(node.left) + self._count_terms(node.right)
        elif isinstance(node, UnaryNode):
            return self._count_terms(node.operand)
        elif isinstance(node, GroupNode):
            return self._count_terms(node.child)
        return 0

    def _is_standalone_not(self, node: QueryNode) -> bool:
        """Check if query is a standalone NOT (FTS5 limitation).

        FTS5 does not support queries like "NOT term" without a positive term.

        Args:
            node: Root node

        Returns:
            True if query is just NOT term(s)
        """
        if isinstance(node, UnaryNode) and node.op == BooleanOp.NOT:
            return True
        if isinstance(node, GroupNode):
            return self._is_standalone_not(node.child)
        return False
