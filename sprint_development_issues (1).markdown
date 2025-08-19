# SOC Analysis Assistant Development Issues

This document outlines the development-focused GitHub issues for building the intelligent Security Operations Center (SOC) analysis assistant, structured into 5 sprints (1.5 weeks each, ~7.5 weeks total). The project prioritizes a web-based UI with JWT-based user authentication from Sprint 1, continuously integrating modules (data pipeline, LSTM Autoencoder, NLP, UI) using real datasets (CIC-IDS 2017/2018, CERT Insider Threat, LANL) and real CTI feeds (e.g., public CVE databases, IP threat lists). Issues are modular, actionable (1-4 hours each), and trackable via a GitHub Projects Kanban board (columns: To Do, In Progress, Review, Done). The tech stack includes Python, PyTorch, Hugging Face Transformers, Pandas/NumPy/Scikit-learn, Flask/PyJWT, and React with Tailwind CSS.

## Sprint 1: Initial UI with Auth & Data Pipeline Foundation (Weeks 1-1.5)
**Sprint Goal**: Develop a basic React-based UI with JWT authentication and set up the initial data ingestion pipeline using real datasets.

### Issue #1: Initialize Project Repository
- **Description**: Set up a GitHub repo with /data, /models, /nlp, /ui, /auth folders, requirements.txt (Python, Pandas, NumPy, Flask, PyJWT), and a basic script structure (data/clean.py, ui/index.html, auth/login.py).
- **Assignee**: Self
- **Labels**: setup, code
- **Acceptance Criteria**: Repo created; requirements.txt installs without errors; clean.py runs a hello-world print; /ui and /auth folders initialized.

### Issue #2: Implement Basic React UI with Login
- **Description**: In ui/index.html and ui/src/App.jsx, create a React app (CDN-hosted React, Tailwind CSS) with a login page (username/password) and a dashboard to display 5 sample alerts from CERT dataset (via JSON from clean.py).
- **Assignee**: Self
- **Labels**: ui, auth, code
- **Acceptance Criteria**: UI renders login page; dashboard shows 5 CERT alerts post-login; dismiss/flag buttons log to console; styled with Tailwind.

### Issue #3: Implement Auth Backend
- **Description**: In auth/login.py, create a Flask API to validate username/password against a JSON user store; issue JWT on successful login.
- **Assignee**: Self
- **Labels**: auth, code
- **Acceptance Criteria**: API validates credentials; returns JWT for valid user; rejects invalid login; notebook tests 3 login attempts.

### Issue #4: Implement Dataset Downloader
- **Description**: Write data/download.py to fetch CIC-IDS 2017/2018, CERT Insider Threat, and LANL datasets; save to /data/raw.
- **Assignee**: Self
- **Labels**: data, code
- **Acceptance Criteria**: Script downloads datasets (<5GB total); files saved as CSVs; logs download status.

**Increment**: React UI with login and CERT alert dashboard; JWT auth backend; data download script; initial dataset.

---

## Sprint 2: Data Preprocessing & UI Integration (Weeks 1.5-3)
**Sprint Goal**: Complete data preprocessing and integrate real processed data into the UI with authentication.

### Issue #5: Develop Data Cleaning Script
- **Description**: In data/clean.py, use Pandas to handle missing values (impute/remove), remove duplicates, and fix inconsistencies for CERT dataset.
- **Assignee**: Self
- **Labels**: data, code
- **Acceptance Criteria**: Script processes CERT CSV; outputs cleaned CSV; Jupyter notebook shows sample before/after.

### Issue #6: Feature Engineering for Sequences
- **Description**: Extend clean.py to encode categorical fields (one-hot for action types, hosts) and normalize numerical fields (e.g., byte counts); generate user-based sequence vectors (1-hour windows).
- **Assignee**: Self
- **Labels**: data, code
- **Acceptance Criteria**: Script outputs pickled sequence vectors; tested on 100 samples; notebook validates output shape.

### Issue #7: Create Data API for UI
- **Description**: In ui/server.py, create a Flask API to serve processed CERT data as JSON (from clean.py); require JWT for access.
- **Assignee**: Self
- **Labels**: ui, auth, integration, code
- **Acceptance Criteria**: API serves 10 CERT alerts; UI fetches and displays them dynamically post-auth; no errors on refresh.

### Issue #8: Enhance UI with Sorting
- **Description**: Update ui/src/App.jsx to add sorting for alerts by timestamp; style with Tailwind; verify JWT on API calls.
- **Assignee**: Self
- **Labels**: ui, auth, code
- **Acceptance Criteria**: UI sorts alerts on click; displays sorted list correctly; validates JWT; notebook tests with 10 alerts.

**Increment**: Fully processed CERT dataset; UI dynamically displays alerts via API with auth; data pipeline complete.

---

## Sprint 3: LSTM Anomaly Detection & UI Integration (Weeks 3-4.5)
**Sprint Goal**: Implement and train the LSTM Autoencoder; integrate anomaly scores into the UI with authentication.

### Issue #9: Configure PyTorch Environment
- **Description**: Update requirements.txt with PyTorch; create notebook to test tensor operations and GPU availability.
- **Assignee**: Self
- **Labels**: setup, code
- **Acceptance Criteria**: Environment installs; notebook runs matrix multiplication; GPU detected if available.

### Issue #10: Code LSTM Autoencoder Model
- **Description**: In models/lstm_autoencoder.py, define LSTM-based encoder-decoder with configurable layers for sequential data.
- **Assignee**: Self
- **Labels**: model, code
- **Acceptance Criteria**: Model class compiles; forward pass tested with dummy sequence (shape: [batch, timesteps, features]).

### Issue #11: Train LSTM Autoencoder
- **Description**: Write train_lstm.py to load benign sequences from Sprint 2, train model (10 epochs, 80% benign CERT data), and save checkpoint to /models.
- **Assignee**: Self
- **Labels**: model, training
- **Acceptance Criteria**: Training completes; loss decreases; checkpoint saved; notebook plots reconstruction error.

### Issue #12: Integrate Anomaly Scores into UI
- **Description**: In predict.py, compute reconstruction error for test sequences; apply threshold (mean + 2*std) to flag anomalies; update ui/server.py to serve scores as JSON; update ui/src/App.jsx to display prioritized alerts with scores.
- **Assignee**: Self
- **Labels**: model, ui, integration, code
- **Acceptance Criteria**: Script outputs anomaly scores for 100 sequences; UI displays 5 prioritized alerts with scores post-auth; styled consistently.

**Increment**: Functional LSTM Autoencoder; trained model checkpoint; UI displays real anomaly scores with auth.

---

## Sprint 4: NLP Module & UI Enhancement (Weeks 4.5-6)
**Sprint Goal**: Develop the NLP pipeline with real CTI integration; enhance UI with contextual summaries.

### Issue #13: Set Up Hugging Face Transformers
- **Description**: Add Transformers to requirements.txt; create notebook to load/test a pre-trained model (e.g., CyberBERT or BERT-base).
- **Assignee**: Self
- **Labels**: setup, nlp, code
- **Acceptance Criteria**: Model loads; notebook runs sample inference (e.g., token classification) on CERT logs without errors.

### Issue #14: Implement NER Pipeline
- **Description**: In nlp/ner.py, fine-tune CyberBERT on CERT logs and public threat reports for NER (IPs, CVEs, malware).
- **Assignee**: Self
- **Labels**: nlp, code
- **Acceptance Criteria**: Fine-tuning completes; NER achieves >85% F1-score on 50 test samples; outputs entities to JSON.

### Issue #15: Develop Narrative Generation
- **Description**: In nlp/summarize.py, create template-based NLG to generate plain-text summaries from NER outputs (e.g., "IP 192.168.1.10 accessed sensitive file").
- **Assignee**: Self
- **Labels**: nlp, code
- **Acceptance Criteria**: Script generates readable summaries for 10 CERT alerts; outputs saved as JSON for UI.

### Issue #16: Integrate NLP Summaries with CTI into UI
- **Description**: In nlp/cti.py, correlate NER outputs with real CTI feeds (e.g., public CVE database, IP threat lists); update ui/server.py to serve summaries; update ui/src/App.jsx to display narratives; ensure JWT auth.
- **Assignee**: Self
- **Labels**: nlp, ui, auth, integration, code
- **Acceptance Criteria**: UI displays 5 alerts with CTI-enriched narratives (<50 words) post-auth; styled with Tailwind.

**Increment**: Fine-tuned NLP model; UI displays alerts with CTI-enriched summaries; standalone NER and NLG scripts.

---

## Sprint 5: Final Integration, Testing, & Artifacts (Weeks 6-7.5)
**Sprint Goal**: Finalize pipeline integration, optimize models, enhance UI with user-specific feedback, and save deployable artifacts.

### Issue #17: Build Main Pipeline Script
- **Description**: Write main.py to chain data ingestion (clean.py), anomaly detection (predict.py), and NLP summarization (ner.py, summarize.py, cti.py); output JSON for UI.
- **Assignee**: Self
- **Labels**: integration, code
- **Acceptance Criteria**: Script runs end-to-end on 100 CERT samples; outputs anomaly scores + narratives as JSON to /output.

### Issue #18: Implement Evaluation Metrics
- **Description**: In eval.py, compute Precision, Recall, F1, AUC-ROC, FNR on test set (20% CERT data, mixed benign/malicious).
- **Assignee**: Self
- **Labels**: testing, code
- **Acceptance Criteria**: Script outputs metrics to eval_metrics.csv; F1 >0.8; FNR <10%; notebook visualizes ROC curve.

### Issue #19: Add UI Feedback with User IDs
- **Description**: Update ui/src/App.jsx and ui/server.py to log dismiss/flag actions with user IDs (from JWT) to /logs/feedback.json for future retraining.
- **Assignee**: Self
- **Labels**: ui, auth, integration, code
- **Acceptance Criteria**: UI buttons send actions with user IDs to API; 10 sample actions logged in JSON; file readable and formatted.

### Issue #20: Save Model Artifacts
- **Description**: Save final LSTM and NLP models to /models with load scripts (load_models.py); document usage in models/README.md.
- **Assignee**: Self
- **Labels**: model, code
- **Acceptance Criteria**: Models loadable; script runs inference on sample CERT data; README clear.

**Increment**: Fully integrated prototype; optimized LSTM and NLP models; UI with user-specific feedback; final evaluation metrics.

---

## Notes
- **Issue Size**: Each issue is scoped to 1-4 hours for feasibility within 1.5-week sprints.
- **Continuous Integration**: Modules (data, models, nlp, ui, auth) use real CERT data from Sprint 1, with CIC-IDS and LANL added in Sprint 5 testing; real CTI feeds for NLP.
- **Dependencies**: Sprints are sequential (UI/auth/data > LSTM > NLP > integration); LSTM/NLP modules independent for potential parallel work.
- **GitHub Usage**: Issues linked to Kanban board; commits reference issue numbers (e.g., “Closes #3”); PRs for review.
- **Testing Focus**: Metrics (F1, FNR) align with research objectives (Section 1.3); notebooks validate modules.
- **UI/Auth Details**: React UI (CDN-hosted React/Tailwind) requires JWT auth via login page before alert dashboard (sortable table, dismiss/flag buttons, narratives); optimized for L1 analysts.
- **Modularity**: Scripts (clean.py, predict.py, ner.py, cti.py) are standalone; main.py integrates backend; UI in /ui and auth in /auth are separate.