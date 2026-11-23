"""Read-only classification must work without backend anomaly alerts or trained model."""
from datetime import datetime, timedelta, timezone

from reading_diagnostics import infer_reading_types


def readings(count=15, voltage=127.0, current=1.0, power=120.0, frequency=60.0):
    base = datetime(2026, 11, 23, tzinfo=timezone.utc)
    return [
        {"id": i, "created_at": (base + timedelta(seconds=i * 5)).isoformat(),
         "device_id": "esp32", "voltage": voltage, "current": current,
         "power": power, "frequency": frequency, "power_factor": 0.95,
         "is_anomaly": False}
        for i in range(count)
    ]


def test_no_alert_and_no_model_flags_still_identifies_high_voltage():
    rows = readings(voltage=145)
    result = infer_reading_types(rows, nominal_voltage=127)
    assert result and all("sobretensao" in r["anomaly_types"] for r in result)
    assert all(r["is_anomaly"] is False for r in result)
    assert all(r["diagnostic_origin"] == "Indício calculado das medições" for r in result)


def test_normal_readings_produce_no_false_alert():
    assert infer_reading_types(readings()) == []


def test_voltage_drop_needs_preceding_healthy_voltage():
    rows = readings(count=3)
    rows[2].update(voltage=0, power=0, current=0)
    result = infer_reading_types(rows)
    assert any("queda" in r["anomaly_types"] for r in result)
    assert "queda" not in infer_reading_types(readings(count=1, voltage=0))[0]["anomaly_types"] if infer_reading_types(readings(count=1, voltage=0)) else True


def test_consumption_spike_requires_history_and_does_not_claim_theft():
    rows = readings()
    rows[-1].update(power=600, current=6)
    result = infer_reading_types(rows)
    assert "consumo_elevado" in result[0]["anomaly_types"]
    assert "furto" not in result[0]["diagnostic_evidence"].lower()


def test_current_spike_requires_history():
    rows = readings()
    rows[-1].update(current=4.0, power=450)
    result = infer_reading_types(rows)
    assert "sobrecorrente" in result[0]["anomaly_types"]


def test_bad_measurements_cannot_crash_analysis():
    rows = readings(count=2)
    rows[0]["voltage"] = None
    rows[1]["created_at"] = "bad-time"
    assert infer_reading_types(rows) == []


def test_uses_nominal_voltage_range():
    assert infer_reading_types(readings(voltage=225), nominal_voltage=220) == []
    assert infer_reading_types(readings(voltage=225), nominal_voltage=127)


def test_output_bounded_by_max_results():
    assert len(infer_reading_types(readings(count=200, voltage=150), max_results=10)) == 10
