"""Basic validation of known FastAPI response envelopes."""
import math
import requests

LISTS = {"/api/devices", "/api/readings", "/api/anomalies", "/api/alerts/rules",
         "/api/alerts/events", "/api/validations", "/api/consumption/hourly"}
OBJECTS = {"/api/readings/latest", "/api/summary", "/api/settings",
           "/api/model/status", "/api/model/evaluation", "/api/quality", "/api/alerts/channels"}
REQUIRED = {"/api/readings/latest": ("created_at", "voltage", "current", "power", "is_anomaly"),
            "/api/summary": ("energy_kwh", "power_avg", "power_max", "anomalies"),
            "/api/model/status": ("ready",)}


def validate_response(path, data):
    if path in LISTS and (not isinstance(data, list) or any(not isinstance(r, dict) for r in data)):
        raise requests.RequestException(f"Resposta inválida em {path}: lista esperada")
    if path in OBJECTS and not isinstance(data, dict):
        raise requests.RequestException(f"Resposta inválida em {path}: objeto esperado")
    missing = [key for key in REQUIRED.get(path, ()) if data.get(key) is None]
    if missing:
        raise requests.RequestException(f"Campos ausentes em {path}: {', '.join(missing)}")
    if path == "/api/readings/latest":
        for key in ("voltage", "current", "power"):
            try:
                valid = math.isfinite(float(data[key]))
            except (ValueError, TypeError):
                valid = False
            if not valid:
                raise requests.RequestException(f"Leitura inválida: {key}")
    return data
