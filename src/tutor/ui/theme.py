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

/* touch targets: a finger, not a mouse. manipulation keeps pinch-zoom and drops double-tap zoom. */
html {{ touch-action: manipulation; }}
.stButton button, [data-testid="stButtonGroup"] button, [data-testid="stPills"] button,
[data-testid="stPopover"] button,
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label,
[data-testid="stTopNavSection"], [data-testid="stTopNavLink"],
[data-testid="stExpander"] summary {{ min-height: 44px; }}
.stButton button {{ padding-left: 14px; padding-right: 14px; }}
button[aria-label^="Help for"] {{ min-width: 44px; min-height: 44px; }}
[data-testid="stMain"] input, [data-testid="stMain"] textarea, [data-testid="stMain"] select {{ font-size: 16px !important; }}
[data-testid="stSlider"] [role="group"] > div {{ min-height: 44px; }}
[data-testid="stSlider"] [role="group"] > div > div:nth-child(2) {{ width: 28px !important; height: 28px !important; }}

/* framed regions (used sparingly: visual, inspector, tray, equation strip) */
.st-key-visual, .st-key-inspector, .st-key-tray, .st-key-eqstrip, .st-key-consequence {{
  background: var(--card); border: 1px solid var(--rule); border-radius: 12px; padding: 14px 16px 10px 16px;
}}
.st-key-tray {{ background: var(--tray); }}
.st-key-eqstrip {{ background: #fffdf5; border-left: 5px solid var(--volt); }}
.st-key-inspector {{ border-top: 5px solid var(--ink); }}

/* lesson main row: visual 60 % / inspector 40 %; wraps when a column would be under 420 px */
.st-key-lessonrow [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 1rem; }}
.st-key-lessonrow [data-testid="stColumn"] {{ min-width: min(100%, 420px); }}
/* tablet / iPad portrait: one existing breakpoint, reused everywhere. Landscape above 900 px keeps two columns. */
@media (max-width: 900px) {{
  [data-testid="stMain"] [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
  [data-testid="stMain"] [data-testid="stColumn"] {{
    flex: 1 1 100% !important; width: 100% !important; min-width: 0 !important;
  }}
  .st-key-consequence [data-testid="stColumn"] {{ flex: 1 1 46% !important; width: auto !important; min-width: 148px !important; }}
  .st-key-termchips [data-testid="stColumn"], .st-key-termchips > div,
  .st-key-eqterms [data-testid="stColumn"], .st-key-eqterms > div {{
    flex: 0 0 auto !important; width: auto !important; min-width: 0 !important;
  }}
  .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
  .katex-display {{ overflow-x: auto; overflow-y: hidden; max-width: 100%; }}
  [data-testid="stPlotlyChart"], [data-testid="stImage"] img, .st-key-visual img {{ max-width: 100%; height: auto; }}
}}
.st-key-tray .stButton button p {{ white-space: nowrap; }}

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
.mst-map .blk {{ padding: 5px 10px; border: 1.5px solid #b7b1a4; border-radius: 8px; font-size: .82rem; color: var(--ink); background: #fff; }}
.mst-map .blk.on {{ border: 2.5px solid var(--ink); color: var(--ink); font-weight: 800; background: var(--hl); }}
.mst-map .blk.later {{ border-color: #e4dfd4; background: #f6f4ef; color: var(--ink); font-weight: 500; }}
.mst-map .arr {{ color: #8a8376; font-size: .9rem; }}
.mst-map .note {{ flex-basis: 100%; font-size: .82rem; color: var(--ink); margin-top: 2px; }}
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

/* toast (Lara greeting): stay inside the viewport and use the notebook palette */
[data-testid="stToast"] {{
  max-width: min(22rem, calc(100vw - 1.5rem)) !important;
  background: var(--card) !important; color: var(--ink) !important;
  border: 1.5px solid var(--hl-edge) !important;
}}

/* creator signature: small, muted, outside the teaching area */
.mst-sign {{ margin: 64px 0 4px 0; padding: 14px 0 6px 0; border-top: 1px solid var(--rule); text-align: center;
             font-size: .74rem; letter-spacing: .05em; color: var(--muted); opacity: .85; }}
.mst-sign .short {{ display: none; }}
.mst-sign-inline {{ font-size: .78rem; letter-spacing: .04em; color: var(--muted); margin: .4rem 0 0 0; }}
@media (max-width: 560px) {{ .mst-sign .long {{ display: none; }} .mst-sign .short {{ display: inline; }} }}

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
