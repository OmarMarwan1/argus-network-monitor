import psycopg2
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()
db_config = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD2"),
    "sslmode": "require",
}

bounds = {"cpu": (5, 95), "memory": (10, 95), "temperature": (25, 85),
          "latency": (0, 200), "packet_loss": (0, 15), "traffic": (0, 100), "interface_errors": (0, 50),
          }

drift = {"cpu": 3, "memory": 2, "temperature": 1, "latency": 0.5,
         "packet_loss": 0.1, "traffic": 5, "interface_errors": 1}

baselines = {
    "multilayer_switch": {"cpu": 35, "memory": 45, "temperature": 40, "latency": 2, "packet_loss": 0.1, "traffic": 50, "interface_errors": 0},
    "switch":             {"cpu": 25, "memory": 35, "temperature": 38, "latency": 1, "packet_loss": 0.1, "traffic": 30, "interface_errors": 0},
    "router":             {"cpu": 30, "memory": 40, "temperature": 42, "latency": 3, "packet_loss": 0.2, "traffic": 60, "interface_errors": 0},
    "fire_wall":          {"cpu": 40, "memory": 50, "temperature": 45, "latency": 2, "packet_loss": 0.1, "traffic": 70, "interface_errors": 0},
    "access_point":       {"cpu": 20, "memory": 30, "temperature": 35, "latency": 4, "packet_loss": 0.5, "traffic": 40, "interface_errors": 0},
    "server":             {"cpu": 45, "memory": 55, "temperature": 40, "latency": 1, "packet_loss": 0.1, "traffic": 80, "interface_errors": 0},
}

pull_strength = 0.1

# --- NEW: anomaly settings ---------------------------------------------------
# Each anomaly type says "add this much to these metrics" while the event lasts.
anomaly_types = {
    "cpu_spike":         {"cpu": 40, "latency": 10},
    "packet_loss_burst": {"packet_loss": 6, "latency": 30, "interface_errors": 10},
    "latency_jump":      {"latency": 60},
    "error_burst":       {"interface_errors": 20, "packet_loss": 2},
}
anomaly_chance = 0.003
anomaly_min_ticks = 3
anomaly_max_ticks = 8

days = 30
reading_interval_mins = 5
batch_size = 5000


def clamp(value, key):
    lo, hi = bounds[key]
    return max(lo, min(hi, value))


def fetch_devices(conn):
    with conn.cursor() as cur:
        cur.execute("select device_id, name, device_type FROM devices;")
        return cur.fetchall()


def init_state(devices):
    state = {}
    base_state = {}
    for device_id, name, device_type in devices:
        base = baselines.get(device_type, baselines["switch"])
        state[device_id] = dict(base)
        base_state[device_id] = dict(base)
    return state, base_state


def step(state, base_state):
    for device_id, metrics in state.items():
        for key in drift:
            pull = (base_state[device_id][key] - metrics[key]) * pull_strength
            change = random.uniform(-drift[key], drift[key])
            metrics[key] = clamp(metrics[key] + change + pull, key)


def apply_anomalies(state, active_events):
    """
    Decides what values to WRITE this tick. Normal devices are written as-is.
    Devices in an anomaly get boosted values and a True label.
    The underlying `state` is never changed, so the device returns to
    normal on its own when the anomaly ends.
    """
    output = {}
    for device_id, metrics in state.items():
        values = dict(metrics)     # copy, so the real state stays clean
        is_anomaly = False

        # maybe start a new anomaly on this device
        if device_id not in active_events and random.random() < anomaly_chance:
            active_events[device_id] = {
                "kind": random.choice(list(anomaly_types)),
                "ticks_left": random.randint(anomaly_min_ticks, anomaly_max_ticks),
            }

        # if an anomaly is running, push the affected metrics up
        if device_id in active_events:
            event = active_events[device_id]
            for key, boost in anomaly_types[event["kind"]].items():
                values[key] = clamp(values[key] + boost, key)
            is_anomaly = True
            event["ticks_left"] -= 1
            if event["ticks_left"] == 0:
                del active_events[device_id]

        output[device_id] = (values, is_anomaly)
    return output


failure_chance = 0.00025
buildup_hours = 12
label_hours = 6
repair_ticks = 3


def apply_failures(state, base_state, active_failures):
    output = {}
    for device_id, metrics in state.items():
        values = dict(metrics)
        label = False

        if device_id not in active_failures and random.random() < failure_chance:
            buildup_ticks = buildup_hours * (60 // reading_interval_mins)
            active_failures[device_id] = {
                "stage": "buildup",
                "ticks_left": buildup_ticks,
                "total_ticks": buildup_ticks,
                "repair_left": repair_ticks,
                # some failures build up more severely than others
                "severity": random.uniform(0.4, 1.0),
            }

        if device_id in active_failures:
            event = active_failures[device_id]

            if event["stage"] == "buildup":
                progress = (1 - event["ticks_left"] /
                            event["total_ticks"]) * event["severity"]
                values["temperature"] = clamp(
                    values["temperature"] + 15 * progress ** 1.5, "temperature")
                values["interface_errors"] = clamp(
                    values["interface_errors"] + 25 * progress ** 1.5, "interface_errors")
                values["latency"] = clamp(
                    values["latency"] + 40 * progress ** 2, "latency")
                values["packet_loss"] = clamp(
                    values["packet_loss"] + 8 * progress ** 2, "packet_loss")
                values["cpu"] = clamp(
                    values["cpu"] + 20 * progress ** 1.5, "cpu")

                label_ticks = label_hours * (60 // reading_interval_mins)
                label = event["ticks_left"] <= label_ticks

                event["ticks_left"] -= 1
                if event["ticks_left"] == 0:
                    event["stage"] = "down"

            elif event["stage"] == "down":
                values["latency"] = bounds["latency"][1]
                values["packet_loss"] = bounds["packet_loss"][1]
                event["stage"] = "repairing"

            elif event["stage"] == "repairing":
                event["repair_left"] -= 1
                if event["repair_left"] == 0:
                    values = dict(base_state[device_id])
                    del active_failures[device_id]

        output[device_id] = (values, label)
    return output


def insert_batch(conn, rows):
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO metrics (device_id, timestamp, cpu, memory, temperature, latency, packet_loss, traffic, interface_errors, is_anomaly, failure_soon)
            VALUES %s;
            """,
            rows,
        )
    conn.commit()


def main():
    conn = psycopg2.connect(**db_config)
    print("connected to DataBase")

    devices = fetch_devices(conn)
    if not devices:
        print("no items found in `devices` table please fill the info needed")
        return

    state, base_state = init_state(devices)
    active_events = {}      # devices currently in a short anomaly
    active_failures = {}    # devices currently in a gradual failure buildup

    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    current_time = start_time
    step_size = timedelta(minutes=reading_interval_mins)

    rows_buffer = []
    total_rows = 0
    anomaly_rows = 0
    failure_rows = 0

    print(f"Generating history from {start_time} to {end_time} "
          f"(every {reading_interval_mins} min)...")

    while current_time <= end_time:
        step(state, base_state)

        # a device being actively failure-tested is skipped for short anomalies,
        # so the two kinds of events don't overlap and confuse the labels
        anomaly_output = apply_anomalies(state, active_events)
        failure_output = apply_failures(state, base_state, active_failures)

        for device_id in state:
            if device_id in active_failures or failure_output[device_id][1]:
                values, failure_soon = failure_output[device_id]
                is_anomaly = False
            else:
                values, is_anomaly = anomaly_output[device_id]
                failure_soon = False

            rows_buffer.append((
                device_id, current_time,
                values["cpu"], values["memory"], values["temperature"],
                values["latency"], values["packet_loss"], values["traffic"],
                int(values["interface_errors"]), is_anomaly, failure_soon,
            ))
            if is_anomaly:
                anomaly_rows += 1
            if failure_soon:
                failure_rows += 1

        if len(rows_buffer) >= batch_size:
            insert_batch(conn, rows_buffer)
            total_rows += len(rows_buffer)
            rows_buffer = []
        current_time += step_size

    if rows_buffer:
        insert_batch(conn, rows_buffer)
        total_rows += len(rows_buffer)

    print(
        f"Done. Inserted {total_rows} rows: {anomaly_rows} anomalies, {failure_rows} failure-warning rows.")
    conn.close()


if __name__ == "__main__":
    main()
