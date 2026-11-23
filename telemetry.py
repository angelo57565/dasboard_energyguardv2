"""Incremental reading access and bounded chart sampling."""
import pandas as pd


def incremental_readings(api, device, since, old=None, limit=20000):
    old = old or []
    query_since = max([since] + [r["created_at"] for r in old if r.get("created_at")])
    fresh = api.get("/api/readings", device_id=device, since=query_since, limit=limit)
    merged = {r["id"]: r for r in old if r.get("id") is not None and r.get("created_at", "") >= since}
    for row in fresh:
        if row.get("id") is not None and row.get("created_at", "") >= since:
            merged[row["id"]] = row
    return sorted(merged.values(), key=lambda r: r["created_at"])[-limit:]


def plot_sample(df: pd.DataFrame, maximum=1800):
    """Preserve spikes, flagged anomalies and endpoints."""
    if len(df) <= maximum:
        return df
    stride = max(1, len(df) // max(1, maximum // 3))
    keep = {0, len(df) - 1}
    p = pd.to_numeric(df["power"], errors="coerce")
    for start in range(0, len(df), stride):
        block = p.iloc[start:start + stride]
        if block.notna().any():
            keep.add(int(block.idxmin()))
            keep.add(int(block.idxmax()))
    if "is_anomaly" in df:
        keep.update(map(int, df.index[df["is_anomaly"].fillna(False)]))
    return df.iloc[sorted(keep)]
