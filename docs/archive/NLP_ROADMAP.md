# NLP Integration Roadmap for SOC Assistant

## Phase 1: Alert Text Classification (Week 1-2)

### Objective
Automatically classify alert severity and type from text descriptions.

### Implementation
```python
# backend/ml/nlp/alert_classifier.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class AlertClassifier:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "distilbert-base-uncased",
            num_labels=4  # Critical, High, Medium, Low
        )
    
    def classify(self, alert_text):
        inputs = self.tokenizer(alert_text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        severity = ['low', 'medium', 'high', 'critical'][probs.argmax().item()]
        confidence = probs.max().item()
        return {"severity": severity, "confidence": confidence}
```

### Training Data
- Collect historical alerts with severity labels
- Augment with synthetic examples
- Use transfer learning from security-domain models

### API Endpoint
```python
@app.route('/api/nlp/classify-alert', methods=['POST'])
@require_auth
def classify_alert():
    alert_text = request.json['text']
    result = alert_classifier.classify(alert_text)
    return jsonify(result)
```

---

## Phase 2: Named Entity Recognition (Week 3-4)

### Objective
Extract security-relevant entities from alerts and logs.

### Entities to Extract
- IP addresses
- Domains/URLs
- Ports
- Usernames
- File paths
- CVE IDs
- Attack types

### Implementation
```python
# backend/ml/nlp/entity_extractor.py
from transformers import pipeline

class SecurityNER:
    def __init__(self):
        self.ner = pipeline("ner", model="dslim/bert-base-NER")
        self.security_patterns = {
            'ip': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'port': r'\bport\s+(\d{1,5})\b',
            'cve': r'CVE-\d{4}-\d{4,7}'
        }
    
    def extract_entities(self, text):
        # Transformer-based NER
        entities = self.ner(text)
        
        # Regex-based extraction for security-specific patterns
        import re
        for entity_type, pattern in self.security_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend([{
                'entity': entity_type,
                'value': match,
                'confidence': 1.0
            } for match in matches])
        
        return entities
```

---

## Phase 3: Log Analysis & Correlation (Week 5-6)

### Objective
Analyze system logs and correlate with network alerts.

### Log Sources
- Firewall logs
- IDS/IPS logs
- System logs (auth.log, syslog)
- Application logs
- Web server logs

### Implementation
```python
# backend/ml/nlp/log_analyzer.py
import re
from datetime import datetime

class LogAnalyzer:
    def __init__(self):
        self.patterns = {
            'failed_login': r'Failed password for (\w+) from ([\d.]+)',
            'privilege_escalation': r'sudo.*COMMAND=(.+)',
            'port_scan': r'SYN.*from ([\d.]+).*to port (\d+)'
        }
    
    def parse_log(self, log_line):
        timestamp = self.extract_timestamp(log_line)
        events = []
        
        for event_type, pattern in self.patterns.items():
            match = re.search(pattern, log_line)
            if match:
                events.append({
                    'type': event_type,
                    'timestamp': timestamp,
                    'details': match.groups()
                })
        
        return events
    
    def correlate_with_alerts(self, logs, alerts):
        """Correlate log events with network alerts"""
        correlations = []
        
        for alert in alerts:
            alert_time = alert['timestamp']
            alert_ip = alert.get('src_ip')
            
            # Find related log events within 5-minute window
            related_logs = [
                log for log in logs
                if abs((log['timestamp'] - alert_time).seconds) < 300
                and alert_ip in str(log.get('details', ''))
            ]
            
            if related_logs:
                correlations.append({
                    'alert': alert,
                    'related_logs': related_logs,
                    'correlation_score': len(related_logs)
                })
        
        return correlations
```

---

## Phase 4: Incident Summarization (Week 7-8)

### Objective
Generate human-readable summaries of security incidents.

### Implementation
```python
# backend/ml/nlp/incident_summarizer.py
from transformers import pipeline

class IncidentSummarizer:
    def __init__(self):
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    def summarize_incident(self, alerts, logs, max_length=150):
        # Combine alerts and logs into narrative
        narrative = self.build_narrative(alerts, logs)
        
        # Generate summary
        summary = self.summarizer(
            narrative,
            max_length=max_length,
            min_length=50,
            do_sample=False
        )[0]['summary_text']
        
        # Extract key facts
        key_facts = self.extract_key_facts(alerts, logs)
        
        return {
            'summary': summary,
            'key_facts': key_facts,
            'timeline': self.build_timeline(alerts, logs)
        }
    
    def build_narrative(self, alerts, logs):
        """Convert structured data to natural language"""
        narrative = []
        
        for alert in alerts:
            narrative.append(
                f"At {alert['timestamp']}, {alert['attack_type']} attack "
                f"detected from {alert['src_ip']} targeting {alert['dst_ip']}."
            )
        
        for log in logs:
            narrative.append(
                f"System logs show {log['event_type']} at {log['timestamp']}."
            )
        
        return " ".join(narrative)
```

---

## Phase 5: Threat Intelligence Integration (Week 9-10)

### Objective
Enrich alerts with external threat intelligence.

### Implementation
```python
# backend/utils/threat_intel.py
import requests

class ThreatIntelligence:
    def __init__(self, api_keys):
        self.virustotal_key = api_keys['virustotal']
        self.abuseipdb_key = api_keys['abuseipdb']
    
    def check_ip_reputation(self, ip_address):
        """Check IP against threat databases"""
        results = {}
        
        # AbuseIPDB
        response = requests.get(
            'https://api.abuseipdb.com/api/v2/check',
            headers={'Key': self.abuseipdb_key},
            params={'ipAddress': ip_address}
        )
        results['abuseipdb'] = response.json()
        
        # VirusTotal
        response = requests.get(
            f'https://www.virustotal.com/api/v3/ip_addresses/{ip_address}',
            headers={'x-apikey': self.virustotal_key}
        )
        results['virustotal'] = response.json()
        
        return self.summarize_threat_intel(results)
    
    def summarize_threat_intel(self, results):
        """Generate NLP summary of threat intelligence"""
        summary_parts = []
        
        abuse_score = results['abuseipdb'].get('data', {}).get('abuseConfidenceScore', 0)
        if abuse_score > 50:
            summary_parts.append(
                f"IP has {abuse_score}% abuse confidence score. "
                f"Reported {results['abuseipdb']['data']['totalReports']} times."
            )
        
        vt_malicious = results['virustotal'].get('data', {}).get('attributes', {}).get('last_analysis_stats', {}).get('malicious', 0)
        if vt_malicious > 0:
            summary_parts.append(
                f"Flagged as malicious by {vt_malicious} security vendors."
            )
        
        return " ".join(summary_parts) if summary_parts else "No significant threat intelligence found."
```

---

## Infrastructure Requirements

### 1. Model Storage
```
backend/ml/models/
├── nlp/
│   ├── alert_classifier/
│   │   ├── config.json
│   │   ├── pytorch_model.bin
│   │   └── tokenizer/
│   ├── ner_model/
│   └── summarizer/
```

### 2. API Endpoints
```python
# New NLP endpoints
POST /api/nlp/classify-alert       # Classify alert severity
POST /api/nlp/extract-entities     # Extract security entities
POST /api/nlp/analyze-logs         # Analyze log files
POST /api/nlp/summarize-incident   # Generate incident summary
POST /api/nlp/enrich-threat        # Threat intel enrichment
```

### 3. Frontend Components
```
frontend/src/components/NLPInsights/
├── AlertClassifier.jsx
├── EntityViewer.jsx
├── LogAnalyzer.jsx
├── IncidentSummary.jsx
└── ThreatIntelPanel.jsx
```

### 4. Database Schema
```sql
-- Store NLP analysis results
CREATE TABLE nlp_analysis (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    analysis_type VARCHAR(50),  -- 'classification', 'ner', 'summary'
    result JSONB,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Store extracted entities
CREATE TABLE security_entities (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),  -- 'ip', 'domain', 'cve', etc.
    entity_value TEXT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    occurrences INTEGER DEFAULT 1
);
```

---

## Training Data Requirements

### Alert Classification
- **Minimum:** 1,000 labeled alerts per severity class
- **Sources:** Historical SOC data, public datasets (CICIDS, NSL-KDD)
- **Augmentation:** Paraphrase existing alerts, synthetic generation

### Named Entity Recognition
- **Minimum:** 500 annotated security logs
- **Annotation Tool:** Label Studio, Prodigy
- **Format:** CoNLL-2003 format with security entity tags

### Summarization
- **Minimum:** 200 incident reports with summaries
- **Sources:** Public incident reports, CVE descriptions
- **Fine-tuning:** BART or T5 on security domain

---

## Performance Targets

| Task | Metric | Target |
|------|--------|--------|
| Alert Classification | F1-Score | >85% |
| Entity Extraction | F1-Score | >90% |
| Log Parsing | Accuracy | >95% |
| Summarization | ROUGE-L | >0.40 |
| Threat Intel Enrichment | Coverage | >80% of IPs |

---

## Deployment Strategy

### Phase 1: Offline Analysis
- Run NLP models on historical data
- Build labeled dataset
- Validate accuracy

### Phase 2: Batch Processing
- Process alerts in batches (every 5 minutes)
- Store results in database
- Display in dashboard

### Phase 3: Real-time Analysis
- Stream processing with Kafka
- Sub-second NLP inference
- Live dashboard updates

---

## Cost Estimation

### Compute Resources
- **Training:** 1x GPU instance (T4/V100) - $0.50/hour × 40 hours = $20
- **Inference:** 1x CPU instance (4 cores) - $0.10/hour × 720 hours/month = $72/month

### API Costs
- **VirusTotal:** $500/month (10,000 requests/day)
- **AbuseIPDB:** Free tier (1,000 requests/day)

### Storage
- **Models:** ~2 GB
- **NLP Results:** ~100 MB/day = 3 GB/month

**Total Monthly Cost:** ~$600

---

## Success Metrics

1. **Analyst Efficiency:** Reduce alert triage time by 40%
2. **False Positive Reduction:** Decrease by 25% with better classification
3. **Incident Response Time:** Improve by 30% with automated summaries
4. **Threat Coverage:** Enrich 80%+ of alerts with threat intelligence

---

**Next Steps:**
1. Set up NLP training environment
2. Collect and label training data
3. Fine-tune models on security domain
4. Implement API endpoints
5. Build frontend components
6. Deploy and monitor
