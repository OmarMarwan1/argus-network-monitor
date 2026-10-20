# ARGUS — Network Monitoring & Failure Prediction Platform

ARGUS is an end-to-end network monitoring platform built around a simulated
enterprise network. It combines a Cisco-designed topology, a PostgreSQL data
pipeline, a FastAPI backend, a live Streamlit dashboard, and two trained ML
models — an Isolation Forest for anomaly detection and a Random Forest for
predicting device failures hours before they happen.

The name comes from Argus Panoptes, the many-eyed giant of Greek myth who
never fully slept — a fitting idea for a system built to watch many devices
at once, continuously.

**Live demo:** `<add your Streamlit Cloud link here>`
**API docs:** `<add your Render /docs link here>`

---

## Architecture

```
Network Devices (Packet Tracer topology)
            |
Python simulators  ───────────────►  PostgreSQL (Neon)
(historical + live telemetry)         devices / metrics / alerts / predictions
            |                                   |
            |                      FastAPI backend (SQLAlchemy + Pydantic)
            |                                   |
            |                      Streamlit dashboard  ◄────────┐
            |                                                    |
            └──────────────────►  ML models (scikit-learn)  ─────┘
                                   Isolation Forest (anomalies)
                                   Random Forest (failure risk)
```

---

## What's built

### 1. Network foundation
A full enterprise-style topology designed in Cisco Packet Tracer:
Internet → ASA firewall (NAT configured) → edge router → redundant core
switches (OSPF, dual-core) → distribution → access layer. Four VLANs (two
user segments, Wi-Fi, servers), DHCP per VLAN, inter-VLAN routing, and
end-to-end connectivity verified through every layer.

### 2. Data pipeline
- PostgreSQL schema: `devices`, `metrics`, `alerts`, `predictions`.
- 13 seeded infrastructure devices (core/distribution/access switches,
  router, firewall, access point, servers) — matched to the real topology.
- A bulk telemetry generator produces 30 days of realistic history per
  device, with per-device-type baselines and bounded, mean-reverting drift
  so values wander naturally without drifting away from normal.
- A live simulator writes new readings continuously for real-time demos.
- Both simulators inject two kinds of labeled events: short anomalies
  (randomized severity and ramp-up) and gradual 12-hour failure buildups,
  so the ML models have genuine signal to learn from.

### 3. Backend API (FastAPI)
Full CRUD on devices, plus device-level metrics, alerts (with optional
severity filtering), and predictions — all backed by SQLAlchemy models and
validated with Pydantic schemas.

| Endpoint | Description |
|---|---|
| `GET /devices` | List all devices |
| `GET /devices/{id}` | Get one device |
| `PATCH /devices/{id}` | Update a device |
| `POST /add_device` | Add a new device |
| `GET /devices/{id}/metrics` | Recent telemetry for one device |
| `GET /alerts` | Alerts, optional `?severity=` filter |
| `GET /predictions` | Current failure risk per device |

### 4. Dashboard (Streamlit)
A live-updating operations dashboard: an overview with network-wide status,
a filterable device table, per-device telemetry charts (with a chart/table
toggle), an alerts view, and a predictions view with risk scores.

### 5. Anomaly detection
Three approaches were trained and compared on a time-based train/test split
(never a random shuffle, since anomalies span consecutive rows):

| Model | Precision | Recall |
|---|---|---|
| Logistic Regression | 0.99 | 0.64 |
| Random Forest | 0.99 | 0.74 |
| **Isolation Forest (deployed)** | 0.63 | 0.52 |

Isolation Forest was chosen for deployment despite the lower score, because
it's unsupervised — it fits a real deployment where nobody has labeled past
failures, unlike the supervised models above. One model is trained **per
device**, since "normal" differs too much by device type to share a single
model (a server at 45% CPU is normal; a switch at 45% is not).

### 6. Failure prediction
A Random Forest trained to flag devices 6 hours before a simulated 12-hour
failure buildup completes, using each device's raw telemetry at a single
point in time:

| Model | Precision | Recall |
|---|---|---|
| Logistic Regression | 0.77 | 0.44 |
| **Random Forest (deployed)** | 0.91 | 0.90 |

---

## Tech stack

| Layer | Tools |
|---|---|
| Network | Cisco Packet Tracer, OSPF, VLANs, DHCP |
| Database | PostgreSQL (hosted on Neon) |
| Backend | FastAPI, SQLAlchemy, Pydantic, psycopg2 |
| Dashboard | Streamlit |
| ML | scikit-learn, pandas, joblib |
| Deployment | Render (API), Streamlit Community Cloud (dashboard), Neon (DB) |

---

## Project structure

```
.
├── main.py                    # FastAPI app and routes
├── database.py                # SQLAlchemy engine/session setup
├── models.py                  # SQLAlchemy table models
├── schemas.py                 # Pydantic request/response schemas
├── dashboard.py                # Streamlit dashboard
├── python_simulator.py        # Bulk historical data generator
├── live_simulator.py          # Real-time data generator
├── anomaly_detection.py       # Scores recent metrics, writes to `alerts`
├── failure_prediction.py      # Scores devices, writes to `predictions`
├── models/                    # Trained, saved model files (.joblib)
├── notebooks/                 # Model training & evaluation notebooks
├── topology.pkt               # Packet Tracer network file
├── requirements.txt
└── .streamlit/config.toml     # Locked dark theme for the dashboard
```

---

## Running it locally

**1. Clone and install:**
```bash
git clone https://github.com/<your-username>/argus-network-monitor.git
cd argus-network-monitor
pip install -r requirements.txt
```

**2. Set up a PostgreSQL database** (local or a free Neon project), then
create a `.env` file in the project root:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
```

**3. Create the schema** — run the `CREATE TABLE` statements for `devices`,
`metrics`, `alerts`, and `predictions` (see `models.py` for the exact
columns), then seed `devices` with your topology's device list.

**4. Generate data and start everything:**
```bash
python python_simulator.py        # 30 days of historical telemetry
python anomaly_detection.py       # trains/evaluates + writes alerts
python failure_prediction.py      # trains/evaluates + writes predictions
python -m uvicorn main:app --reload   # backend, in one terminal
python -m streamlit run dashboard.py  # dashboard, in another terminal
```

Optional, for a real-time demo:
```bash
python live_simulator.py          # writes new readings continuously
```

---

## Known limitations

- **All telemetry is simulated**, not captured from real hardware. Normal
  behavior, anomalies, and failure buildups all follow patterns I designed
  into the generator, so the models are learning those specific patterns —
  not necessarily how a real network fails.
- **Contamination and risk thresholds were calibrated using the injected
  labels.** A real deployment without known failure history would need to
  estimate these rather than know them in advance.
- The deployed dashboard may show a generated historical snapshot rather
  than a continuously live feed, depending on whether the real-time
  simulator is kept running.

---

## Roadmap

- [x] Network topology, VLANs, OSPF, firewall
- [x] Data pipeline with realistic simulated telemetry
- [x] FastAPI backend with full CRUD
- [x] Streamlit dashboard
- [x] Anomaly detection (Isolation Forest)
- [x] Failure prediction (Random Forest)
- [x] Public deployment (Render + Streamlit Cloud + Neon)
- [ ] **AI assistant** — a chatbot that answers questions like *"why is
      Core_SW1 considered high risk?"* using the device's real metrics,
      alerts, and predictions as context
- [ ] Explainability — surfacing *why* a device was flagged, not just that
      it was
- [ ] Full end-to-end demo scenario (inject a failure live, watch it
      detected, predicted, and explained)
- [ ] Dockerize the full stack

---

## License

MIT — see `LICENSE`.
