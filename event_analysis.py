"""Read-only event reconstruction from ESP32 telemetry.

Durations are observed sample spans, never proof of continuous outage or damage.
Does not send alerts or write to the backend.
"""
from collections import Counter
from math import isfinite

import pandas as pd


EVENT_LABELS = {
    "queda": "Possível interrupção de tensão",
    "sobretensao": "Tensão elevada",
    "subtensao": "Tensão baixa",
    "sobrecorrente": "Pico de corrente",
    "consumo_elevado": "Pico de potência",
    "consumo_baixo": "Potência abaixo do habitual",
    "frequencia": "Frequência fora da faixa",
    "fp_baixo": "Fator de potência baixo",
    "sensor": "Medição possivelmente inconsistente",
    "comunicacao": "Intervalo sem telemetria",
}


def number(value):
    try:
        n = float(value)
        return n if isfinite(n) else None
    except (ValueError, TypeError):
        return None


def valid_samples(rows):
    """Normalize timestamps, discard invalid entries, sort and collapse duplicates."""
    entries = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        stamp = pd.to_datetime(row.get("created_at"), utc=True, errors="coerce")
        if pd.isna(stamp):
            continue
        entries[stamp] = dict(row)
    return [(stamp, entries[stamp]) for stamp in sorted(entries)]


def sample_codes(row, nominal, baseline_power=None, baseline_current=None):
    """Transparent heuristic flags only, not metrological compliance or a diagnosis."""
    v, c, p = (number(row.get(key)) for key in ("voltage", "current", "power"))
    f, fp = number(row.get("frequency")), number(row.get("power_factor"))
    if v is None or c is None:
        return []
    lower, upper = (117, 133) if nominal == 127 else (202, 231) if nominal == 220 else (nominal * .92, nominal * 1.05)
    codes = []
    if v < 0 or c < 0 or (p is not None and p < 0) or (p is not None and p > v * c * 1.15 + 15):
        codes.append("sensor")
    if 0 <= v < 20:
        codes.append("queda")
    elif v < lower:
        codes.append("subtensao")
    elif v > upper:
        codes.append("sobretensao")
    if v >= 20 and f is not None and not 59.5 <= f <= 60.5:
        codes.append("frequencia")
    if v >= lower and c > .5 and fp is not None and fp < .7:
        codes.append("fp_baixo")
    if p is not None and baseline_power is not None:
        if baseline_power >= 100 and p >= baseline_power * 2.5 and p - baseline_power >= 300:
            codes.append("consumo_elevado")
        elif baseline_power >= 300 and p <= baseline_power * .3:
            codes.append("consumo_baixo")
    if baseline_current is not None and baseline_current >= .5 and c >= baseline_current * 3 and c - baseline_current >= 2:
        codes.append("sobrecorrente")
    return codes


def extract_events(rows, nominal=127, interval_s=5, max_gap_factor=3):
    """Return episodes with observed duration and peak values.

    A gap greater than 3 configured sample intervals splits episodes.
    Gaps are communication uncertainty, NOT established electrical outages.
    """
    samples = valid_samples(rows)
    if not samples:
        return []
    step = max(1., number(interval_s) or 5.)
    permitted_gap = max(3 * step, 10.)
    events = []
    active = {}
    powers, currents = [], []

    def close(code):
        event = active.pop(code)
        event["Duração observada (s)"] = max(
            0., (event["end"] - event["start"]).total_seconds()
        )
        event["Amostras"] = event.pop("count")
        event["Início"] = event.pop("start")
        event["Última amostra"] = event.pop("end")
        event["Tipo"] = EVENT_LABELS[code]
        event["Código"] = code
        event["Interpretação"] = "Indício em leituras; duração entre amostras observadas"
        event["Potência máxima (W)"] = event.pop("power_peak")
        event["Corrente máxima (A)"] = event.pop("current_peak")
        event["Tensão mínima (V)"] = event.pop("voltage_min")
        event["Tensão máxima (V)"] = event.pop("voltage_max")
        events.append(event)

    previous = None
    for stamp, row in samples:
        if previous is not None and (stamp - previous).total_seconds() > permitted_gap:
            for code in list(active):
                close(code)
            gap = (stamp - previous).total_seconds()
            events.append({
                "Início": previous, "Última amostra": stamp,
                "Tipo": EVENT_LABELS["comunicacao"], "Código": "comunicacao",
                "Duração observada (s)": None, "Amostras": 0,
                "Potência máxima (W)": None, "Corrente máxima (A)": None,
                "Tensão mínima (V)": None, "Tensão máxima (V)": None,
                "Interpretação": f"Lacuna de {gap:.0f} s entre leituras; causa não identificada",
            })
            powers.clear()
            currents.clear()

        median_p = float(pd.Series(powers[-60:]).median()) if len(powers) >= 12 else None
        median_c = float(pd.Series(currents[-60:]).median()) if len(currents) >= 12 else None
        found = set(sample_codes(row, nominal, median_p, median_c))
        for code in list(active):
            if code not in found:
                close(code)
        v, c, p = (number(row.get(key)) for key in ("voltage", "current", "power"))
        for code in found:
            if code not in active:
                active[code] = dict(start=stamp, end=stamp, count=0,
                                    power_peak=None, current_peak=None,
                                    voltage_min=None, voltage_max=None)
            record = active[code]
            record["end"] = stamp
            record["count"] += 1
            if p is not None:
                record["power_peak"] = max(p, record["power_peak"]) if record["power_peak"] is not None else p
            if c is not None:
                record["current_peak"] = max(c, record["current_peak"]) if record["current_peak"] is not None else c
            if v is not None:
                record["voltage_min"] = min(v, record["voltage_min"]) if record["voltage_min"] is not None else v
                record["voltage_max"] = max(v, record["voltage_max"]) if record["voltage_max"] is not None else v
        if v is not None and v >= 20 and c is not None and c >= 0 and p is not None and p >= 0:
            powers.append(p)
            currents.append(c)
        previous = stamp
    for code in list(active):
        close(code)
    return sorted(events, key=lambda e: e["Início"], reverse=True)


def event_table(events):
    if not events:
        return pd.DataFrame(columns=["Início", "Última amostra", "Tipo", "Duração observada (s)"])
    return pd.DataFrame(events)


def device_diagnostics(rows, interval_s=5, now=None):
    samples = valid_samples(rows)
    if not samples:
        return {"state": "Sem dados", "last": None, "gap_count": 0, "invalid": 0}
    step = max(1., number(interval_s) or 5.)
    gaps = sum((b[0] - a[0]).total_seconds() > max(3 * step, 10)
               for a, b in zip(samples, samples[1:]))
    invalid = sum(
        (number(row.get("voltage")) is None or number(row.get("current")) is None)
        for _, row in samples
    )
    last = samples[-1][0]
    current = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if current.tzinfo is None:
        current = current.tz_localize("UTC")
    age = (current.tz_convert("UTC") - last).total_seconds()
    limit = max(30., 3 * step)
    state = "Sem novas leituras" if age > 2 * limit or age < -5 else (
        "Com atraso" if age > limit else "Recebendo leituras"
    )
    return {"state": state, "last": last, "gap_count": gaps, "invalid": invalid}


def usual_consumption(rows):
    """Compare first/second time halves at sampling level, NOT energy billing."""
    samples = valid_samples(rows)
    values = [(ts, number(r.get("power"))) for ts, r in samples]
    values = [(t, p) for t, p in values if p is not None and p >= 0]
    if len(values) < 24:
        return {"available": False, "reason": "São necessárias ao menos 24 amostras válidas."}
    half = len(values) // 2
    before = [p for _, p in values[:half]]
    after = [p for _, p in values[half:]]
    old, new = float(pd.Series(before).median()), float(pd.Series(after).median())
    return {"available": True, "before": old, "after": new,
            "change_pct": ((new - old) / old * 100) if old > 0 else None,
            "note": "Mediana de potência da primeira metade versus segunda metade das leituras; "
                    "não é comparação sazonal nem consumo faturado."}


def quality_report(rows, events):
    samples = valid_samples(rows)
    def stats(key):
        nums = [number(r.get(key)) for _, r in samples]
        nums = [x for x in nums if x is not None]
        return {"mínimo": min(nums), "média": sum(nums) / len(nums), "máximo": max(nums)} if nums else None
    return {
        "samples": len(samples), "voltage": stats("voltage"), "frequency": stats("frequency"),
        "events": dict(Counter(x["Tipo"] for x in events)),
        "note": "Resumo das leituras disponíveis, não certificação de qualidade da concessionária.",
    }
