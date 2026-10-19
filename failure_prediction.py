import time
from datetime import timedelta
import joblib
import pandas as pd
from sqlalchemy import text

from database import engine

model_file = "models/failure_prediction_model.joblib"

history_hours = 6
loop_secs = 0


def get_risk_level(probability):
    if probability >= 0.70:
        return "high"
    if probability >= 0.35:
        return "medium"
    return "low"


def build_explanation(latest_row, recent, features):
    mean = recent[features].mean()
    std = recent[features].std().replace(0, 1)
    z = (latest_row[features] - mean) / std
    metric = z.abs().idxmax()
    direction = "above" if z[metric] > 0 else "below"
    return (f"{metric} is {latest_row[metric]:.1f}, {abs(z[metric]):.1f} standard "
            f"deviations {direction} this device's recent normal ({mean[metric]:.1f})")


def run_once(saved):
    model, features = saved["model"], saved["features"]
    latest_time = pd.read_sql("select MAX(timestamp) AS latest FROM metrics",
                              engine, parse_dates=["latest"])["latest"].iloc[0]
    if pd.isna(latest_time):
        print("metrics table is empty please fill some data")
        return
    since = latest_time - timedelta(hours=history_hours)
    data = pd.read_sql(text("SELECT * FROM metrics WHERE timestamp>= :since ORDER BY device_id , timestamp"),
                       engine, params={"since": since.to_pydatetime()}, parse_dates=["timestamp"])
    rows = []
    for device_id, recent in data.groupby("device_id"):
        latest_row = recent.sort_values("timestamp").iloc[-1]

        probability = model.predict_proba(latest_row[features].to_frame().T)[0]
        probability = probability[list(model.classes_).index(True)]

        rows.append({
            "device_id": int(device_id),
            "timestamp": latest_row["timestamp"],
            "failure_risk": round(probability*100, 1),
            "risk_level": get_risk_level(probability),
            "explanation": build_explanation(latest_row, recent, features)
        })
    predictions = pd.DataFrame(rows)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM predictions"))
        if not predictions.empty:
            predictions.to_sql("predictions", conn,
                               if_exists="append", index=False)

    high = int((predictions["risk_level"] == "high").sum()
               ) if not predictions.empty else 0
    print(f"scored {len(predictions)} devices, {high} at high risk "
          f"(as of {latest_time:%Y-%m-%d %H:%M})")


def main():
    saved = joblib.load(model_file)
    print(
        f"loaded failure prediction model (trained on {len(saved['features'])} features)")

    while True:
        run_once(saved)
        if loop_secs == 0:
            break
        time.sleep(loop_secs)


if __name__ == "__main__":
    main()
