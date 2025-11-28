"""Abstract Syntax Tree for boolean search queries.

Provides dataclasses representing parsed query structure:
- TermNode: Single search term (word, phrase, or prefix)
- BinaryNode: Binary boolean expression (AND, OR)
- UnaryNode: Unary expression (NOT)
- GroupNode: Parenthesised group
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Union


class BooleanOp(Enum):
    """Boolean operators supported in queries."""

    AND = auto()
    OR = auto()
    NOT = auto()


@dataclass
class TermNode:
    """A single search term.

    Attributes:
        value: The term text (without quotes or wildcard)
        is_phrase: True if this is an exact phrase match
        is_prefix: True if this is a prefix wildcard match
    """

    value: str
    is_phrase: bool = False
    is_prefix: bool = False


@dataclass
class BinaryNode:
    """Binary boolean expression.

    Attributes:
        left: Left operand
        op: Boolean operator (AND or OR)
        right: Right operand
    """

    left: "QueryNode"
    op: BooleanOp
    right: "QueryNode"


@dataclass
class UnaryNode:
    """Unary boolean expression.

    Attributes:
        op: Boolean operator (NOT)
        operand: The operand to negate
    """

    op: BooleanOp
    operand: "QueryNode"


@dataclass
class GroupNode:
    """Parenthesised group.

    Attributes:
        child: The grouped expression
    """

    child: "QueryNode"


# Type alias for any query node
QueryNode = Union[TermNode, BinaryNode, UnaryNode, GroupNode]
