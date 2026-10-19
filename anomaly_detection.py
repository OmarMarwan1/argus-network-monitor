import time
from datetime import timedelta
import joblib
import pandas as pd
from sqlalchemy import text

from database import engine

model_file = "IsolationForest_models.joblib"

lookback_hours = 24
pad_hours = 2
loop_seconds = 0


def get_severity(z):
    if z >= 6:
        return "high"
    if z >= 4:
        return "medium"
    return "low"


def find_anomalies(data, models, features, since):
    alerts = []
    for device_id, g in data.groupby("device_id"):
        if device_id not in models:
            continue
        g = g.sort_values("timestamp")
        flagged = pd.Series(models[device_id].predict(
            g[features]) == -1, index=g.index)
        starts = flagged & ~flagged.shift(1, fill_value=False)
        mean = g[features].mean()
        std = g[features].std().replace(0, 1)
        for idx in g.index[starts.values]:
            row = g.loc[idx]
            if row["timestamp"] < since:
                continue
            z = (row[features] - mean) / std
            metric = z.abs().idxmax()
            direction = "above" if z[metric] > 0 else "below"

            alerts.append({
                "device_id": int(device_id),
                "timestamp": row["timestamp"],
                "alert_type": "anomaly",
                "metric": metric,
                "severity": get_severity(abs(z[metric])),
                "description": (f"{metric} is {row[metric]:.1f}, "
                                f"{abs(z[metric]):.1f} standard deviations {direction} "
                                f"this device's normal ({mean[metric]:.1f})"),
            })

    return pd.DataFrame(alerts)


def run_once(saved):
    latest = pd.read_sql("SELECT MAX(timestamp) AS latest FROM metrics",
                         engine, parse_dates=["latest"])["latest"].iloc[0]
    if pd.isna(latest):
        print("metrics table is empty, nothing to check")
        return

    since = latest - timedelta(hours=lookback_hours)
    start = since - timedelta(hours=pad_hours)

    data = pd.read_sql(
        text("SELECT * FROM metrics WHERE timestamp >= :start ORDER BY device_id, timestamp"),
        engine, params={"start": start.to_pydatetime()}, parse_dates=["timestamp"],
    )

    alerts = find_anomalies(data, saved["models"], saved["features"], since)

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM alerts WHERE alert_type = 'anomaly' AND timestamp >= :since"),
            {"since": since.to_pydatetime()},
        )
        if not alerts.empty:
            alerts.to_sql("alerts", conn, if_exists="append", index=False)

    print(f"checked {len(data)} readings, wrote {len(alerts)} alerts "
          f"(window: {since:%Y-%m-%d %H:%M} to {latest:%Y-%m-%d %H:%M})")


def main():
    saved = joblib.load(model_file)
    print(f"loaded {len(saved['models'])} models")

    while True:
        run_once(saved)
        if loop_seconds == 0:
            break
        time.sleep(loop_seconds)


if __name__ == "__main__":
    main()
