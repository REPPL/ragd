"""Tests for the boolean query parser module.

Tests cover:
- AST node construction
- Query parsing (AND, OR, NOT, phrases, prefixes, groups)
- FTS5 transformation
- Query validation
- Error handling with user-friendly messages
"""

from __future__ import annotations

import pytest

from ragd.search.query import (
    BinaryNode,
    BooleanOp,
    EmptyQueryError,
    FTS5Transformer,
    GroupNode,
    InvalidOperatorError,
    QueryParser,
    QueryParseError,
    QueryValidator,
    TermNode,
    UnaryNode,
    UnbalancedParenthesesError,
    parse_query,
)


class TestTermNode:
    """Tests for TermNode AST node."""

    def test_simple_term(self) -> None:
        """Test simple term creation."""
        node = TermNode(value="python")
        assert node.value == "python"
        assert not node.is_phrase
        assert not node.is_prefix

    def test_phrase_term(self) -> None:
        """Test phrase term creation."""
        node = TermNode(value="machine learning", is_phrase=True)
        assert node.value == "machine learning"
        assert node.is_phrase
        assert not node.is_prefix

    def test_prefix_term(self) -> None:
        """Test prefix term creation."""
        node = TermNode(value="mach", is_prefix=True)
        assert node.value == "mach"
        assert not node.is_phrase
        assert node.is_prefix


class TestQueryParser:
    """Tests for QueryParser."""

    @pytest.fixture
    def parser(self) -> QueryParser:
        """Create parser instance."""
        return QueryParser()

    def test_simple_term(self, parser: QueryParser) -> None:
        """Test parsing a single term."""
        ast = parser.parse("python")
        assert isinstance(ast, TermNode)
        assert ast.value == "python"

    def test_phrase(self, parser: QueryParser) -> None:
        """Test parsing a quoted phrase."""
        ast = parser.parse('"machine learning"')
        assert isinstance(ast, TermNode)
        assert ast.value == "machine learning"
        assert ast.is_phrase

    def test_prefix(self, parser: QueryParser) -> None:
        """Test parsing a prefix wildcard."""
        ast = parser.parse("mach*")
        assert isinstance(ast, TermNode)
        assert ast.value == "mach"
        assert ast.is_prefix

    def test_and_explicit(self, parser: QueryParser) -> None:
        """Test parsing explicit AND."""
        ast = parser.parse("python AND testing")
        assert isinstance(ast, BinaryNode)
        assert ast.op == BooleanOp.AND
        assert isinstance(ast.left, TermNode)
        assert ast.left.value == "python"
        assert isinstance(ast.right, TermNode)
        assert ast.right.value == "testing"

    def test_and_implicit(self, parser: QueryParser) -> None:
        """Test parsing implicit AND (adjacent terms)."""
        ast = parser.parse("python testing")
        assert isinstance(ast, BinaryNode)
        assert ast.op == BooleanOp.AND

    def test_or_operator(self, parser: QueryParser) -> None:
        """Test parsing OR operator."""
        ast = parser.parse("python OR java")
        assert isinstance(ast, BinaryNode)
        assert ast.op == BooleanOp.OR
        assert isinstance(ast.left, TermNode)
        assert ast.left.value == "python"
        assert isinstance(ast.right, TermNode)
        assert ast.right.value == "java"

    def test_not_operator(self, parser: QueryParser) -> None:
        """Test parsing NOT operator."""
        ast = parser.parse("NOT deprecated")
        assert isinstance(ast, UnaryNode)
        assert ast.op == BooleanOp.NOT
        assert isinstance(ast.operand, TermNode)
        assert ast.operand.value == "deprecated"

    def test_combined_not(self, parser: QueryParser) -> None:
        """Test parsing term NOT term."""
        ast = parser.parse("python NOT snake")
        assert isinstance(ast, BinaryNode)
        assert ast.op == BooleanOp.AND
        assert isinstance(ast.right, UnaryNode)
        assert ast.right.op == BooleanOp.NOT

    def test_grouped_expression(self, parser: QueryParser) -> None:
        """Test parsing grouped expression."""
        ast = parser.parse("(a OR b)")
        assert isinstance(ast, GroupNode)
        assert isinstance(ast.child, BinaryNode)
        assert ast.child.op == BooleanOp.OR

    def test_complex_grouped(self, parser: QueryParser) -> None:
        """Test parsing complex grouped expression."""
        ast = parser.parse("(a OR b) AND c")
        assert isinstance(ast, BinaryNode)
        assert ast.op == BooleanOp.AND
        assert isinstance(ast.left, GroupNode)
        assert isinstance(ast.right, TermNode)

    def test_case_insensitive_operators(self, parser: QueryParser) -> None:
        """Test that operators are case-insensitive."""
        # Test lowercase
        ast1 = parser.parse("a and b")
        assert isinstance(ast1, BinaryNode)
        assert ast1.op == BooleanOp.AND

        # Test mixed case
        ast2 = parser.parse("a Or b")
        assert isinstance(ast2, BinaryNode)
        assert ast2.op == BooleanOp.OR

    def test_nested_groups(self, parser: QueryParser) -> None:
        """Test parsing nested groups."""
        ast = parser.parse("((a OR b) AND c)")
        assert isinstance(ast, GroupNode)


class TestQueryParserErrors:
    """Tests for query parser error handling."""

    @pytest.fixture
    def parser(self) -> QueryParser:
        """Create parser instance."""
        return QueryParser()

    def test_empty_query_error(self, parser: QueryParser) -> None:
        """Test empty query raises EmptyQueryError."""
        with pytest.raises(EmptyQueryError):
            parser.parse("")

    def test_whitespace_only_error(self, parser: QueryParser) -> None:
        """Test whitespace-only query raises EmptyQueryError."""
        with pytest.raises(EmptyQueryError):
            parser.parse("   ")

    def test_unbalanced_parens_missing_close(self, parser: QueryParser) -> None:
        """Test missing closing parenthesis."""
        with pytest.raises(UnbalancedParenthesesError):
            parser.parse("(a OR b")

    def test_unbalanced_parens_missing_open(self, parser: QueryParser) -> None:
        """Test missing opening parenthesis."""
        with pytest.raises(UnbalancedParenthesesError):
            parser.parse("a OR b)")

    def test_leading_and_error(self, parser: QueryParser) -> None:
        """Test leading AND raises error."""
        with pytest.raises(InvalidOperatorError) as exc_info:
            parser.parse("AND python")
        assert "cannot start with AND" in str(exc_info.value)

    def test_leading_or_error(self, parser: QueryParser) -> None:
        """Test leading OR raises error."""
        with pytest.raises(InvalidOperatorError) as exc_info:
            parser.parse("OR python")
        assert "cannot start with OR" in str(exc_info.value)

    def test_trailing_and_error(self, parser: QueryParser) -> None:
        """Test trailing AND raises error."""
        with pytest.raises(InvalidOperatorError) as exc_info:
            parser.parse("python AND")
        assert "cannot end with AND" in str(exc_info.value)

    def test_trailing_or_error(self, parser: QueryParser) -> None:
        """Test trailing OR raises error."""
        with pytest.raises(InvalidOperatorError) as exc_info:
            parser.parse("python OR")
        assert "cannot end with OR" in str(exc_info.value)

    def test_error_user_message(self, parser: QueryParser) -> None:
        """Test error provides user-friendly message."""
        try:
            parser.parse("AND python")
        except QueryParseError as e:
            msg = e.user_message()
            assert "Query error:" in msg
            assert "AND python" in msg


class TestFTS5Transformer:
    """Tests for FTS5 query transformation."""

    @pytest.fixture
    def transformer(self) -> FTS5Transformer:
        """Create transformer instance."""
        return FTS5Transformer()

    def test_term_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test term transformation."""
        node = TermNode(value="python")
        result = transformer.transform(node)
        assert result == '"python"'

    def test_phrase_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test phrase transformation."""
        node = TermNode(value="machine learning", is_phrase=True)
        result = transformer.transform(node)
        assert result == '"machine learning"'

    def test_prefix_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test prefix transformation."""
        node = TermNode(value="mach", is_prefix=True)
        result = transformer.transform(node)
        assert result == '"mach"*'

    def test_and_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test AND transformation."""
        node = BinaryNode(
            left=TermNode(value="a"),
            op=BooleanOp.AND,
            right=TermNode(value="b"),
        )
        result = transformer.transform(node)
        assert result == '("a" AND "b")'

    def test_or_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test OR transformation."""
        node = BinaryNode(
            left=TermNode(value="a"),
            op=BooleanOp.OR,
            right=TermNode(value="b"),
        )
        result = transformer.transform(node)
        assert result == '("a" OR "b")'

    def test_not_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test NOT transformation (standalone)."""
        node = UnaryNode(op=BooleanOp.NOT, operand=TermNode(value="x"))
        result = transformer.transform(node)
        assert result == 'NOT "x"'

    def test_and_not_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test AND + NOT transformation (FTS5 syntax)."""
        node = BinaryNode(
            left=TermNode(value="a"),
            op=BooleanOp.AND,
            right=UnaryNode(op=BooleanOp.NOT, operand=TermNode(value="b")),
        )
        result = transformer.transform(node)
        # FTS5 uses "a NOT b", not "a AND NOT b"
        assert result == '("a" NOT "b")'

    def test_group_to_fts5(self, transformer: FTS5Transformer) -> None:
        """Test group transformation."""
        node = GroupNode(
            child=BinaryNode(
                left=TermNode(value="a"),
                op=BooleanOp.OR,
                right=TermNode(value="b"),
            )
        )
        result = transformer.transform(node)
        assert result == '(("a" OR "b"))'


class TestQueryValidator:
    """Tests for query validation."""

    @pytest.fixture
    def validator(self) -> QueryValidator:
        """Create validator instance."""
        return QueryValidator()

    def test_simple_query_valid(self, validator: QueryValidator) -> None:
        """Test simple query passes validation."""
        node = TermNode(value="python")
        result = validator.validate(node, "python")
        assert result.is_valid
        assert len(result.warnings) == 0

    def test_standalone_not_warning(self, validator: QueryValidator) -> None:
        """Test standalone NOT triggers warning."""
        node = UnaryNode(op=BooleanOp.NOT, operand=TermNode(value="x"))
        result = validator.validate(node, "NOT x")
        assert result.is_valid  # Still valid, just warns
        # Warning mentions "Standalone NOT" (capital case)
        assert any("Standalone NOT" in w for w in result.warnings)

    def test_deeply_nested_warning(self, validator: QueryValidator) -> None:
        """Test deeply nested query triggers warning."""
        # Build deeply nested structure
        node: TermNode | GroupNode = TermNode(value="x")
        for _ in range(10):
            node = GroupNode(child=node)

        result = validator.validate(node, "((((((((((x))))))))))")
        assert any("nesting" in w for w in result.warnings)

    def test_term_count(self, validator: QueryValidator) -> None:
        """Test term counting."""
        node = BinaryNode(
            left=TermNode(value="a"),
            op=BooleanOp.AND,
            right=TermNode(value="b"),
        )
        result = validator.validate(node, "a AND b")
        assert result.term_count == 2


class TestParseQueryFunction:
    """Tests for the high-level parse_query function."""

    def test_simple_query(self) -> None:
        """Test simple query transformation."""
        result = parse_query("python")
        assert result == '"python"'

    def test_and_query(self) -> None:
        """Test AND query transformation."""
        result = parse_query("python AND testing")
        assert result == '("python" AND "testing")'

    def test_or_query(self) -> None:
        """Test OR query transformation."""
        result = parse_query("python OR java")
        assert result == '("python" OR "java")'

    def test_not_query(self) -> None:
        """Test NOT query transformation."""
        result = parse_query("python NOT snake")
        assert result == '("python" NOT "snake")'

    def test_phrase_query(self) -> None:
        """Test phrase query transformation."""
        result = parse_query('"machine learning"')
        assert result == '"machine learning"'

    def test_prefix_query(self) -> None:
        """Test prefix query transformation."""
        result = parse_query("mach*")
        assert result == '"mach"*'

    def test_grouped_query(self) -> None:
        """Test grouped query transformation."""
        result = parse_query("(a OR b) AND c")
        assert "OR" in result
        assert "AND" in result

    def test_complex_query(self) -> None:
        """Test complex query transformation."""
        result = parse_query('(Python OR Java) AND "web development" NOT deprecated')
        assert "Python" in result
        assert "Java" in result
        assert "web development" in result
        assert "NOT" in result

    def test_implicit_and(self) -> None:
        """Test implicit AND (adjacent terms)."""
        result = parse_query("python testing tutorial")
        # Should have multiple ANDs
        assert result.count("AND") >= 2
