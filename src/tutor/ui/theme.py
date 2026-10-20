"""Global CSS: "clean laboratory notebook + interactive engineering diagram" (spec 16).

Only layout, cards for the few elements that need framing, selection states and
touch-friendly sizing. Colours mirror tutor.ui.svg.core so SVG and widgets agree.
"""

from __future__ import annotations

import streamlit as st

from tutor.ui.svg.core import CURRENT, HILITE, HILITE_EDGE, INK, MINUS, MUTED, PLUS, VOLT

CSS = f"""
<style>
:root {{
  --ink: {INK}; --muted: {MUTED}; --volt: {VOLT}; --cur: {CURRENT}; --plus: {PLUS}; --minus: {MINUS};
  --hl: {HILITE}; --hl-edge: {HILITE_EDGE}; --paper: #fbfaf7; --card: #ffffff; --rule: #e4dfd3; --tray: #f4f1e8;
}}
/* pin the light scheme even if Streamlit's theme object arrives late ("System" race) */
html, body, .stApp {{ color-scheme: light; background-color: var(--paper) !important; color: var(--ink); }}

/* notebook paper: faint grid on the main area only */
[data-testid="stMain"] {{
  background-color: var(--paper);
  background-image: linear-gradient(rgba(29,36,48,.035) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(29,36,48,.035) 1px, transparent 1px);
  background-size: 24px 24px;
}}
.block-container {{ padding-top: 3.2rem; padding-bottom: 4rem; max-width: 1240px; }}
h1, h2, h3 {{ font-family: Georgia, Cambria, "Times New Roman", serif !important; color: var(--ink); letter-spacing: -.01em; font-weight: 700 !important; }}
h1 {{ font-size: 2.0rem !important; }}
h2 {{ font-size: 1.45rem !important; }}
h3 {{ font-size: 1.15rem !important; }}

/* touch targets */
.stButton button, [data-testid="stSegmentedControl"] button, [data-testid="stPills"] button {{ min-height: 40px; }}

/* framed regions (used sparingly: visual, inspector, tray, equation strip) */
.st-key-visual, .st-key-inspector, .st-key-tray, .st-key-eqstrip, .st-key-consequence {{
  background: var(--card); border: 1px solid var(--rule); border-radius: 12px; padding: 14px 16px 10px 16px;
}}
.st-key-tray {{ background: var(--tray); }}
.st-key-eqstrip {{ background: #fffdf5; border-left: 5px solid var(--volt); }}
.st-key-inspector {{ border-top: 5px solid var(--ink); }}

/* lesson main row: visual 60 % / inspector 40 %; wraps below ~900 px (tablet) */
.st-key-lessonrow [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 1rem; }}
.st-key-lessonrow [data-testid="stColumn"] {{ min-width: min(100%, 420px); }}
@media (max-width: 900px) {{
  .st-key-lessonrow [data-testid="stColumn"] {{ flex: 1 1 100% !important; width: 100% !important; }}
}}

/* small type helpers */
.mst-kicker {{ font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 0 0 .2rem 0; }}
.mst-problem {{ font-size: 1.12rem; line-height: 1.5; color: var(--ink); margin: .2rem 0 .6rem 0; }}
.mst-problem b {{ color: var(--ink); }}
.mst-muted {{ color: var(--muted); font-size: .9rem; }}
.mst-chip {{ display:inline-block; padding: 2px 9px; border-radius: 999px; font-size: .78rem; font-weight: 700;
            border: 1.5px solid var(--ink); margin-right: 6px; }}
.mst-chip.verified {{ border-color: #15803d; color: #15803d; }}
.mst-chip.supplemental {{ border-color: var(--muted); color: var(--muted); border-style: dashed; }}
.mst-chip.needs_review {{ border-color: #b45309; color: #b45309; background: #fff7e6; }}
.mst-readout {{ font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; font-size: 1.05rem; }}
.mst-big {{ font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; font-size: 1.6rem; font-weight: 700; color: var(--volt); }}

/* sensor-system map */
.mst-map {{ display:flex; flex-wrap: wrap; align-items:center; gap: 4px; margin: .1rem 0 .8rem 0; }}
.mst-map .blk {{ padding: 5px 10px; border: 1.5px solid #cfc9bb; border-radius: 8px; font-size: .8rem; color: var(--muted); background: #fff; }}
.mst-map .blk.on {{ border: 2.5px solid var(--ink); color: var(--ink); font-weight: 800; background: var(--hl); }}
.mst-map .arr {{ color: #b9b2a2; font-size: .9rem; }}
.mst-map .note {{ flex-basis: 100%; font-size: .82rem; color: var(--muted); margin-top: 2px; }}
.mst-map .note b {{ color: var(--ink); }}

/* ---- content boxes (keyed containers holding Markdown + LaTeX) ---- */
[class*="st-key-box-"] {{ border-radius: 10px; padding: 10px 14px 4px 14px; margin: 4px 0 8px 0; border: 2px solid; }}
[class*="st-key-box-hit"] {{ border-color: #15803d; background: #effbf2; }}
[class*="st-key-box-miss"] {{ border-color: #b45309; background: #fff7e6; }}
[class*="st-key-box-flag"] {{ border-color: #b45309; background: #fff7e6; font-size: .95rem; }}
[class*="st-key-box-fail"] {{ border-color: #b91c1c; border-left-width: 8px; background: #fff5f5; }}
[class*="st-key-box-fail"] .mst-boxtitle {{ color: #b91c1c; }}
[class*="st-key-box-analogy"] {{ border: 1.5px dashed var(--muted); background: rgba(255,255,255,.6); }}
[class*="st-key-box-note"] {{ border: 1.5px solid #cfc9bb; background: #ffffff; }}
[class*="st-key-box-predict"] {{ border: 2px dashed var(--volt); background: #fffaf0; }}
[class*="st-key-box-problem"] {{ border: none; padding: 0 0 2px 0; margin: 0; }}
[class*="st-key-box-problem"] p {{ font-size: 1.12rem; line-height: 1.55; }}
.mst-boxtitle {{ font-weight: 800; letter-spacing: .05em; font-size: .76rem; text-transform: uppercase; margin: 0 0 2px 0; }}
.mst-plain {{ background: var(--hl); border-radius: 6px; padding: 4px 10px; display: inline-block; margin: 2px 0 8px 0;
             border: 1px solid var(--hl-edge); }}

/* ---- maths typography: never squint at a subscript, minus sign or Δ ---- */
.stMarkdown .katex {{ font-size: 1.12em; }}
.st-key-eqstrip .katex-display {{ font-size: 1.32em; margin: .35em 0; }}
.st-key-eqstrip .katex-display > .katex {{ font-size: 1em; }}
[class*="st-key-derivstep"] .katex-display {{ font-size: 1.38em; }}
[class*="st-key-eqterms"] button {{ min-width: 52px; }}
[class*="st-key-eqterms"] button .katex {{ font-size: 1.15em; }}
[data-testid="stPills"] .katex {{ font-size: 1.05em; }}

/* mastery badges: shape + text, never colour alone */
.mst-badge {{ display:inline-block; font-size: .74rem; font-weight: 800; padding: 1px 8px; border-radius: 6px; border: 1.5px solid; letter-spacing: .02em; }}
.mst-badge.not_started {{ color: #6b7280; border-style: dotted; }}
.mst-badge.shaky {{ color: #b45309; border-style: dashed; background: #fff7e6; }}
.mst-badge.solid {{ color: #1d5fa8; background: #eef5fd; }}
.mst-badge.exam_ready {{ color: #15803d; background: #effbf2; border-width: 2.5px; }}

/* equation-strip arrows */
.mst-eqarrow {{ text-align:center; color: var(--muted); font-size: 1.4rem; padding-top: .6rem; }}

/* glossary chips: never squeeze labels to "Volt…" */
.st-key-termchips > div {{ flex: 0 0 auto !important; width: auto !important; max-width: none !important; }}
.st-key-termchips button {{ width: max-content !important; max-width: none !important; }}
.st-key-termchips button div, .st-key-termchips button span {{ overflow: visible !important; max-width: none !important; width: auto !important; }}
.st-key-termchips button p {{ white-space: nowrap; overflow: visible; text-overflow: clip; }}
.st-key-eqterms > div {{ flex: 0 0 auto !important; width: auto !important; }}

/* hide the anchor-link icons next to headings */
[data-testid="stHeaderActionElements"] {{ display: none; }}
</style>
"""


def inject() -> None:
    st.html(CSS)


def highlight_controls(control_keys: list[str]) -> None:
    """Emphasise the control(s) linked to the current selection (spec 16.5 step 2)."""
    if not control_keys:
        return
    rules = "\n".join(
        f".st-key-{k} {{ outline: 3px dashed var(--hl-edge); outline-offset: 4px; background: #fff6c9; border-radius: 10px; }}"
        for k in control_keys
    )
    st.html(f"<style>{rules}</style>")
