"""Keep punctuation from sitting against rendered mathematics.

A dash immediately after a closing ``$...$`` is drawn by KaTeX as if it were a
minus. ``I = V/R — R is...`` is read as ``I = V/R - R``. Minus signs that live
*inside* a math span are left alone.
"""

from __future__ import annotations

import re

# Hyphen, en dash, em dash. The hyphen is only punctuation when it follows the
# closing dollar; a minus inside ``$-Q$`` never reaches this check.
_DASH = frozenset("-–—")
_RANGE_DASH = frozenset("-–")  # between two math spans: a range, not a sentence
_IMPORTANT = re.compile(r"frac|\\int|\\sum|\\sqrt|=")


def inline_spans(text: str) -> list[tuple[int, int]]:
    """(index of opening ``$``, index of closing ``$``) for inline math. ``$$`` is skipped."""
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("$$", i):
            j = text.find("$$", i + 2)
            if j < 0:
                break
            i = j + 2
            continue
        if text[i] == "$":
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == "$":
                    break
                j += 1
            if j >= n:
                break
            spans.append((i, j))
            i = j + 1
            continue
        i += 1
    return spans


def dash_junctions(text: str) -> list[str]:
    """Snippets where inline math is immediately followed by a dash."""
    found: list[str] = []
    for _start, end in inline_spans(text):
        k = end + 1
        while k < len(text) and text[k] in " \t":
            k += 1
        if k < len(text) and text[k] in _DASH:
            snippet = text[max(0, end - 24): min(len(text), k + 28)].replace("\n", " ")
            found.append(snippet)
    return found


def separate_dash_junctions(text: str) -> str:
    """Rewrite dash-after-math so the dash cannot be read as an operator.

    * An en dash or hyphen between two math spans is a range: ``$10^5$ to $10^6$``.
    * An em dash, or a dash before prose, becomes a new sentence.
    * A colon glued to a full equation (one that contains ``=`` or a fraction)
      becomes a sentence too. A colon after a short symbol is left alone.
    """
    spans = inline_spans(text)
    for start, end in reversed(spans):
        k = end + 1
        while k < len(text) and text[k] in " \t":
            k += 1
        if k >= len(text) or text[k] not in _DASH:
            continue
        dash = text[k]
        rest_at = k + 1
        while rest_at < len(text) and text[rest_at] in " \t":
            rest_at += 1
        rest = text[rest_at:]
        if dash in _RANGE_DASH and rest.startswith("$"):
            text = text[: end + 1] + " to " + rest
            continue
        # A full equation starts a new sentence; the renderer then lifts it.
        # A short symbol only needs the dash gone, so the clause continues.
        # A raw newline would break a YAML folded scalar.
        body = text[start + 1: end]
        if _IMPORTANT.search(body):
            text = text[: end + 1] + ". " + _capitalize(rest)
        else:
            text = text[: end + 1] + ", " + rest
    return separate_colon_after_equation(text)


def separate_colon_after_equation(text: str) -> str:
    """A colon glued to a full equation is an explanation, not part of the formula."""
    spans = inline_spans(text)
    for start, end in reversed(spans):
        if not _IMPORTANT.search(text[start + 1: end]):
            continue
        if end + 1 >= len(text) or text[end + 1] != ":":
            continue
        rest = text[end + 2:]
        if rest.startswith(" "):
            rest = rest[1:]
        text = text[: end + 1] + ". " + _capitalize(rest)
    return text


def _capitalize(rest: str) -> str:
    i = 0
    while rest.startswith("**", i):
        i += 2
    if i < len(rest) and rest[i].isalpha() and rest[i].islower():
        return rest[:i] + rest[i].upper() + rest[i + 1:]
    return rest
