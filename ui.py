import base64
import html
import re
from pathlib import Path

import streamlit as st

from icons import svg

ASSETS = Path(__file__).parent / "assets"
BANNER_ICONS = {"ok": "check", "warn": "alert", "danger": "x", "info": "info"}


@st.cache_resource
def logo_b64(name: str = "logo.png") -> str:
    return base64.b64encode((ASSETS / name).read_bytes()).decode()


def md(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def brand() -> None:
    md(f'<div class="eg-brand"><img src="data:image/png;base64,{logo_b64()}" alt=""/><span>EnergyGuard</span></div>')


def header(device: str, online: bool, updated: str) -> None:
    kind, label = ("ok", "Online") if online else ("danger", "Offline")
    md(
        '<div class="eg-header">'
        f'<img class="eg-logo" src="data:image/png;base64,{logo_b64()}" alt="EnergyGuard"/>'
        '<div class="eg-head-text"><div class="eg-title">EnergyGuard</div>'
        f'<div class="eg-sub">Monitoramento inteligente de energia · {html.escape(device)}</div></div>'
        '<div class="eg-head-right">'
        f'<span class="eg-pill {kind}"><span class="eg-dot"></span>{label}</span>'
        f'<span class="eg-updated">Atualizado às {html.escape(updated)}</span>'
        "</div></div>"
    )


def section(title: str, icon: str = "chart") -> None:
    md(f'<div class="eg-section">{svg(icon, 22)}<span>{html.escape(title)}</span></div>')


def banner(kind: str, text: str) -> None:
    md(
        f'<div class="eg-banner eg-{kind}">{svg(BANNER_ICONS[kind], 20)}'
        f'<span class="eg-msg">{html.escape(text)}</span></div>'
    )


_UNIT = re.compile(r"^(.*\S)\s+([A-Za-zµΩ]{1,4})$")


def _value_html(value: str) -> str:
    m = _UNIT.match(value)
    if m:
        return f'{html.escape(m.group(1))}<span class="eg-unit">{html.escape(m.group(2))}</span>'
    return html.escape(value)


def cards(items: list[tuple], cols: int | None = None) -> None:
    parts = []
    for item in items:
        label, value, *rest = item
        icon = rest[0] if rest else None
        chip = f'<span class="eg-chip">{svg(icon, 20)}</span>' if icon else ""
        parts.append(
            f'<div class="eg-card">{chip}<div class="eg-body"><div class="eg-label">{html.escape(label)}</div>'
            f'<div class="eg-value">{_value_html(value)}</div></div></div>'
        )
    attrs = f' class="eg-grid eg-fixed" style="--cols:{cols}"' if cols else ' class="eg-grid"'
    md(f"<div{attrs}>{''.join(parts)}</div>")


def sparkline(values: list[float], tone: str) -> str:
    vals = [float(v) for v in values if v is not None]
    if len(vals) < 2:
        return f'<svg class="eg-spark {tone}" viewBox="0 0 100 30" preserveAspectRatio="none"></svg>'
    lo, hi = min(vals), max(vals)
    span = max(hi - lo, max(abs(hi), 1.0) * 0.05)
    step = 100.0 / (len(vals) - 1)
    pts = [(i * step, 27 - (v - lo) / span * 24) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,30 {line} 100,30"
    return (
        f'<svg class="eg-spark {tone}" viewBox="0 0 100 30" preserveAspectRatio="none" aria-hidden="true">'
        f'<polygon points="{area}" fill="currentColor" fill-opacity="0.14"/>'
        f'<polyline points="{line}" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>'
    )


def hero(status: tuple[str, str, str], kpis: list[dict]) -> None:
    kind, title, sub = status
    icon = {"ok": "shield", "warn": "alert", "danger": "x"}[kind]
    parts = [
        f'<div class="eg-status {kind}">{svg(icon, 34)}'
        f'<div class="eg-st-title">{html.escape(title)}</div><div class="eg-st-sub">{html.escape(sub)}</div></div>'
    ]
    for k in kpis:
        parts.append(
            '<div class="eg-kpi"><div class="eg-kpi-top">'
            f'<span class="eg-chip">{svg(k["icon"], 20)}</span><span class="eg-label">{html.escape(k["label"])}</span></div>'
            f'<div class="eg-kpi-val">{html.escape(k["value"])}<span class="eg-unit">{html.escape(k["unit"])}</span></div>'
            f'{sparkline(k["spark"], k["tone"])}</div>'
        )
    md(f'<div class="eg-hero">{"".join(parts)}</div>')


def progress(fraction: float, text: str) -> None:
    pct = max(0.0, fraction) * 100
    over = " over" if fraction > 1 else ""
    md(
        f'<div class="eg-bar{over}"><div style="width:{min(pct, 100):.1f}%"></div></div>'
        f'<div class="eg-label">{html.escape(text)}</div>'
    )


def table(df) -> None:
    md('<div class="eg-scroll">' + df.to_html(index=False, border=0, classes="eg-table", escape=True) + "</div>")


def plot(fig, key: str) -> None:
    st.plotly_chart(fig, theme=None, key=key, config={"displayModeBar": False})


def rerun(auto: bool) -> None:
    st.rerun(scope="fragment") if auto else st.rerun()
