from datetime import datetime, timedelta, timezone

from event_analysis import (
    device_diagnostics, event_table, extract_events, quality_report,
    sample_codes, usual_consumption,
)


def samples(n=30, voltage=127, current=1, power=120, step=5):
    start = datetime(2026, 11, 23, tzinfo=timezone.utc)
    return [
        {"id": i, "created_at": (start + timedelta(seconds=i * step)).isoformat(),
         "voltage": voltage, "current": current, "power": power,
         "frequency": 60, "power_factor": .95, "device_id": "test"}
        for i in range(n)
    ]


def test_voltage_outage_episode_has_bounded_observed_duration():
    data = samples()
    for index in (10, 11, 12):
        data[index].update(voltage=0, power=0, current=0)
    result = [e for e in extract_events(data) if e["Código"] == "queda"]
    assert len(result) == 1
    assert result[0]["Duração observada (s)"] == 10
    assert result[0]["Amostras"] == 3


def test_telemetry_gap_does_not_imply_voltage_outage():
    data = samples(n=3)
    data[2]["created_at"] = (
        datetime(2026, 11, 23, tzinfo=timezone.utc) + timedelta(minutes=8)
    ).isoformat()
    events = extract_events(data, interval_s=5)
    assert any(e["Código"] == "comunicacao" for e in events)
    assert not any(e["Código"] == "queda" for e in events)
    assert next(e for e in events if e["Código"] == "comunicacao")["Duração observada (s)"] is None


def test_single_sample_spike_not_assumed_to_have_duration():
    data = samples()
    data[20].update(voltage=145, power=120, current=1)
    peaks = [e for e in extract_events(data) if e["Código"] == "sobretensao"]
    assert len(peaks) == 1
    assert peaks[0]["Duração observada (s)"] == 0
    assert peaks[0]["Tensão máxima (V)"] == 145


def test_current_spike_uses_historical_baseline():
    data = samples()
    data[20].update(current=4, power=430)
    assert any(e["Código"] == "sobrecorrente" for e in extract_events(data))


def test_quality_stats_and_event_counts():
    data = samples()
    report = quality_report(data, extract_events(data))
    assert report["samples"] == 30
    assert report["voltage"]["mínimo"] == 127
    assert report["frequency"]["média"] == 60


def test_device_status_and_gap_count():
    data = samples(n=3)
    data[2]["created_at"] = (datetime(2026, 11, 23, tzinfo=timezone.utc) +
                             timedelta(seconds=100)).isoformat()
    result = device_diagnostics(data, interval_s=5,
                                now=datetime(2026, 11, 23, tzinfo=timezone.utc) +
                                timedelta(seconds=105))
    assert result["state"] == "Recebendo leituras"
    assert result["gap_count"] == 1


def test_consumer_comparison_does_not_claim_energy_billing():
    data = samples(n=30)
    for row in data[15:]:
        row["power"] = 240
    result = usual_consumption(data)
    assert result["available"] and result["change_pct"] == 100
    assert "não é comparação sazonal" in result["note"]


def test_incomplete_history_disables_comparison():
    assert not usual_consumption(samples(n=10))["available"]


def test_missing_or_invalid_data_safe():
    data = samples(n=3)
    data[0]["created_at"] = "not a date"
    data[1]["voltage"] = None
    assert isinstance(extract_events(data), list)
    assert event_table([]).empty
    assert device_diagnostics([])["state"] == "Sem dados"


def test_physical_bounds_produce_indicators_not_fraud():
    assert "sobretensao" in sample_codes({"voltage": 150, "current": 1, "power": 120}, 127)
    assert "furto" not in repr(extract_events(samples())).lower()
