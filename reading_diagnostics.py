"""Screen-only diagnostic indicators from telemetry; independent of alerts and ML.

Rules are conservative descriptive checks, not a fault diagnosis, protection system,
or notification. No API writes or persistence are performed.
"""
from math import isfinite

import pandas as pd


def _number(value):
    try:
        result = float(value)
        return result if isfinite(result) else None
    except (TypeError, ValueError):
        return None


def infer_reading_types(rows, nominal_voltage=127, max_results=200):
    """Infer transparent warning candidates from sequential measurements.

    No automatic alerts, backend model, notifications, or persisted classifications.
    Requires measured voltage and current; rolling baseline needs 12 earlier
    valid load samples. The baseline is contextual, not a calibrated limit.
    """
    if not isinstance(rows, list) or not rows:
        return []
    nominal = _number(nominal_voltage)
    if nominal is None or nominal <= 0:
        nominal = 127.0
    voltage_min = 117.0 if nominal == 127 else 202.0 if nominal == 220 else nominal * 0.92
    voltage_max = 133.0 if nominal == 127 else 231.0 if nominal == 220 else nominal * 1.05

    # Process in chronological order, avoiding invalid timestamps and cross-device comparisons.
    valid = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ts = pd.to_datetime(row.get("created_at"), utc=True, errors="coerce")
        if pd.isna(ts):
            continue
        valid.append((ts, row))
    valid.sort(key=lambda x: x[0])

    output, power_history, current_history = [], [], []
    prior_voltage = None
    for _, row in valid:
        voltage = _number(row.get("voltage"))
        current = _number(row.get("current"))
        power = _number(row.get("power"))
        frequency = _number(row.get("frequency"))
        factor = _number(row.get("power_factor"))
        if voltage is None or current is None:
            continue

        types = []
        reasons = []
        if voltage < 0 or current < 0 or (power is not None and power < 0):
            types.append("sensor")
            reasons.append("Medição negativa incompatível com as grandezas esperadas.")
        elif power is not None and power > voltage * current * 1.15 + 15:
            types.append("sensor")
            reasons.append("Potência ativa supera a aparente em mais que a margem de triagem.")

        if voltage < voltage_min and voltage >= 20:
            types.append("subtensao")
            reasons.append(f"Tensão {voltage:.1f} V, abaixo do valor de referência {voltage_min:.1f} V.")
        elif voltage > voltage_max:
            types.append("sobretensao")
            reasons.append(f"Tensão {voltage:.1f} V, acima do valor de referência {voltage_max:.1f} V.")

        # Voltage disappearance is ambiguous: report only a possible power/sensor interruption.
        if prior_voltage is not None and prior_voltage >= voltage_min and voltage < 20:
            types.append("queda")
            reasons.append("Tensão medida caiu de nível habitual para menos de 20 V.")
        if voltage > 20 and frequency is not None and not (59.5 <= frequency <= 60.5):
            types.append("frequencia")
            reasons.append(f"Frequência medida: {frequency:.2f} Hz (faixa de triagem 59,5–60,5 Hz).")
        if voltage >= voltage_min and current > 0.5 and factor is not None and factor < 0.7:
            types.append("fp_baixo")
            reasons.append(f"Fator de potência medido: {factor:.2f}, abaixo de 0,70.")

        # Need a stable historical baseline rather than a single sudden value.
        if power is not None and power >= 0 and len(power_history) >= 12:
            baseline = float(pd.Series(power_history[-60:]).median())
            if baseline >= 100 and power > 2.5 * baseline and power - baseline >= 300:
                types.append("consumo_elevado")
                reasons.append(f"Potência {power:.0f} W versus mediana recente {baseline:.0f} W.")
            elif baseline >= 300 and power < 0.3 * baseline:
                types.append("consumo_baixo")
                reasons.append(f"Potência {power:.0f} W versus mediana recente {baseline:.0f} W.")

        if current >= 0 and len(current_history) >= 12:
            baseline_i = float(pd.Series(current_history[-60:]).median())
            if baseline_i >= 0.5 and current > 3 * baseline_i and current - baseline_i >= 2:
                types.append("sobrecorrente")
                reasons.append(f"Corrente {current:.2f} A versus mediana recente {baseline_i:.2f} A.")

        if types:
            output.append({
                **row, "anomaly_types": list(dict.fromkeys(types)),
                "diagnostic_evidence": " ".join(reasons),
                "diagnostic_origin": "Indício calculado das medições",
            })
        if voltage >= 20 and power is not None and power >= 0 and current >= 0:
            power_history.append(power)
            current_history.append(current)
        prior_voltage = voltage

    # Keep bounded and recent; panel is read-only and never creates an alert.
    return list(reversed(output[-max_results:]))


def indicator_source(row):
    return row.get("diagnostic_origin") or "Classificação registrada pela API"
