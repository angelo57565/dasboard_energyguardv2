import pandas as pd
import pytest
import requests

from contracts import validate_response
from helpers import age_seconds, reporting_coverage, short_summary, month_projection, validation_dataframe
from telemetry import incremental_readings, plot_sample


def test_fifteen_minutes():
    times = pd.date_range("2026-01-01", periods=16, freq="min", tz="UTC")
    df = pd.DataFrame({"created_at": times, "power": [1000] * 16, "is_anomaly": [False] * 16})
    assert short_summary(df)["energy_kwh"] == pytest.approx(0.25)


def test_coverage():
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    df = pd.DataFrame({"created_at": [start, start, start + pd.Timedelta(seconds=10)]})
    assert reporting_coverage(df, start, start + pd.Timedelta(seconds=30), 10) == pytest.approx(200 / 3)


def test_timestamps():
    assert age_seconds("invalid") == float("inf")
    assert age_seconds("2999-01-01T00:00:00Z") == float("inf")


def test_zero_reference():
    df = validation_dataframe([{"created_at": "2026-01-01T00:00:00Z", "measured": 1, "reference": 0}])
    assert pd.isna(df["erro_pct"].iloc[0])


def test_projection_needs_start_of_month():
    now = pd.Timestamp("2026-01-20T12:00:00", tz="America/Sao_Paulo")
    hourly = pd.DataFrame({"period": [now - pd.Timedelta(hours=1)], "kwh": [1.]})
    assert pd.isna(month_projection(hourly, now)[1])


def test_contracts():
    with pytest.raises(requests.RequestException):
        validate_response("/api/devices", {})
    with pytest.raises(requests.RequestException):
        validate_response("/api/readings/latest", {"voltage": 100})


def test_sampling():
    df = pd.DataFrame({"power": [10] * 1000, "is_anomaly": [False] * 1000})
    df.loc[100, "is_anomaly"] = True
    df.loc[400, "power"] = 900
    sample = plot_sample(df, 100)
    assert 100 in sample.index and 400 in sample.index


def test_incremental_dedup():
    class FakeApi:
        def get(self, path, **params):
            return [{"id": 2, "created_at": "2026-01-01T00:01:00+00:00"}]
    old = [{"id": 1, "created_at": "2026-01-01T00:00:00+00:00"},
           {"id": 2, "created_at": "2026-01-01T00:01:00+00:00"}]
    assert len(incremental_readings(FakeApi(), "test", "2026-01-01T00:00:00+00:00", old)) == 2
