"""Transform query AST to SQLite FTS5 query syntax.

Converts the parsed AST representation into a string that can be
passed to SQLite FTS5 MATCH clause.
"""

from __future__ import annotations

from ragd.search.query.ast import (
    BinaryNode,
    BooleanOp,
    GroupNode,
    QueryNode,
    TermNode,
    UnaryNode,
)


class FTS5Transformer:
    """Transform query AST to FTS5 query string.

    FTS5 query syntax:
    - Terms are quoted: "term"
    - Phrases: "exact phrase"
    - Prefix: "term"*
    - AND: term1 AND term2
    - OR: term1 OR term2
    - NOT: NOT term
    - Grouping: (expr)
    """

    def transform(self, node: QueryNode) -> str:
        """Convert AST to FTS5 query string.

        Args:
            node: Query AST root node

        Returns:
            FTS5-compatible query string
        """
        return self._visit(node)

    def _visit(self, node: QueryNode) -> str:
        """Visit a node and generate FTS5 syntax.

        Args:
            node: Any query node

        Returns:
            FTS5 query fragment
        """
        if isinstance(node, TermNode):
            return self._visit_term(node)
        elif isinstance(node, BinaryNode):
            return self._visit_binary(node)
        elif isinstance(node, UnaryNode):
            return self._visit_unary(node)
        elif isinstance(node, GroupNode):
            return self._visit_group(node)
        else:
            msg = f"Unknown node type: {type(node)}"
            raise TypeError(msg)

    def _visit_term(self, node: TermNode) -> str:
        """Generate FTS5 term.

        Args:
            node: Term node

        Returns:
            Quoted term, phrase, or prefix pattern
        """
        if node.is_phrase:
            # Phrase: already quoted in source, escape internal quotes
            escaped = node.value.replace('"', '""')
            return f'"{escaped}"'
        elif node.is_prefix:
            # Prefix: quote the base and add wildcard
            clean = self._escape_term(node.value)
            return f'"{clean}"*'
        else:
            # Regular term: quote and escape
            clean = self._escape_term(node.value)
            return f'"{clean}"'

    def _visit_binary(self, node: BinaryNode) -> str:
        """Generate FTS5 binary expression.

        FTS5 NOT syntax: `query1 NOT query2` (no AND before NOT)
        So we handle AND + NOT specially.

        Args:
            node: Binary node (AND/OR)

        Returns:
            Binary expression with operator
        """
        left = self._visit(node.left)

        # Special case: AND with NOT on right side
        # FTS5 syntax is "term1 NOT term2", not "term1 AND NOT term2"
        if node.op == BooleanOp.AND and isinstance(node.right, UnaryNode):
            if node.right.op == BooleanOp.NOT:
                # Generate "term1 NOT term2" instead of "term1 AND NOT term2"
                right_operand = self._visit(node.right.operand)
                return f"({left} NOT {right_operand})"

        right = self._visit(node.right)
        op = node.op.name  # "AND" or "OR"
        return f"({left} {op} {right})"

    def _visit_unary(self, node: UnaryNode) -> str:
        """Generate FTS5 unary expression.

        Note: Standalone NOT is problematic in FTS5. It must be used
        as "term1 NOT term2". The validator warns about standalone NOT.

        Args:
            node: Unary node (NOT)

        Returns:
            NOT expression (may not work standalone in FTS5)
        """
        operand = self._visit(node.operand)
        return f"NOT {operand}"

    def _visit_group(self, node: GroupNode) -> str:
        """Generate FTS5 grouped expression.

        Args:
            node: Group node

        Returns:
            Parenthesised expression
        """
        return f"({self._visit(node.child)})"

    def _escape_term(self, value: str) -> str:
        """Escape special characters for FTS5 quoted term.

        Removes characters that could break FTS5 parsing.
        Preserves alphanumeric, hyphens, and underscores.

        Args:
            value: Raw term value

        Returns:
            Escaped term safe for FTS5
        """
        # Keep alphanumeric, hyphen, underscore
        # Remove everything else that could break FTS5
        return "".join(c for c in value if c.isalnum() or c in "-_")
