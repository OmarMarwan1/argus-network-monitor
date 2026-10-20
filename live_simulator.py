"""
Live Telemetry Simulator
-------------------------
Writes one new reading per device every few seconds, so the dashboard has
"real-time" data to show. It reuses the exact same logic as your bulk
generator (python_simulator.py), so live data behaves like the history:
healthy values near baseline, with occasional anomalies and, more rarely,
a gradual failure buildup.

Keep this file in the same folder as python_simulator.py.
Run it with:   python live_simulator.py      (Ctrl+C to stop)
"""

import time
from datetime import datetime

import psycopg2

from python_simulator import (
    db_config, fetch_devices, init_state, step,
    apply_anomalies, apply_failures, insert_batch,
)

interval_seconds = 4   # one new reading per device every N seconds


def main():
    conn = psycopg2.connect(**db_config)
    print("connected to DataBase")

    devices = fetch_devices(conn)
    if not devices:
        print("no items found in `devices` table please fill the info needed")
        return

    state, base_state = init_state(devices)
    active_events = {}      # devices currently inside a short anomaly
    active_failures = {}    # devices currently inside a gradual failure buildup

    print(f"Live simulation started for {len(devices)} devices "
          f"(every {interval_seconds}s). Press Ctrl+C to stop.")

    try:
        while True:
            step(state, base_state)

            # same rule as the bulk generator: a device being failure-tested
            # is skipped for short anomalies, so the two kinds of events
            # don't overlap and confuse the labels
            anomaly_output = apply_anomalies(state, active_events)
            failure_output = apply_failures(state, base_state, active_failures)
            now = datetime.now()

            rows = []
            anomalous = 0
            failing = 0
            for device_id in state:
                if device_id in active_failures or failure_output[device_id][1]:
                    values, failure_soon = failure_output[device_id]
                    is_anomaly = False
                else:
                    values, is_anomaly = anomaly_output[device_id]
                    failure_soon = False

                rows.append((
                    device_id, now,
                    values["cpu"], values["memory"], values["temperature"],
                    values["latency"], values["packet_loss"], values["traffic"],
                    int(values["interface_errors"]), is_anomaly, failure_soon,
                ))
                if is_anomaly:
                    anomalous += 1
                if failure_soon:
                    failing += 1

            insert_batch(conn, rows)

            print(f"[{now:%H:%M:%S}] inserted {len(rows)} rows "
                  f"({anomalous} anomalous, {failing} failure-warning)")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\nstopped by user")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
