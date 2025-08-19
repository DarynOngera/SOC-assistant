# SOC Analysis Assistant Project Structure

This document defines the project structure for the intelligent Security Operations Center (SOC) analysis assistant, supporting a modular, continuously integrated development process across 5 sprints (1.5 weeks each, ~7.5 weeks total). The structure organizes code, data, models, NLP, UI, and authentication components to facilitate development, testing, and integration of the data pipeline, LSTM Autoencoder, NLP module, and web-based UI with JWT-based user authentication for L1 SOC analysts. Real datasets (CIC-IDS 2017/2018, CERT Insider Threat, LANL) and real CTI feeds (e.g., public CVE databases, IP threat lists) are used from Sprint 1, ensuring continuous integration without mock data. The project is managed via GitHub with a Kanban board for issue tracking.

## Project Root Directory
```
soc-analysis-assistant/
├── auth/                    # Authentication scripts for JWT-based UI access
├── data/                    # Data ingestion and preprocessing scripts and datasets
├── models/                  # Machine learning models and training scripts
├── nlp/                     # NLP processing scripts (NER, narrative generation, CTI integration)
├── ui/                      # Web-based UI (React, Tailwind CSS) and API
├── notebooks/               # Jupyter notebooks for experimentation and validation
├── logs/                    # Output logs (e.g., user feedback, evaluation metrics)
├── output/                  # Processed outputs (e.g., JSON alerts, summaries)
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies (PyTorch, Pandas, Flask, PyJWT, etc.)
├── README.md                # Project overview, setup instructions
└── .gitignore               # Git ignore file for temporary files, datasets, etc.
```

## Directory Details

### auth/
Contains scripts for user authentication to secure UI access for SOC analysts.
- `login.py`: Flask API for username/password validation and JWT issuance using a JSON user store.
- `users.json`: JSON file storing user credentials (username, hashed password) for authentication.
- `README.md`: Documentation for auth setup, API endpoints, and JWT usage.

### data/
Houses scripts for acquiring and preprocessing real datasets (CIC-IDS, CERT, LANL) and storing processed data.
- `download.py`: Script to fetch CIC-IDS 2017/2018, CERT Insider Threat, and LANL datasets to /data/raw.
- `clean.py`: Script for data cleaning (handle missing values, duplicates) and feature engineering (sequence generation with one-hot encoding, normalization).
- `raw/`: Subdirectory for raw datasets (CSVs, e.g., CIC-IDS traffic, CERT logs).
- `processed/`: Subdirectory for cleaned and processed data (CSVs, pickled sequence vectors).
- `data_sources.md`: Documentation of dataset sources, formats, and preprocessing steps.

### models/
Stores LSTM Autoencoder model definitions, training scripts, and saved artifacts.
- `lstm_autoencoder.py`: LSTM Autoencoder model definition for anomaly detection on sequential data.
- `train_lstm.py`: Script to train the LSTM Autoencoder on benign sequences from processed datasets.
- `predict.py`: Script to compute reconstruction errors and flag anomalies, outputting JSON for UI.
- `load_models.py`: Script to load saved models for inference.
- `checkpoints/`: Subdirectory for saved model checkpoints (e.g., .pth files).
- `README.md`: Documentation for model setup, training, and inference.

### nlp/
Contains scripts for Named Entity Recognition (NER), narrative generation, and real CTI integration.
- `ner.py`: Script to fine-tune CyberBERT on cybersecurity text (e.g., CERT logs, public threat reports) for NER (IPs, CVEs, malware).
- `summarize.py`: Script for template-based NLG to create plain-text alert summaries.
- `cti.py`: Script to correlate NER outputs with real CTI feeds (e.g., public CVE databases, IP threat lists via API or local data).
- `README.md`: Documentation for NLP setup, fine-tuning, and CTI integration.

### ui/
Holds the React-based web UI with Tailwind CSS and Flask API for dynamic alert display and user interaction.
- `index.html`: Entry point for the React app (CDN-hosted React, Tailwind CSS).
- `src/`: Subdirectory for React components and JavaScript.
  - `App.jsx`: Main React component for login page and alert dashboard (sortable table, dismiss/flag buttons).
  - `components/`: Reusable components (e.g., LoginForm.jsx, AlertTable.jsx).
- `server.py`: Flask API to serve alerts (anomaly scores, narratives) from data/models/nlp, with JWT validation.
- `README.md`: Documentation for UI setup, API endpoints, and running the app.

### notebooks/
Contains Jupyter notebooks for data exploration, model validation, and UI testing with real data.
- `data_exploration.ipynb`: Notebook for inspecting raw and processed datasets (e.g., CERT sequences).
- `lstm_training.ipynb`: Notebook for training and visualizing LSTM Autoencoder results.
- `nlp_validation.ipynb`: Notebook for testing NER and narrative generation with real CTI.
- `ui_testing.ipynb`: Notebook for testing UI data fetching, display, and auth flows.
- `evaluation.ipynb`: Notebook for computing and visualizing metrics (Precision, Recall, F1, AUC-ROC, FNR).

### logs/
Stores runtime logs and user feedback from authenticated UI interactions.
- `feedback.json`: JSON file logging user actions (e.g., dismiss/flag alerts with user IDs from JWT).
- `eval_metrics.csv`: CSV file storing evaluation metrics from testing (e.g., F1, FNR).

### output/
Holds processed outputs for UI consumption and debugging.
- `alerts.json`: JSON file with anomaly scores and NLP-generated narratives for UI display.
- `summaries/`: Subdirectory for text summaries (optional, for debugging NLP outputs).

### tests/
Contains unit and integration tests for scripts, models, and API endpoints.
- `test_data.py`: Tests for data cleaning and feature engineering.
- `test_lstm.py`: Tests for LSTM Autoencoder model and predictions.
- `test_nlp.py`: Tests for NER, narrative generation, and CTI integration.
- `test_ui.py`: Tests for UI API endpoints, JWT auth, and alert display.
- `README.md`: Documentation for running tests.

## File Details
- `requirements.txt`: Lists Python dependencies (e.g., `torch`, `pandas`, `numpy`, `flask`, `pyjwt`, `transformers`).
- `README.md`: Project overview, setup instructions (backend, UI, auth), and run commands.
- `.gitignore`: Ignores temporary files (e.g., `__pycache__`), large datasets, and model checkpoints.

## Notes
- **Continuous Integration**: Modules (data, models, nlp, ui, auth) are integrated with real data (CIC-IDS, CERT, LANL) from Sprint 1; real CTI feeds (e.g., public CVE databases) are used for NLP.
- **Modularity**: Each directory is standalone, enabling parallel development and debugging; main.py integrates modules.
- **UI/Auth**: React UI (CDN-hosted React/Tailwind) requires JWT auth via a login page before accessing the alert dashboard (sortable table, dismiss/flag buttons); optimized for L1 analysts.
- **Data Management**: Raw datasets in /data/raw are not committed; processed data in /data/processed is committed if small (<100MB).
- **Version Control**: Git/GitHub tracks changes; commits reference issue numbers (e.g., “Closes #3”); PRs for review.
- **Scalability**: Structure supports adding features (e.g., advanced UI filters, additional models) in future iterations.