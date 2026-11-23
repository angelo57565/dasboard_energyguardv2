import pandas as pd

from anomaly_insights import (
    CATALOG, category, classification_for, codes_for, detail_rows, overview_by_type,
    numeric, reading_time,
)


def sample(**overrides):
    row = {
        "id": 12, "device_id": "esp32-a", "created_at": "2026-11-23T18:00:00Z",
        "voltage": 225.5, "current": 8.1, "power": 1700.0,
        "anomaly_score": -0.11, "feedback": None,
        "anomaly_types": ["sobretensao", "consumo_elevado"],
        "reasons": [],
    }
    row.update(overrides)
    return row


def test_classifications_do_not_infer_crime_or_theft():
    label, priority, evidence, advice = category("consumo_elevado")
    assert "consumo" in label.lower()
    assert "não demonstra desvio" in advice
    assert priority == "Atenção"
    assert "furto" not in label.lower()


def test_all_backend_types_are_supported():
    assert len(CATALOG) == 10
    for code in CATALOG:
        assert len(classification_for(sample(anomaly_types=[code]))) == 1


def test_multiple_types_are_preserved_and_counted():
    rows = [sample(), sample(id=13, anomaly_types=["sobretensao"])]
    result = overview_by_type(rows)
    assert result["Ocorrências"].sum() == 3
    assert int(result.loc[result["Código da API"] == "sobretensao", "Ocorrências"].iloc[0]) == 2
    assert len(detail_rows(rows)) == 3


def test_no_type_is_explicitly_unclassified():
    row = sample(anomaly_types=None)
    assert codes_for(row) == []
    assert classification_for(row)[0]["label"] == "Anomalia sem classificação técnica"
    assert detail_rows([row])["Código da API"].iloc[0] == "sem_tipo"


def test_unknown_code_kept_not_misclassified():
    row = sample(anomaly_types=["novo_codigo"])
    results = detail_rows([row])
    assert results["Código da API"].iloc[0] == "novo_codigo"
    assert results["Tipo identificado"].iloc[0] == "Anomalia sem classificação técnica"


def test_duplicate_code_counted_once_per_event():
    row = sample(anomaly_types=["queda", "queda"])
    assert codes_for(row) == ["queda"]
    assert len(detail_rows([row])) == 1


def test_none_nan_and_bad_time_are_safe():
    row = sample(voltage=None, current=float("nan"), power="broken", created_at="bad-date")
    result = detail_rows([row])
    assert result["Tensão"].iloc[0] == "—"
    assert result["Corrente"].iloc[0] == "—"
    assert result["Potência"].iloc[0] == "—"
    assert result["Horário"].iloc[0] == "Horário indisponível"
    assert numeric("n/a") == "—"
    assert reading_time("2026-11-23T18:00:00") == "Horário sem fuso"


def test_filter_includes_only_matching_type():
    rows = [sample(), sample(id=15, anomaly_types=["queda"])]
    out = detail_rows(rows, "queda")
    assert len(out) == 1
    assert out["ID"].iloc[0] == 15


def test_empty_records_has_stable_columns():
    assert overview_by_type([]).empty
    assert detail_rows([]).empty
    assert isinstance(detail_rows([]), pd.DataFrame)
