"""Interpret backend anomaly types without inventing electrical fault causes.

A classification is a triage hypothesis, NOT a verified diagnosis of the installation.
Only types returned by the FastAPI backend are used.
"""
from collections import Counter
from datetime import datetime
from math import isfinite
from zoneinfo import ZoneInfo

import pandas as pd

LOCAL_TZ = "America/Sao_Paulo"

# Levels indicate review priority only, NOT risk of physical damage or incident severity.
CATALOG = {
    "queda": ("Possível interrupção de energia", "Alta",
              "Queda brusca das grandezas monitoradas; também pode indicar falha ou ausência de sinal do sensor.",
              "Confira o fornecimento, disjuntores e o funcionamento dos sensores."),
    "sobretensao": ("Tensão acima do limite configurado", "Alta",
                    "Tensão registrada acima da faixa definida para este dispositivo.",
                    "Confirme a tensão com instrumento adequado e procure assistência qualificada se persistir."),
    "subtensao": ("Tensão abaixo do limite configurado", "Alta",
                   "Tensão registrada abaixo da faixa definida para este dispositivo.",
                   "Confira a alimentação e a tensão com um instrumento de referência."),
    "sobrecorrente": ("Corrente elevada ou pico", "Alta",
                      "A corrente medida teve comportamento acima do padrão estabelecido.",
                      "Revise a carga conectada e o dimensionamento com profissional habilitado."),
    "consumo_elevado": ("Potência / consumo acima do habitual", "Atenção",
                        "A potência medida está acima do comportamento considerado normal pelo sistema.",
                        "Compare aparelhos ligados e horários. Isso não demonstra desvio de energia."),
    "consumo_baixo": ("Potência / consumo abaixo do habitual", "Atenção",
                      "A potência medida ficou abaixo do comportamento esperado.",
                      "Verifique se cargas foram desligadas ou se houve interrupção parcial."),
    "frequencia": ("Frequência fora da faixa", "Alta",
                   "A frequência elétrica informada pelo sensor ficou fora da faixa configurada.",
                   "Verifique a qualidade da medição e procure avaliação técnica se recorrente."),
    "fp_baixo": ("Fator de potência baixo", "Atenção",
                 "A relação entre potência ativa e aparente ficou abaixo da regra utilizada.",
                 "Investigue as características das cargas, sem presumir desperdício ou defeito."),
    "sensor": ("Possível inconsistência do sensor", "Alta",
               "As grandezas foram consideradas fisicamente incoerentes pelo sistema.",
               "Verifique conexões, calibração e integridade da cadeia de medição."),
    "incomum": ("Comportamento incomum sem causa identificada", "Analisar",
                "O modelo identificou um padrão diferente, mas não determinou a causa.",
                "Examine o histórico e compare com o funcionamento conhecido da instalação."),
}
PRIORITY_ORDER = {"Alta": 0, "Atenção": 1, "Analisar": 2}
FALLBACK = ("Anomalia sem classificação técnica", "Analisar",
            "A API sinalizou uma anomalia sem fornecer um tipo conhecido.",
            "Revise a leitura e os motivos disponíveis; não conclua uma causa automaticamente.")


def codes_for(row: dict) -> list[str]:
    """Normalize backend codes; never infer a code from power/voltage values alone."""
    values = row.get("anomaly_types")
    if not isinstance(values, list):
        return []
    return list(dict.fromkeys(v for v in values if isinstance(v, str) and v.strip()))


def category(code: str) -> tuple[str, str, str, str]:
    """Keep unknown backend codes visible without treating them as confirmed causes."""
    return CATALOG.get(code, FALLBACK)


def classification_for(row: dict) -> list[dict]:
    codes = codes_for(row) or [""]
    result = []
    for code in codes:
        label, priority, evidence, recommendation = category(code)
        result.append({"code": code, "label": label, "priority": priority,
                       "evidence": evidence, "recommendation": recommendation})
    return result


def overview_by_type(rows: list[dict]) -> pd.DataFrame:
    """Count one reading in every type returned by the backend; no exclusive categories."""
    counts = Counter(code for row in rows for code in (codes_for(row) or [""]))
    records = [
        {"Tipo": category(code)[0], "Prioridade de triagem": category(code)[1],
         "Ocorrências": count, "Código da API": code or "sem_tipo"}
        for code, count in counts.items()
    ]
    if not records:
        return pd.DataFrame(columns=["Tipo", "Prioridade de triagem", "Ocorrências", "Código da API"])
    return pd.DataFrame(records).sort_values(
        ["Ocorrências", "Tipo"], ascending=[False, True]
    ).reset_index(drop=True)


def numeric(value, decimals=1, unit="") -> str:
    try:
        num = float(value)
        if not isfinite(num):
            return "—"
        return f"{num:.{decimals}f}{(' ' + unit) if unit else ''}"
    except (TypeError, ValueError):
        return "—"


def reading_time(value, tz=LOCAL_TZ) -> str:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return "Horário sem fuso"
        return dt.astimezone(ZoneInfo(tz)).strftime("%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError, OverflowError):
        return "Horário indisponível"


def detail_rows(rows: list[dict], selected_code: str | None = None) -> pd.DataFrame:
    """One table entry per occurrence/type, preserving a multi-label anomaly."""
    records = []
    for row in rows:
        for info in classification_for(row):
            if selected_code is not None and info["code"] != selected_code:
                continue
            records.append({
                "ID": row.get("id", "—"),
                "Horário": reading_time(row.get("created_at")),
                "Dispositivo": row.get("device_id") or "—",
                "Tipo identificado": info["label"],
                "Prioridade de triagem": info["priority"],
                "Tensão": numeric(row.get("voltage"), 1, "V"),
                "Corrente": numeric(row.get("current"), 2, "A"),
                "Potência": numeric(row.get("power"), 1, "W"),
                "Score do modelo": numeric(row.get("anomaly_score"), 3),
                "Avaliação": {"real": "Confirmada pelo usuário", "false": "Falso alarme"}.get(
                    row.get("feedback"), "Não avaliada"
                ),
                "O que foi observado": info["evidence"],
                "O que verificar": info["recommendation"],
                "Código da API": info["code"] or "sem_tipo",
            })
    return pd.DataFrame(records, columns=[
        "ID", "Horário", "Dispositivo", "Tipo identificado", "Prioridade de triagem",
        "Tensão", "Corrente", "Potência", "Score do modelo", "Avaliação",
        "O que foi observado", "O que verificar", "Código da API",
    ])
