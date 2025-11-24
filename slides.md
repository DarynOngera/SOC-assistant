# Slide 1 – Title

**Title:** Intelligent SOC Assistant: From Network Data to Actionable Alerts

**Subtitle:** An ML-powered SOC dashboard for real-time anomaly detection and analyst support

**Presenter:** [Your Name]
**Context:** [Course / Organization / Date]

---

# Slide 2 – Background

- **Modern SOCs are overwhelmed** by high-volume network and security events.
- **Level 1 analysts** must quickly decide which alerts matter, often with limited context.
- Existing tools are often **fragmented**: separate systems for network monitoring, simulations, and reporting.
- There is a growing need to combine **ML-based anomaly detection**, **attack simulation**, and **governance** in a single workflow.

---

# Slide 3 – Problem Statement

- How can we help SOC analysts:
  - **Reduce alert fatigue** and false positives?
  - **Prioritize truly suspicious activity** across large volumes of traffic?
  - **Experiment safely** with realistic attack traffic without touching production?
  - **Maintain auditability and access control** while doing all this?
- In short:
  - **Problem:** SOCs lack an integrated, intelligent platform that turns raw network data and simulations into **actionable, explainable alerts** for analysts.

---

# Slide 4 – Main Objective

- **Overall Goal**
  - Design and implement an **end-to-end SOC assistant** that supports L1 analysts from data ingestion to alert triage.

- **Specific Objectives**
  - Build a **secure backend** (Flask + JWT + RBAC) to expose SOC APIs and manage users/roles.
  - Integrate **ML models** (LSTM autoencoder + supervised detector) for network anomaly detection.
  - Provide a **simulation layer** using Mininet/PCAP replay to generate realistic attack traffic.
  - Deliver a **dashboard UI** for alerts, network statistics, and admin controls.
  - Ensure **audit logging and export** for compliance and investigations.

---

# Slide 5 – Justification

- **Operational Need**
  - SOC teams face **alert overload** and limited time; better tooling can directly reduce risk and response time.

- **Technical Value**
  - Demonstrates a **full-stack security system**: data pipeline, ML, backend APIs, and frontend dashboard.
  - Shows how to integrate **advanced ML** into a realistic SOC workflow (not just offline notebooks).

- **Research / Learning Value**
  - Hands-on experience with **network datasets, anomaly detection, and model deployment**.
  - Framework for future **NLP/LLM modules** that can explain alerts or support chat-style investigations.

- **Practical Impact**
  - Provides a **safe environment** to replay attacks via PCAPs, tune detection logic, and train analysts.
  - Aligns with how real SOCs operate: RBAC, audit trails, and exportable evidence.

---

# Slide 6 – Demo Overview

- **Demo Goal:** Show how the SOC assistant turns network traffic into prioritized alerts an analyst can act on.

- **Step 1 – Login & Roles**
  - Sign in as an analyst/admin via the JWT-secured login.
  - Briefly show roles and access (e.g., admin vs analyst).

- **Step 2 – Start Simulation (PCAP Replay)**
  - Use the **Mininet/PCAP replay** endpoint from the dashboard.
  - Choose an attack type (e.g., SYN flood, port scan) and start a short simulation.

- **Step 3 – Model-Driven Alerts**
  - Explain that replayed traffic is processed by the **ML models**.
  - Show new alerts appearing with **anomaly scores, severity, and attack type classification**.

- **Step 4 – Analyst Triage Workflow**
  - Filter alerts by severity/attack type.
  - Flag a critical alert, dismiss a benign one.
  - Highlight that these actions are **logged in the audit trail**.

- **Step 5 – Audit & Export**
  - Open the audit/logs view.
  - Export a subset to **CSV/Excel/PDF** to demonstrate reporting and investigation support.

- **Closing Point**
  - Emphasize how all components—ML, simulation, dashboard, RBAC, and audit—work together to support real SOC workflows.
