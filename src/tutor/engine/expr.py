"""A tiny, safe arithmetic-expression parser.

Content files (formulas, derivation steps, faded-derivation options) contain
machine-readable expressions such as ``"-V0*dR/R/4"``. The spec forbids
``eval()`` on content strings, and ``sympy.sympify`` uses ``eval`` internally,
so this module parses expressions itself and builds either

* a SymPy expression (for algebra checks), or
* a dimension vector (for dimension checks, see :mod:`tutor.engine.dims`).

Grammar (explicit multiplication only)::

    expr  := term (('+' | '-') term)*
    term  := unary (('*' | '/') unary)*
    unary := ('-' | '+') unary | power
    power := atom (('^' | '**') unary)?        # right-associative
    atom  := NUMBER | NAME | NAME '(' expr (',' expr)* ')' | '(' expr ')'
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Union

import sympy as sp


class ExprError(ValueError):
    """Raised for syntax errors or unknown names."""


# --- AST ---------------------------------------------------------------------


@dataclass(frozen=True)
class Num:
    value: Fraction


@dataclass(frozen=True)
class Name:
    name: str


@dataclass(frozen=True)
class Neg:
    arg: "Node"


@dataclass(frozen=True)
class BinOp:
    op: str  # one of + - * / ^
    left: "Node"
    right: "Node"


@dataclass(frozen=True)
class Call:
    func: str
    args: tuple["Node", ...]


Node = Union[Num, Name, Neg, BinOp, Call]

FUNCTIONS = {"sqrt", "sin", "cos", "exp", "log", "abs", "re"}
CONSTANTS = {"pi", "imath"}  # imath = imaginary unit (``i`` would clash with currents)

_TOKEN_RE = re.compile(
    r"\s*(?:(?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)"
    r"|(?P<name>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<op>\*\*|[-+*/^(),]))"
)


def _tokenize(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m or m.end() == pos:
            raise ExprError(f"Unexpected character {text[pos]!r} at position {pos} in {text!r}")
        kind = m.lastgroup
        assert kind is not None
        tokens.append((kind, m.group(kind)))
        pos = m.end()
        # skip trailing whitespace
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return tokens


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.tokens = _tokenize(text)
        self.i = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self) -> tuple[str, str]:
        tok = self.peek()
        if tok is None:
            raise ExprError(f"Unexpected end of expression in {self.text!r}")
        self.i += 1
        return tok

    def expect(self, value: str) -> None:
        kind, val = self.take()
        if val != value:
            raise ExprError(f"Expected {value!r} but found {val!r} in {self.text!r}")

    def parse(self) -> Node:
        node = self.expr()
        if self.peek() is not None:
            raise ExprError(f"Unexpected token {self.peek()[1]!r} in {self.text!r}")  # type: ignore[index]
        return node

    def expr(self) -> Node:
        node = self.term()
        while (tok := self.peek()) is not None and tok[1] in ("+", "-"):
            self.take()
            node = BinOp(tok[1], node, self.term())
        return node

    def term(self) -> Node:
        node = self.unary()
        while (tok := self.peek()) is not None and tok[1] in ("*", "/"):
            self.take()
            node = BinOp(tok[1], node, self.unary())
        return node

    def unary(self) -> Node:
        tok = self.peek()
        if tok is not None and tok[1] == "-":
            self.take()
            return Neg(self.unary())
        if tok is not None and tok[1] == "+":
            self.take()
            return self.unary()
        return self.power()

    def power(self) -> Node:
        base = self.atom()
        tok = self.peek()
        if tok is not None and tok[1] in ("^", "**"):
            self.take()
            return BinOp("^", base, self.unary())
        return base

    def atom(self) -> Node:
        kind, val = self.take()
        if kind == "num":
            return Num(Fraction(val))
        if kind == "name":
            nxt = self.peek()
            if nxt is not None and nxt[1] == "(":
                if val not in FUNCTIONS:
                    raise ExprError(f"Unknown function {val!r} in {self.text!r}")
                self.take()
                args = [self.expr()]
                while (t := self.peek()) is not None and t[1] == ",":
                    self.take()
                    args.append(self.expr())
                self.expect(")")
                return Call(val, tuple(args))
            return Name(val)
        if val == "(":
            node = self.expr()
            self.expect(")")
            return node
        raise ExprError(f"Unexpected token {val!r} in {self.text!r}")


def parse(text: str) -> Node:
    """Parse ``text`` into an AST. Raises :class:`ExprError` on bad input."""
    if not isinstance(text, str) or not text.strip():
        raise ExprError("Empty expression")
    return _Parser(text).parse()


def names(node: Node) -> set[str]:
    """All free identifiers in an AST (excluding constants)."""
    if isinstance(node, Name):
        return set() if node.name in CONSTANTS else {node.name}
    if isinstance(node, Neg):
        return names(node.arg)
    if isinstance(node, BinOp):
        return names(node.left) | names(node.right)
    if isinstance(node, Call):
        out: set[str] = set()
        for a in node.args:
            out |= names(a)
        return out
    return set()


def const_value(node: Node) -> Fraction | None:
    """Value of a purely numeric sub-expression, else ``None``."""
    if isinstance(node, Num):
        return node.value
    if isinstance(node, Neg):
        v = const_value(node.arg)
        return None if v is None else -v
    if isinstance(node, BinOp):
        a, b = const_value(node.left), const_value(node.right)
        if a is None or b is None:
            return None
        if node.op == "+":
            return a + b
        if node.op == "-":
            return a - b
        if node.op == "*":
            return a * b
        if node.op == "/":
            return None if b == 0 else a / b
        if node.op == "^" and b.denominator == 1:
            return a ** int(b) if not (a == 0 and b < 0) else None
    return None


# --- SymPy conversion --------------------------------------------------------

_SP_FUNCS = {
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "exp": sp.exp,
    "log": sp.log,
    "abs": sp.Abs,
    "re": sp.re,
}


def to_sympy(node: Node | str, symbols: dict[str, sp.Symbol] | None = None) -> sp.Expr:
    """Convert an AST (or expression string) into a SymPy expression.

    Unknown names become positive real symbols unless ``symbols`` provides them.
    """
    if isinstance(node, str):
        node = parse(node)
    if symbols is None:
        symbols = {}

    def conv(n: Node) -> sp.Expr:
        if isinstance(n, Num):
            return sp.Rational(n.value.numerator, n.value.denominator)
        if isinstance(n, Name):
            if n.name == "pi":
                return sp.pi
            if n.name == "imath":
                return sp.I
            if n.name not in symbols:
                symbols[n.name] = sp.Symbol(n.name, positive=True)
            return symbols[n.name]
        if isinstance(n, Neg):
            return -conv(n.arg)
        if isinstance(n, BinOp):
            a, b = conv(n.left), conv(n.right)
            return {
                "+": lambda: a + b,
                "-": lambda: a - b,
                "*": lambda: a * b,
                "/": lambda: a / b,
                "^": lambda: a**b,
            }[n.op]()
        if isinstance(n, Call):
            return _SP_FUNCS[n.func](*[conv(a) for a in n.args])
        raise ExprError(f"Cannot convert node {n!r}")

    return conv(node)


def equivalent(a: str, b: str) -> bool:
    """True if two expression strings are algebraically identical."""
    syms: dict[str, sp.Symbol] = {}
    ea, eb = to_sympy(a, syms), to_sympy(b, syms)
    return sp.simplify(ea - eb) == 0
