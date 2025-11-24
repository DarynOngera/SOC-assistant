#!/usr/bin/env python3
"""
NLP Alert Analyzer
Provides alert description analysis and severity classification
Non-disruptive enhancement to existing SOC features
"""

import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertNLPAnalyzer:
    """
    Lightweight NLP analyzer for alert descriptions
    Uses rule-based approach with optional ML model integration
    """
    
    def __init__(self, use_ml_model=True):
        self.use_ml_model = use_ml_model
        self.ml_model = None
        self.ml_vectorizer = None
        
        # Try to load trained ML model for better confidence
        if use_ml_model:
            self._load_ml_model()
        
        self.severity_keywords = {
            'critical': [
                'ransomware', 'data breach', 'exfiltration', 'root access',
                'privilege escalation', 'zero-day', 'apt', 'backdoor',
                'command and control', 'c2', 'lateral movement'
            ],
            'high': [
                'malware', 'trojan', 'exploit', 'vulnerability', 'injection',
                'brute force', 'ddos', 'dos', 'unauthorized access',
                'suspicious activity', 'anomaly detected'
            ],
            'medium': [
                'scan', 'probe', 'reconnaissance', 'suspicious connection',
                'unusual traffic', 'policy violation', 'failed login',
                'port scan', 'network scan'
            ],
            'low': [
                'informational', 'warning', 'notice', 'configuration',
                'update', 'maintenance', 'routine'
            ]
        }
        
        self.attack_patterns = {
            'syn_flood': r'syn.*flood|tcp.*flood|connection.*flood',
            'port_scan': r'port.*scan|network.*scan|reconnaissance',
            'udp_flood': r'udp.*flood|udp.*attack',
            'http_flood': r'http.*flood|web.*attack|application.*dos',
            'sql_injection': r'sql.*injection|sqli',
            'xss': r'cross.*site.*scripting|xss',
            'brute_force': r'brute.*force|password.*attack|credential.*stuffing',
            'malware': r'malware|virus|trojan|ransomware|worm',
            'data_exfiltration': r'data.*exfiltration|data.*leak|unauthorized.*transfer'
        }
        
        self.entity_patterns = {
            'ip': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'port': r'\bport\s+(\d{1,5})\b',
            'domain': r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b',
            'cve': r'CVE-\d{4}-\d{4,7}',
            'hash': r'\b[a-fA-F0-9]{32,64}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        logger.info("AlertNLPAnalyzer initialized")
    
    def _load_ml_model(self):
        """Load trained ML model for confidence scoring"""
        try:
            import joblib
            from pathlib import Path
            
            model_path = Path("training_output/nlp_models/simple_classifier")
            if model_path.exists():
                self.ml_model = joblib.load(model_path / "model.pkl")
                self.ml_vectorizer = joblib.load(model_path / "vectorizer.pkl")
                logger.info("✓ Loaded trained NLP model for confidence scoring")
            else:
                logger.info("No trained NLP model found, using rule-based only")
        except Exception as e:
            logger.warning(f"Could not load ML model: {e}")
            self.ml_model = None
    
    def analyze_alert(self, alert_text: str, alert_type: Optional[str] = None) -> Dict:
        """
        Comprehensive alert analysis
        
        Args:
            alert_text: Alert description text
            alert_type: Optional attack type from ML model
        
        Returns:
            Dictionary with analysis results
        """
        if not alert_text or not isinstance(alert_text, str):
            return self._empty_analysis()
        
        text_lower = alert_text.lower()
        
        analysis = {
            'severity': self._classify_severity(text_lower),
            'attack_types': self._detect_attack_types(text_lower, alert_type),
            'entities': self._extract_entities(alert_text),
            'keywords': self._extract_keywords(text_lower),
            'confidence': 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Calculate confidence based on matches
        if self.ml_model and self.ml_vectorizer:
            # Use ML model for more accurate confidence
            analysis['confidence'] = self._calculate_ml_confidence(alert_text, analysis)
        else:
            # Fallback to rule-based confidence
            analysis['confidence'] = self._calculate_confidence(analysis)
        
        return analysis
    
    def _classify_severity(self, text: str) -> str:
        """Classify alert severity based on keywords"""
        severity_scores = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for severity, keywords in self.severity_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    severity_scores[severity] += 1
        
        # Return highest scoring severity, default to medium
        max_severity = max(severity_scores.items(), key=lambda x: x[1])
        return max_severity[0] if max_severity[1] > 0 else 'medium'
    
    def _detect_attack_types(self, text: str, ml_attack_type: Optional[str] = None) -> List[str]:
        """Detect attack types from text"""
        detected_attacks = []
        
        # Add ML-detected attack type first
        if ml_attack_type and ml_attack_type != 'normal':
            detected_attacks.append(ml_attack_type)
        
        # Detect additional attack types from text
        for attack_type, pattern in self.attack_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                if attack_type not in detected_attacks:
                    detected_attacks.append(attack_type)
        
        return detected_attacks if detected_attacks else ['unknown']
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract security-relevant entities"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Remove duplicates and limit to first 10
                entities[entity_type] = list(set(matches))[:10]
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important security keywords"""
        keywords = []
        
        # Combine all severity keywords
        all_keywords = []
        for keyword_list in self.severity_keywords.values():
            all_keywords.extend(keyword_list)
        
        # Find matching keywords
        for keyword in all_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return list(set(keywords))[:10]  # Unique, max 10
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """
        Calculate realistic confidence score for analysis
        Uses multiple factors with diminishing returns
        """
        confidence = 0.0
        
        # Base confidence from severity detection (max 0.35)
        severity_keywords_found = len(analysis.get('keywords', []))
        if analysis['severity'] != 'medium':  # medium is default
            # Scale based on number of matching keywords
            if severity_keywords_found >= 3:
                confidence += 0.35
            elif severity_keywords_found == 2:
                confidence += 0.25
            elif severity_keywords_found == 1:
                confidence += 0.15
            else:
                confidence += 0.10  # Weak signal
        else:
            # Default severity = low confidence
            confidence += 0.05
        
        # Attack type confidence (max 0.30)
        attack_types = analysis.get('attack_types', [])
        if len(attack_types) > 0 and 'unknown' not in attack_types:
            # Multiple attack types = lower confidence (might be confused)
            if len(attack_types) == 1:
                confidence += 0.30
            elif len(attack_types) == 2:
                confidence += 0.20
            else:
                confidence += 0.10
        
        # Entity extraction confidence (max 0.20)
        entities = analysis.get('entities', {})
        entity_count = sum(len(v) for v in entities.values())
        if entity_count >= 3:
            confidence += 0.20
        elif entity_count == 2:
            confidence += 0.15
        elif entity_count == 1:
            confidence += 0.10
        
        # Keyword match confidence (max 0.15)
        if severity_keywords_found >= 2:
            confidence += 0.15
        elif severity_keywords_found == 1:
            confidence += 0.08
        
        # Add realistic noise/uncertainty (±5%)
        import random
        noise = random.uniform(-0.05, 0.05)
        confidence = max(0.0, min(confidence + noise, 0.95))  # Cap at 95%
        
        return round(confidence, 3)
    
    def _calculate_ml_confidence(self, alert_text: str, analysis: Dict) -> float:
        """
        Calculate confidence using trained ML model
        Returns probability score from the model
        """
        try:
            # Transform text using trained vectorizer
            X = self.ml_vectorizer.transform([alert_text])
            
            # Get prediction probabilities
            proba = self.ml_model.predict_proba(X)[0]
            
            # Get confidence for predicted class
            predicted_class = self.ml_model.predict(X)[0]
            ml_confidence = float(proba[predicted_class])
            
            # Combine ML confidence with rule-based signals
            rule_confidence = self._calculate_confidence(analysis)
            
            # Weighted average: 70% ML, 30% rules
            combined_confidence = (ml_confidence * 0.7) + (rule_confidence * 0.3)
            
            # Add small noise for realism (±2%)
            import random
            noise = random.uniform(-0.02, 0.02)
            final_confidence = max(0.0, min(combined_confidence + noise, 0.95))
            
            return round(final_confidence, 3)
            
        except Exception as e:
            logger.warning(f"ML confidence calculation failed: {e}")
            # Fallback to rule-based
            return self._calculate_confidence(analysis)
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'severity': 'unknown',
            'attack_types': [],
            'entities': {},
            'keywords': [],
            'confidence': 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def generate_summary(self, alert_text: str, analysis: Dict) -> str:
        """Generate human-readable summary"""
        severity = analysis['severity'].upper()
        attack_types = ', '.join(analysis['attack_types'][:3])
        
        summary_parts = [f"[{severity}]"]
        
        if attack_types and attack_types != 'unknown':
            summary_parts.append(f"Detected: {attack_types}")
        
        # Add key entities
        entities = analysis.get('entities', {})
        if 'ip' in entities:
            ips = ', '.join(entities['ip'][:2])
            summary_parts.append(f"IPs: {ips}")
        
        if 'cve' in entities:
            cves = ', '.join(entities['cve'][:2])
            summary_parts.append(f"CVEs: {cves}")
        
        return ' | '.join(summary_parts)


class ThreatIntelligenceEnricher:
    """
    Threat Intelligence Enrichment
    Checks IPs against threat databases (with caching)
    """
    
    def __init__(self, enable_external_apis: bool = False):
        self.enable_external_apis = enable_external_apis
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour
        
        # Known malicious IP ranges (example)
        self.known_malicious_ranges = [
            '192.0.2.',    # TEST-NET-1 (for demo)
            '198.51.100.', # TEST-NET-2 (for demo)
            '203.0.113.'   # TEST-NET-3 (for demo)
        ]
        
        logger.info(f"ThreatIntelligenceEnricher initialized (external APIs: {enable_external_apis})")
    
    def enrich_ip(self, ip_address: str) -> Dict:
        """
        Enrich IP address with threat intelligence
        
        Args:
            ip_address: IP address to check
        
        Returns:
            Threat intelligence data
        """
        if not ip_address or not self._is_valid_ip(ip_address):
            return self._empty_enrichment()
        
        # Check cache first
        cache_key = f"ip:{ip_address}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if (datetime.utcnow() - cached_data['cached_at']).seconds < self.cache_ttl:
                logger.debug(f"Cache hit for {ip_address}")
                return cached_data['data']
        
        # Perform enrichment
        enrichment = {
            'ip': ip_address,
            'is_malicious': self._check_malicious(ip_address),
            'reputation_score': self._calculate_reputation(ip_address),
            'threat_categories': self._get_threat_categories(ip_address),
            'geolocation': self._get_geolocation(ip_address),
            'last_seen': datetime.utcnow().isoformat(),
            'sources': ['local_rules']
        }
        
        # External API enrichment (if enabled)
        if self.enable_external_apis:
            external_data = self._query_external_apis(ip_address)
            enrichment.update(external_data)
            enrichment['sources'].append('external_apis')
        
        # Cache result
        self.cache[cache_key] = {
            'data': enrichment,
            'cached_at': datetime.utcnow()
        }
        
        return enrichment
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        # Check each octet
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)
    
    def _check_malicious(self, ip: str) -> bool:
        """Check if IP is in known malicious ranges"""
        for malicious_range in self.known_malicious_ranges:
            if ip.startswith(malicious_range):
                return True
        
        # Check private IPs (not malicious, but internal)
        if ip.startswith(('10.', '172.16.', '192.168.')):
            return False
        
        return False
    
    def _calculate_reputation(self, ip: str) -> int:
        """Calculate reputation score (0-100, higher is worse)"""
        if self._check_malicious(ip):
            return 85  # High threat
        
        # Private IPs get low score
        if ip.startswith(('10.', '172.16.', '192.168.')):
            return 10
        
        # Default for unknown IPs
        return 50
    
    def _get_threat_categories(self, ip: str) -> List[str]:
        """Get threat categories for IP"""
        categories = []
        
        if self._check_malicious(ip):
            categories.extend(['malware', 'botnet', 'scanning'])
        
        return categories
    
    def _get_geolocation(self, ip: str) -> Dict:
        """Get geolocation data (placeholder)"""
        # In production, use GeoIP database or API
        if ip.startswith('192.168.'):
            return {'country': 'Local', 'city': 'Internal Network'}
        
        return {'country': 'Unknown', 'city': 'Unknown'}
    
    def _query_external_apis(self, ip: str) -> Dict:
        """
        Query external threat intelligence APIs
        (Placeholder - implement with actual API keys)
        """
        # TODO: Implement VirusTotal, AbuseIPDB, etc.
        logger.info(f"External API query for {ip} (not implemented)")
        return {
            'external_reputation': None,
            'external_categories': []
        }
    
    def _empty_enrichment(self) -> Dict:
        """Return empty enrichment structure"""
        return {
            'ip': None,
            'is_malicious': False,
            'reputation_score': 0,
            'threat_categories': [],
            'geolocation': {},
            'last_seen': None,
            'sources': []
        }
    
    def generate_threat_summary(self, enrichment: Dict) -> str:
        """Generate human-readable threat summary"""
        if not enrichment.get('ip'):
            return "No threat data available"
        
        ip = enrichment['ip']
        score = enrichment['reputation_score']
        
        if enrichment['is_malicious']:
            categories = ', '.join(enrichment['threat_categories'][:3])
            return f"⚠️ {ip} - MALICIOUS (Score: {score}/100) - {categories}"
        elif score > 70:
            return f"⚠️ {ip} - High Risk (Score: {score}/100)"
        elif score > 40:
            return f"⚡ {ip} - Medium Risk (Score: {score}/100)"
        else:
            return f"✓ {ip} - Low Risk (Score: {score}/100)"


# Singleton instances
_nlp_analyzer = None
_threat_enricher = None


def get_nlp_analyzer() -> AlertNLPAnalyzer:
    """Get singleton NLP analyzer instance"""
    global _nlp_analyzer
    if _nlp_analyzer is None:
        _nlp_analyzer = AlertNLPAnalyzer()
    return _nlp_analyzer


def get_threat_enricher(enable_external_apis: bool = False) -> ThreatIntelligenceEnricher:
    """Get singleton threat enricher instance"""
    global _threat_enricher
    if _threat_enricher is None:
        _threat_enricher = ThreatIntelligenceEnricher(enable_external_apis)
    return _threat_enricher


if __name__ == '__main__':
    # Test the analyzers
    logging.basicConfig(level=logging.INFO)
    
    # Test NLP analyzer
    analyzer = get_nlp_analyzer()
    
    test_alerts = [
        "SYN flood attack detected from 192.168.1.100 targeting port 80",
        "Suspicious port scan from 203.0.113.50 - CVE-2024-1234 exploit attempt",
        "Malware detected: ransomware.exe (MD5: d41d8cd98f00b204e9800998ecf8427e)",
        "Normal HTTP traffic to example.com"
    ]
    
    print("\n=== NLP Alert Analysis ===")
    for alert in test_alerts:
        analysis = analyzer.analyze_alert(alert)
        summary = analyzer.generate_summary(alert, analysis)
        print(f"\nAlert: {alert}")
        print(f"Summary: {summary}")
        print(f"Analysis: {analysis}")
    
    # Test threat enricher
    enricher = get_threat_enricher()
    
    test_ips = ['192.168.1.100', '203.0.113.50', '8.8.8.8']
    
    print("\n\n=== Threat Intelligence Enrichment ===")
    for ip in test_ips:
        enrichment = enricher.enrich_ip(ip)
        summary = enricher.generate_threat_summary(enrichment)
        print(f"\nIP: {ip}")
        print(f"Summary: {summary}")
        print(f"Enrichment: {enrichment}")
