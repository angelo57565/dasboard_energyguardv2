from string import Template

from icons import TAB_ICONS, mask_url

THEMES = {
    "dark": dict(
        bg="#080D18", surface="#121C2E", surface2="#19253A", field="#172238", text="#EDF3FD", muted="#A9BED7",
        border="#30415D", accent="#4CA7FF", accent2="#FFD166", accent_text="#051329", focus="#FFD166",
        ok="#36D9A0", ok_bg="#0B2E28", warn="#FFD166", warn_bg="#322809", danger="#FF8797", danger_bg="#371923",
        info="#3AA0FF", info_bg="#0E2340", shadow="0 10px 28px rgba(0,0,0,.38)", bw="1px", fs="1rem", radius="14px",
    ),
    "light": dict(
        bg="#F5F7FC", surface="#FFFFFF", surface2="#EBF0F8", field="#FFFFFF", text="#15243A", muted="#405673",
        border="#BCC9DA", accent="#175CD3", accent2="#8C5600", accent_text="#FFFFFF", focus="#C04A00",
        ok="#096B50", ok_bg="#E0F5ED", warn="#8C5600", warn_bg="#FFF0C7", danger="#A42237", danger_bg="#FFE8EC",
        info="#0B3DDB", info_bg="#E3EAFF", shadow="none", bw="2px", fs="1.06rem", radius="12px",
    ),
}

PLOT = {
    "dark": dict(template="plotly_dark", text="#EAF0FA", grid="#30415D", paper="rgba(0,0,0,0)",
                 voltage="#3AA0FF", current="#FFC83D", power="#34D399", anomaly="#FF5C7A", width=2.0,
                 apparent="#B794F6", reactive="#F687B3", bar="#3AA0FF", fill=0.10),
    "light": dict(template="plotly_white", text="#000000", grid="#BCC9DA", paper="#FFFFFF",
                  voltage="#0B3DDB", current="#8A4B00", power="#006B3C", anomaly="#C00000", width=2.8,
                  apparent="#5B21B6", reactive="#9D174D", bar="#0B3DDB", fill=0.08),
}

_CSS = Template(r"""
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
  background: $bg !important; color: $text !important; font-size: $fs;
}
[data-testid="stMainBlockContainer"], .block-container { max-width: 1240px; margin: 0 auto; padding: 1.6rem 1.4rem 3rem !important; }
[data-stale="true"] { opacity: 1 !important; transition: none !important; }
[data-testid="stStatusWidget"] { visibility: hidden; }
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background: $surface !important; border-right: $bw solid $border; }

.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label, .stApp small,
.stApp [data-testid="stWidgetLabel"] p, .stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCaptionContainer"] { color: $text !important; }
.stApp [data-testid="stCaptionContainer"] { color: $muted !important; }
.stApp a { color: $accent !important; text-decoration: underline; }

input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="base-input"] {
  background: $field !important; color: $text !important; border-color: $border !important; border-radius: 10px !important;
}
input, textarea { -webkit-text-fill-color: $text !important; }
[data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] svg { color: $text !important; fill: $text !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] { background: $field !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] li * { color: $text !important; }

.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 10px; font-weight: 700; min-height: 2.7rem; width: 100%;
  background: $surface2 !important; color: $text !important; border: $bw solid $border !important;
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
.stButton > button *, .stDownloadButton > button *, [data-testid="stFormSubmitButton"] > button * { color: inherit !important; }
.stButton > button[data-testid*="Button-primary"], [data-testid="stFormSubmitButton"] > button[data-testid*="primary"] {
  background: $accent !important; color: $accent_text !important; border-color: $accent !important;
}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-1px); filter: brightness(1.1); }
.stButton > button:disabled, .stDownloadButton > button:disabled { opacity: .65; }
:focus-visible { outline: 3px solid $focus !important; outline-offset: 2px; }

[data-testid="stTabs"] [role="tablist"] { gap: 4px; border-bottom: $bw solid $border; flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; }
[data-testid="stTabs"] button[role="tab"] { padding: 10px 14px; border-radius: 10px 10px 0 0; transition: background .15s ease; }
[data-testid="stTabs"] button[role="tab"]:hover { background: $surface2; }
[data-testid="stTabs"] button[role="tab"] p { color: $muted !important; font-weight: 700; margin: 0; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p { color: $text !important; }
[data-baseweb="tab-highlight"] { background: $accent !important; height: 3px !important; border-radius: 3px; }
[data-baseweb="tab-border"] { background: transparent !important; }
[data-testid="stTabs"] [role="tablist"] button[role="tab"]::before {
  content: ""; display: inline-block; width: 18px; height: 18px; margin-right: 8px; vertical-align: -3px;
  background-color: currentColor; -webkit-mask-size: contain; mask-size: contain;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center; opacity: .9;
}
[data-testid="stTabs"] button[role="tab"] { color: $muted; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: $accent; }
[data-testid="stTabs"] [data-testid="stTabs"] [role="tablist"] button[role="tab"]::before { display: none; }

[data-testid="stExpander"] details { border: $bw solid $border !important; background: $surface !important; border-radius: $radius; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: $text !important; }

.eg-ico { flex: none; }
.eg-brand { display: flex; align-items: center; gap: 10px; margin: 2px 0 14px; }
.eg-brand img { width: 38px; height: 38px; border-radius: 10px; }
.eg-brand span { font-size: 1.15em; font-weight: 800; color: $text; letter-spacing: .2px; }

.eg-header { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; padding: 14px 16px; margin-bottom: 14px;
  background: $surface; border: $bw solid $border; border-radius: $radius; box-shadow: $shadow; }
.eg-logo { width: 54px; height: 54px; border-radius: 14px; }
.eg-head-text { flex: 1 1 220px; min-width: 0; }
.eg-title { font-size: 1.55em; font-weight: 800; line-height: 1.15; color: $text; }
.eg-sub { color: $muted; font-size: .92em; margin-top: 2px; }
.eg-head-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.eg-updated { color: $muted; font-size: .85em; white-space: nowrap; }

.eg-pill { display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; border-radius: 999px; font-weight: 700; font-size: .88em; border: 2px solid; }
.eg-pill.ok { color: $ok; background: $ok_bg; border-color: $ok; }
.eg-pill.danger { color: $danger; background: $danger_bg; border-color: $danger; }
.eg-pill.warn { color: $warn; background: $warn_bg; border-color: $warn; }
.eg-dot { width: 9px; height: 9px; border-radius: 50%; background: currentColor; }
.eg-pill.ok .eg-dot { animation: eg-live 1.8s ease-in-out infinite; }
@keyframes eg-live { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }

.eg-section { display: flex; align-items: center; gap: 10px; margin: 22px 0 10px; color: $text; font-weight: 800; font-size: 1.12em; }
.eg-section .eg-ico { color: $accent; }

.eg-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 6px 0 14px; }
.eg-grid.eg-fixed { grid-template-columns: repeat(var(--cols, 4), minmax(0, 1fr)); }
.eg-card { display: flex; gap: 12px; align-items: center; background: $surface; border: $bw solid $border; border-radius: $radius; padding: 13px 15px;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
.eg-card:hover { transform: translateY(-2px); box-shadow: $shadow; border-color: $accent; }
.eg-card .eg-body { min-width: 0; flex: 1; }
.eg-chip { display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; flex: none;
  border-radius: 11px; background: $info_bg; color: $accent; }
.eg-label { color: $muted; font-size: .84em; font-weight: 700; }
.eg-value { color: $text; font-size: 1.3em; font-weight: 800; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.eg-unit { font-size: .62em; font-weight: 700; color: $muted; margin-left: 4px; }

.eg-hero { display: grid; grid-template-columns: 1.25fr repeat(3, minmax(0, 1fr)); gap: 12px; margin: 4px 0 8px; }
.eg-status { display: flex; flex-direction: column; justify-content: center; gap: 8px; padding: 18px; border: 2px solid; border-radius: $radius; }
.eg-status.ok { background: $ok_bg; border-color: $ok; color: $ok; }
.eg-status.warn { background: $warn_bg; border-color: $warn; color: $warn; }
.eg-status.danger { background: $danger_bg; border-color: $danger; color: $danger; }
.eg-status .eg-st-title { font-size: 1.3em; font-weight: 800; line-height: 1.2; }
.eg-status .eg-st-sub { font-size: .9em; opacity: .95; }
.eg-kpi { background: $surface; border: $bw solid $border; border-radius: $radius; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
.eg-kpi:hover { transform: translateY(-2px); box-shadow: $shadow; border-color: $accent; }
.eg-kpi-top { display: flex; align-items: center; gap: 10px; }
.eg-kpi-val { font-size: 2.1em; font-weight: 800; line-height: 1.15; color: $text; white-space: nowrap; }
.eg-spark { width: 100%; height: 38px; margin-top: 4px; }
.eg-spark.c1 { color: $accent; } .eg-spark.c2 { color: $accent2; } .eg-spark.c3 { color: $ok; }

.stApp .eg-banner { display: flex; align-items: flex-start; gap: 10px; border: 2px solid; border-radius: 12px; padding: 11px 14px; margin: 6px 0 12px; font-weight: 700; }
.stApp .eg-banner span.eg-msg { padding-top: 1px; }
.stApp .eg-ok { color: $ok !important; background: $ok_bg; border-color: $ok; }
.stApp .eg-warn { color: $warn !important; background: $warn_bg; border-color: $warn; }
.stApp .eg-danger { color: $danger !important; background: $danger_bg; border-color: $danger; }
.stApp .eg-info { color: $info !important; background: $info_bg; border-color: $info; }

.eg-bar { background: $surface2; border: $bw solid $border; border-radius: 999px; height: 16px; overflow: hidden; margin: 6px 0 4px; }
.eg-bar > div { background: $accent; height: 100%; border-radius: 999px; transition: width .4s ease; }
.eg-bar.over > div { background: $danger; }

.eg-scroll { overflow-x: auto; margin-bottom: 10px; border: $bw solid $border; border-radius: $radius; }
.eg-table { width: 100%; border-collapse: collapse; }
.eg-table th { background: $surface2; color: $text; padding: 9px 12px; text-align: left; white-space: nowrap; border-bottom: $bw solid $border; font-size: .9em; }
.eg-table td { color: $text; padding: 9px 12px; white-space: nowrap; border-bottom: $bw solid $border; font-size: .93em; }
.eg-table tr:last-child td { border-bottom: none; }
.eg-table tbody tr:hover td { background: $surface; }

@media (max-width: 1000px) {
  .eg-hero { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .eg-hero .eg-status { grid-column: 1 / -1; }
}
@media (max-width: 800px) {
  .eg-grid.eg-fixed { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  [data-testid="stMainBlockContainer"], .block-container { padding: 1rem .8rem 2.5rem !important; }
  .eg-title { font-size: 1.3em; }
}
@media (max-width: 520px) {
  .eg-hero { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .eg-hero .eg-kpi:last-child { grid-column: 1 / -1; }
  .eg-kpi-val { font-size: 1.7em; }
  .eg-kpi { padding: 12px; }
  .eg-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
  .eg-card { padding: 11px 12px; }
  .eg-card .eg-chip { display: none; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
""")


def _tab_icon_css() -> str:
    rules = []
    for i, name in enumerate(TAB_ICONS, start=1):
        url = mask_url(name)
        rules.append(
            f'[data-testid="stTabs"] [role="tablist"] button[role="tab"]:nth-of-type({i})::before '
            f"{{ -webkit-mask-image: {url}; mask-image: {url}; }}"
        )
    return "\n".join(rules)


_UX_CSS = r"""
/* Consistent scalable typography and keyboard accessibility */
html, body, .stApp { font-size: VAR_FONT_SIZE !important; }
.stApp [data-testid="stMarkdownContainer"], .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp [data-baseweb="select"], .stApp [data-testid="stDataFrame"] {
  font-size: 1rem !important;
}
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stCaptionContainer"] {
  font-size: .91rem !important;
}
.stApp button { min-height: 44px; }
.stApp :focus-visible { outline: 3px solid VAR_FOCUS !important; outline-offset: 3px; }
.eg-hero .eg-kpi-val { font-size: clamp(1.5rem, 2.3vw, 2.25rem); white-space: normal; overflow-wrap: anywhere; }
.eg-card .eg-value { font-size: 1.28rem; white-space: normal; overflow-wrap: anywhere; }
.eg-section { font-size: 1.16rem; }
.eg-title { font-size: clamp(1.25rem, 2.8vw, 1.75rem); }
.eg-header { border-radius: 18px; padding: 18px 20px; }
.eg-card, .eg-kpi { border-radius: 15px; }
.eg-status { min-height: 148px; }
.eg-connection-info { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
.eg-connection-info strong { color: VAR_TEXT; font-weight: 750; }
.eg-connection-panel { padding: 16px 20px; border: 2px solid VAR_BORDER; border-radius: 16px;
  background: VAR_SURFACE; margin: 12px 0 18px; }
.eg-connection-panel.ok { border-left: 5px solid VAR_OK; }
.eg-connection-panel.warn { border-left: 5px solid VAR_WARN; }
.eg-connection-panel.danger { border-left: 5px solid VAR_DANGER; }
.eg-connection-panel.info { border-left: 5px solid VAR_ACCENT; }
.eg-connection-title { display: flex; align-items: center; gap: 9px; font-size: 1.09rem; font-weight: 800; }
.eg-connection-description { color: VAR_MUTED; margin-top: 6px; line-height: 1.6; }
.eg-secondary { color: VAR_MUTED; font-size: .91rem; }
.eg-timestamp { font-variant-numeric: tabular-nums; }
.eg-simple-help { padding: 10px 14px; background: VAR_SURFACE2;
  border-radius: 12px; margin: 10px 0; color: VAR_TEXT; }
.eg-data-note { border-left: 4px solid VAR_WARN; padding: 9px 12px;
  background: VAR_SURFACE2; margin: 10px 0; color: VAR_TEXT; border-radius: 7px; }
[data-testid="stDataFrame"] { border: 1px solid VAR_BORDER; border-radius: 12px; overflow: hidden; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] { font-weight: 700; }
@media (max-width: 640px) {
  .eg-header { padding: 14px; }
  .eg-status { min-height: auto; }
  .eg-hero { grid-template-columns: 1fr; }
  .eg-hero .eg-kpi:last-child { grid-column: auto; }
  .eg-grid.eg-fixed { grid-template-columns: repeat(1, minmax(0, 1fr)); }
}
"""


def build_css(name: str, font_px: int = 16) -> str:
    """Theme CSS with a per-session user-selected scalable type size."""
    if name not in THEMES:
        name = "dark"
    font_px = font_px if font_px in (16, 18, 20) else 16
    tokens = THEMES[name]
    extra = (_UX_CSS.replace("VAR_FONT_SIZE", f"{font_px}px")
             .replace("VAR_FOCUS", tokens["focus"])
             .replace("VAR_TEXT", tokens["text"])
             .replace("VAR_MUTED", tokens["muted"])
             .replace("VAR_BORDER", tokens["border"])
             .replace("VAR_SURFACE2", tokens["surface2"])
             .replace("VAR_SURFACE", tokens["surface"])
             .replace("VAR_OK", tokens["ok"])
             .replace("VAR_WARN", tokens["warn"])
             .replace("VAR_DANGER", tokens["danger"])
             .replace("VAR_ACCENT", tokens["accent"]))
    return "<style>" + _CSS.substitute(tokens) + "\n" + _tab_icon_css() + "\n" + extra + "</style>"
