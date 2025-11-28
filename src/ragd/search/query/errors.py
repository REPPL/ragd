"""Custom exceptions for query parsing with user-friendly messages.

Provides exceptions that include context for helpful CLI error display:
- Position pointer showing where the error occurred
- Suggestions for how to fix the query
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QueryParseError(Exception):
    """Base exception for query parsing errors.

    Attributes:
        query: The original query string
        message: Human-readable error description
        position: Character position where error occurred (0-indexed)
        suggestion: Optional hint for fixing the query
    """

    query: str
    message: str
    position: int | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        """Return the error message."""
        return self.message

    def user_message(self) -> str:
        """Format error for CLI display with position pointer and suggestion.

        Returns:
            Formatted multi-line error message for terminal display
        """
        lines = [f"Query error: {self.message}"]

        if self.position is not None and self.query:
            lines.append(f"  {self.query}")
            pointer = " " * (self.position + 2) + "^"
            lines.append(pointer)

        if self.suggestion:
            lines.append(f"Suggestion: {self.suggestion}")

        return "\n".join(lines)


@dataclass
class UnbalancedParenthesesError(QueryParseError):
    """Raised when parentheses are not balanced.

    Example:
        "(machine learning" - missing closing parenthesis
    """

    def __init__(
        self,
        query: str,
        message: str = "Unbalanced parentheses",
        position: int | None = None,
    ) -> None:
        super().__init__(
            query=query,
            message=message,
            position=position,
            suggestion="Check that every '(' has a matching ')'",
        )


@dataclass
class EmptyQueryError(QueryParseError):
    """Raised when query is empty or becomes empty after parsing.

    Example:
        "" or "   " - empty query
    """

    def __init__(
        self,
        query: str,
        message: str = "Query cannot be empty",
    ) -> None:
        super().__init__(
            query=query,
            message=message,
            position=None,
            suggestion=None,
        )


@dataclass
class InvalidOperatorError(QueryParseError):
    """Raised when an operator is used incorrectly.

    Examples:
        "AND python" - leading operator
        "python OR" - trailing operator
        "python AND AND test" - consecutive operators
    """

    def __init__(
        self,
        query: str,
        message: str,
        position: int | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(
            query=query,
            message=message,
            position=position,
            suggestion=suggestion,
        )


@dataclass
class InvalidPhraseError(QueryParseError):
    """Raised when a phrase is malformed.

    Example:
        '"unclosed phrase' - missing closing quote
    """

    def __init__(
        self,
        query: str,
        message: str = "Unclosed phrase",
        position: int | None = None,
    ) -> None:
        super().__init__(
            query=query,
            message=message,
            position=position,
            suggestion="Close the phrase with a matching '\"'",
        )
