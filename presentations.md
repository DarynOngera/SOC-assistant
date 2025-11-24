# SOC Assistant – 15-Minute Panel Presentation

## 0. Framing (0:00 – 1:00)
- **Who I am**: [Your name], builder of an intelligent SOC analysis assistant.
- **What this is**: A full-stack, ML-powered SOC dashboard that helps Level 1 analysts detect and triage threats faster and more accurately.
- **One-line value**: Turn noisy security logs into prioritized, explainable alerts in real time.

---

## 1. Problem Statement (1:00 – 3:00)
- **SOC reality today**
  - Huge volume of network and security events.
  - High false-positive rates and alert fatigue.
  - Junior/L1 analysts struggle to know **what to look at first**.
- **Specific pain points**
  - Manual correlation between different data sources (network flows, IDS alerts, logs).
  - Lack of consistent anomaly detection and threat classification.
  - Difficult to replay/experiment with attack traffic in a safe environment.
- **Goal**
  - Build a system that **reduces noise**, **highlights true anomalies**, and **guides analysts** with an integrated, explainable dashboard.

> **Problem statement**: “How can we give SOC analysts a single, intelligent view that combines network anomaly detection, attack simulation, and auditability—without adding more tools and complexity?”

---

## 2. Proposed Solution Overview (3:00 – 5:00)
- **SOC Assistant**: an end-to-end platform that includes:
  - **Backend**: Flask-based SOC dashboard server with secure JWT authentication and RBAC.
  - **ML Engine**: LSTM autoencoder and supervised models for network anomaly detection.
  - **Simulation Layer**: Mininet + PCAP replay to generate realistic attack traffic.
  - **Frontend**: React-based dashboard (alerts, statistics, network map, admin tools).
  - **Audit & Export**: Structured audit logs with export to CSV/Excel/PDF.
- **High-level data flow**
  - Network/PCAP data → feature extraction → ML models → anomaly scores → alerts → dashboard + audit logs.
- **Key design goals**
  - Modular, testable, and ready for future NLP/LLM-based analysis.
  - Clear separation of concerns: data pipeline, ML, API, UI, and admin/rbac.

---

## 3. Architecture & Components (5:00 – 8:00)

### 3.1 System Architecture
- **Core modules**
  - **Data & ML** (`train.py`, `trainer.py`, model artifacts): feature engineering, LSTM autoencoder, supervised SOC detector.
  - **Dashboard Server** (`src/dashboard/server.py`): REST + WebSocket, authentication, alert APIs, Mininet integration, audit export.
  - **Simulation**: PCAP replay mode to quickly generate realistic alerts without live Mininet.
  - **RBAC & Admin**: role-based access, admin endpoints, audit logging.

### 3.2 Model Pipeline
- **Unsupervised anomaly detection**
  - LSTM autoencoder trained on normal network traffic.
  - Reconstruction error → anomaly score; optimized thresholds.
- **Supervised detector** (from `trainer.py`)
  - Handles categorical encoding, scaling, feature selection, SMOTE, threshold optimization.
  - Provides `predict_single`, `predict_batch`, and a `get_feature_template` used by the dashboard.

### 3.3 Backend Server
- **Key responsibilities**
  - User authentication (JWT), role-based authorization.
  - Endpoints for alerts, statistics, data refresh, and Mininet simulation control.
  - Integrates trained models to:
    - Score incoming or replayed traffic.
    - Classify attack type.
    - Stream alerts via WebSocket to the UI.

---

## 4. Key Features & Walkthrough (8:00 – 12:00)

### 4.1 Authentication & RBAC
- **Roles**: Super Admin, SOC Manager, Senior Analyst, Analyst, Viewer.
- **Capabilities**
  - Admin-only endpoints to create/manage users and roles.
  - Session management with token refresh.
  - Secure password policies and audit logging of admin actions.
- **Why it matters**: Mirrors real SOC team structures and enforces least privilege.

### 4.2 Mininet / PCAP Simulation
- **PCAP replay mode**
  - Instead of running heavy Mininet scenarios live, the system replays pre-captured PCAPs.
  - Quickly generates alerts (5–15 seconds) without root access.
- **Endpoints**
  - Start/stop simulation, check status, list attack types.
- **Impact**
  - Safe way to demo or test detection logic using realistic traffic patterns.

### 4.3 Alerting & Dashboard
- **Alerts API**
  - Real-time anomaly scores from ML models.
  - Attack type classification and severity.
  - Filtering, pagination, and triage actions (flag, dismiss).
- **Dashboard views**
  - **Alerts list** with severity, source/destination, timestamp, and status.
  - **Network statistics**: counts of events, anomaly rates, attack distribution.
  - **Network map** and threat trends over time.
- **User workflow**
  1. Analyst logs in.
  2. Starts a simulation or waits for live data.
  3. Reviews new alerts, filters by severity or attack type.
  4. Flags critical alerts; dismisses false positives; all actions are audited.

### 4.4 Audit & Export
- **Audit logs**
  - Records key security events: logins, role changes, alert actions, exports.
- **Export capability**
  - JSON, CSV, Excel, PDF.
  - Filter by time range, event type, username, severity.
- **Value**
  - Supports compliance, investigations, and offline analysis.

---

## 5. Engineering Practices & Testing (12:00 – 13:30)
- **Code quality**
  - Modular design: separate modules for models, server, RBAC, exporters, simulations.
  - Configuration via environment where appropriate (e.g., secrets, paths).
- **Testing**
  - Integration tests for the full pipeline: data → model → server endpoints → UI behavior.
  - Specific tests for:
    - Feature mismatch handling and threshold optimization.
    - Model integration into the dashboard.
    - Audit export formats and filters.
- **Logging & observability**
  - Structured logging with clear log levels and reduced noise.
  - Helpful error messages for feature mismatches and prediction failures.

---

## 6. Impact, Limitations & Future Work (13:30 – 15:00)

### 6.1 Impact
- **For SOC analysts**
  - Prioritized, explainable alerts instead of raw events.
  - Faster triage, less alert fatigue.
- **For organizations**
  - Easier to experiment with detection logic via PCAP replay.
  - Stronger governance with audit trails and RBAC.

### 6.2 Current Limitations
- Primarily focused on network traffic; limited log/NLP analysis so far.
- Requires curated PCAPs or network feeds for best results.
- UI and UX can be further polished for large-scale deployments.

### 6.3 Future Directions
- **NLP/LLM module** for:
  - Natural-language explanations for alerts.
  - Chat-style investigations (“Show me suspicious activity from this host in the last hour”).
- **More datasets**: add CERT/LANL logs and unify them into the same dashboard.
- **Advanced correlation**: cross-correlate alerts, user behavior, and host telemetry.

---

## 7. Closing (Optional 20–30s buffer)
- **Recap**
  - Built an end-to-end SOC assistant: from data and models, to simulation, to a secure dashboard.
  - Designed for real SOC constraints: high volume, limited time, need for explainability and governance.
- **Final line**
  - “This project shows how we can move from isolated tools to an integrated, intelligent SOC assistant that actually supports analysts in real time.”
