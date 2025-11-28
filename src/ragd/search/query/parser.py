"""Boolean query parser using pyparsing.

Parses user search queries into an AST (Abstract Syntax Tree) that can be
transformed into FTS5 syntax. Supports:
- Boolean operators: AND, OR, NOT (case-insensitive)
- Parentheses for grouping
- Quoted phrases: "exact phrase"
- Prefix wildcards: term*
- Implicit AND between adjacent terms
"""

from __future__ import annotations

import pyparsing as pp

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


def _build_term(tokens: pp.ParseResults) -> TermNode:
    """Build a TermNode from parsed token."""
    return tokens[0]


def _build_phrase(tokens: pp.ParseResults) -> TermNode:
    """Build a phrase TermNode from quoted string."""
    # pyparsing QuotedString removes the quotes
    return TermNode(value=tokens[0], is_phrase=True)


def _build_prefix(tokens: pp.ParseResults) -> TermNode:
    """Build a prefix TermNode from word*."""
    # Remove trailing *
    value = tokens[0][:-1]
    return TermNode(value=value, is_prefix=True)


def _build_word(tokens: pp.ParseResults) -> TermNode:
    """Build a simple word TermNode."""
    return TermNode(value=tokens[0])


def _build_not(tokens: pp.ParseResults) -> UnaryNode:
    """Build a NOT UnaryNode."""
    return UnaryNode(op=BooleanOp.NOT, operand=tokens[0])


def _build_group(tokens: pp.ParseResults) -> GroupNode:
    """Build a GroupNode from parenthesised expression."""
    return GroupNode(child=tokens[0])


def _build_binary_chain(tokens: pp.ParseResults, op: BooleanOp) -> QueryNode:
    """Build left-associative chain of binary nodes."""
    result = tokens[0]
    for term in tokens[1:]:
        result = BinaryNode(left=result, op=op, right=term)
    return result


def _build_and_chain(tokens: pp.ParseResults) -> QueryNode:
    """Build AND chain from tokens."""
    return _build_binary_chain(tokens, BooleanOp.AND)


def _build_or_chain(tokens: pp.ParseResults) -> QueryNode:
    """Build OR chain from tokens."""
    return _build_binary_chain(tokens, BooleanOp.OR)


def _create_parser() -> pp.ParserElement:
    """Create the pyparsing grammar for boolean queries.

    Grammar (in order of precedence, highest first):
    - atom: word | phrase | prefix | "(" expr ")"
    - not_expr: "NOT" atom | atom
    - and_expr: not_expr ("AND" not_expr)*
    - or_expr: and_expr ("OR" and_expr)*
    - implicit_and: or_expr+  (adjacent expressions without operator)

    Note: We require explicit AND/OR operators. Adjacent terms are connected
    with implicit AND at the top level.

    Returns:
        pyparsing ParserElement for the complete grammar
    """
    # Suppress whitespace handling - pyparsing does this by default
    pp.ParserElement.enablePackrat()

    # Keywords (case-insensitive, must be whole words)
    # Use CaselessKeyword which requires word boundaries
    AND = pp.CaselessKeyword("AND")
    OR = pp.CaselessKeyword("OR")
    NOT = pp.CaselessKeyword("NOT")

    # Parentheses
    LPAREN = pp.Suppress(pp.Literal("("))
    RPAREN = pp.Suppress(pp.Literal(")"))

    # Term patterns
    # Phrase: "quoted text"
    phrase = pp.QuotedString('"', escChar="\\", unquoteResults=True)
    phrase.setParseAction(_build_phrase)

    # Prefix: word ending with *
    prefix_term = pp.Regex(r"[a-zA-Z0-9_-]+\*")
    prefix_term.setParseAction(_build_prefix)

    # Word: alphanumeric with hyphens/underscores
    # Use negative lookahead to exclude keywords
    word = ~AND + ~OR + ~NOT + pp.Regex(r"[a-zA-Z0-9_-]+")
    word.setParseAction(lambda t: _build_word(t))

    # Forward declaration for recursive grammar
    expr = pp.Forward()

    # Atom: phrase, prefix, word, or grouped expression
    grouped = LPAREN + expr + RPAREN
    grouped.setParseAction(_build_group)
    atom = phrase | prefix_term | word | grouped

    # NOT expression: NOT atom | atom
    not_atom = pp.Suppress(NOT) + atom
    not_atom.setParseAction(_build_not)
    not_expr = not_atom | atom

    # AND expression: not_expr ("AND" not_expr)*
    and_expr = not_expr + pp.ZeroOrMore(pp.Suppress(AND) + not_expr)
    and_expr.setParseAction(_build_and_chain)

    # OR expression: and_expr ("OR" and_expr)*
    or_expr = and_expr + pp.ZeroOrMore(pp.Suppress(OR) + and_expr)
    or_expr.setParseAction(_build_or_chain)

    # Implicit AND: multiple expressions without explicit operators
    # This handles "python testing" as "python AND testing"
    implicit_and = pp.OneOrMore(or_expr)
    implicit_and.setParseAction(_build_and_chain)

    # Complete expression
    expr <<= implicit_and

    return expr


class QueryParser:
    """Parse boolean search queries into AST.

    Thread-safe parser that converts user queries into a structured
    AST representation for further processing.

    Example:
        >>> parser = QueryParser()
        >>> ast = parser.parse('python AND "machine learning"')
        >>> # Returns BinaryNode(TermNode("python"), AND, TermNode("machine learning", is_phrase=True))
    """

    def __init__(self) -> None:
        """Initialise the parser with pyparsing grammar."""
        self._parser = _create_parser()

    def parse(self, query: str) -> QueryNode:
        """Parse query string into AST.

        Args:
            query: User search query

        Returns:
            Root QueryNode of the AST

        Raises:
            QueryParseError: On invalid query syntax
            EmptyQueryError: On empty query
            UnbalancedParenthesesError: On mismatched parentheses
            InvalidOperatorError: On invalid operator usage
        """
        query = query.strip()

        if not query:
            raise EmptyQueryError(query)

        # Pre-validation checks
        self._validate_structure(query)

        try:
            result = self._parser.parseString(query, parseAll=True)
            return result[0]
        except pp.ParseException as e:
            self._handle_parse_error(query, e)

    def _validate_structure(self, query: str) -> None:
        """Validate query structure before parsing.

        Args:
            query: User query string

        Raises:
            UnbalancedParenthesesError: On mismatched parentheses
            InvalidPhraseError: On unclosed quotes
            InvalidOperatorError: On invalid operator position
        """
        # Check parentheses balance
        depth = 0
        for i, char in enumerate(query):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    raise UnbalancedParenthesesError(query, position=i)
        if depth != 0:
            raise UnbalancedParenthesesError(query)

        # Check quote balance
        in_quote = False
        escape_next = False
        for i, char in enumerate(query):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"':
                in_quote = not in_quote

        if in_quote:
            raise InvalidPhraseError(query)

        # Check for leading/trailing operators
        upper = query.upper()
        words = upper.split()

        if words and words[0] in ("AND", "OR"):
            raise InvalidOperatorError(
                query,
                f"Query cannot start with {words[0]}",
                position=0,
                suggestion=f"Remove the leading {words[0]} or add a search term before it",
            )

        if words and words[-1] in ("AND", "OR", "NOT"):
            # Find position of last word
            pos = query.upper().rfind(words[-1])
            raise InvalidOperatorError(
                query,
                f"Query cannot end with {words[-1]}",
                position=pos,
                suggestion="Add a search term after the operator",
            )

    def _handle_parse_error(
        self, query: str, error: pp.ParseException
    ) -> None:
        """Convert pyparsing error to user-friendly exception.

        Args:
            query: Original query
            error: pyparsing exception

        Raises:
            QueryParseError: Always raises with user-friendly message
        """
        # Try to provide helpful context
        raise QueryParseError(
            query=query,
            message=f"Unable to parse query at position {error.loc}",
            position=error.loc,
            suggestion="Try simplifying the query or check for special characters",
        )
