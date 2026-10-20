"""A dash after closing inline math is rejected; a minus inside math is not."""

from tutor.engine.typography import dash_junctions, separate_dash_junctions


def test_ohm_style_dash_is_caught_and_minus_inside_math_is_not():
    bad = r"$I = \dfrac{V}{R}$ — $R$ is in the denominator."
    assert dash_junctions(bad)
    good = separate_dash_junctions(bad)
    assert dash_junctions(good) == []
    assert r"\dfrac{V}{R}" in good
    assert "—" not in good

    inside = r"one plate carries $+Q$, the other exactly $-Q$."
    assert dash_junctions(inside) == []
    virtual = r"the input $V_-$ (marked $-$) stays put."
    assert dash_junctions(virtual) == []


def test_range_between_two_expressions_becomes_words():
    raw = r"real gain $10^5$–$10^6$"
    fixed = separate_dash_junctions(raw)
    assert dash_junctions(fixed) == []
    assert " to " in fixed
    assert "$10^6$" in fixed


def test_short_symbol_keeps_the_sentence_going():
    raw = r"including the drop across $R_1$ — stays the same."
    fixed = separate_dash_junctions(raw)
    assert dash_junctions(fixed) == []
    assert "$R_1$, stays the same." in fixed


def test_colon_after_a_full_equation_becomes_a_sentence():
    raw = r"It sits in the denominator of $I = V/R$: a bigger bottom number makes the result smaller."
    fixed = separate_dash_junctions(raw)
    assert "$I = V/R$:" not in fixed
    assert "$I = V/R$. A bigger" in fixed
    # A colon after a short symbol is a label, not an operator.
    short = r"the numerator (top, $V$: the push)"
    assert separate_dash_junctions(short) == short


def test_leading_equation_lifts_out_of_the_sentence():
    from tutor.ui.components.prose import blocks

    parts = blocks(r"$I = \dfrac{V}{R}$. $R$ is in the denominator.")
    assert parts[0] == ("math", r"I = \dfrac{V}{R}")
    assert parts[1][0] == "md"
    assert parts[1][1].startswith("$R$")


def test_display_math_is_not_scanned_as_inline():
    text = "$$\nI = V/R\n$$ — this dash is outside display math, after a line break it is fine"
    # The em dash is not on the same inline span. A following prose dash after $$ is not inline.
    assert dash_junctions(text) == []
