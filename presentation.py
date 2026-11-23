"""Pure UI semantics: device communication state and human-friendly labels."""
from dataclasses import dataclass
from datetime import datetime
from math import isfinite


FONT_SIZES = {"Normal": 16, "Grande": 18, "Extra grande": 20}
TABLE_MODES = ("Resumida", "Completa")
READING_COLUMNS = ("Horário", "Dispositivo", "Tensão (V)", "Corrente (A)",
                   "Potência (W)", "Freq. (Hz)", "Anomalia")
HELP = {
    "power": "Potência em W: uso instantâneo; não é o consumo acumulado.",
    "energy": "Consumo em kWh: quantidade de energia acumulada durante um período.",
    "voltage": "Tensão em V: valor medido na entrada do circuito.",
    "current": "Corrente em A: intensidade da corrente medida.",
    "factor": "Fator de potência: relação entre potência ativa e aparente.",
    "score": "Score do modelo: indicador de comportamento incomum; não é probabilidade de falha.",
}


@dataclass(frozen=True)
class DeviceState:
    code: str
    label: str
    detail: str
    kind: str
    fresh: bool


def device_state(age_seconds: float | None, interval_s: float = 5.0) -> DeviceState:
    """An inference from latest API reading age; not a direct ESP32 presence test."""
    timeout = max(30.0, 3.0 * max(float(interval_s), 1.0))
    if age_seconds is None or not isfinite(age_seconds) or age_seconds < -5:
        return DeviceState("offline", "Sem novas leituras do ESP32",
                           "Não foi possível confirmar quando ocorreu a última leitura.", "danger", False)
    if age_seconds <= timeout:
        return DeviceState("online", "ESP32 enviando leituras",
                           "A comunicação está dentro do intervalo esperado.", "ok", True)
    if age_seconds <= timeout * 2:
        return DeviceState("delayed", "ESP32 com atraso no envio",
                           "As leituras estão atrasadas. Verifique a rede e o dispositivo.", "warn", False)
    return DeviceState("offline", "Sem novas leituras do ESP32",
                       "O dispositivo não envia novas leituras há mais tempo que o esperado.", "danger", False)


def status_time(value: str | None) -> str:
    """Safe display label for ISO timestamps supplied by the API."""
    if not value:
        return "Horário desconhecido"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError, AttributeError):
        return "Horário inválido"


def visible_table_columns(columns, mode: str):
    """Full mode never removes columns; compact mode picks familiar measurements."""
    available = list(columns)
    if mode == "Completa":
        return available
    subset = [col for col in READING_COLUMNS if col in available]
    return subset if subset else available[:7]
