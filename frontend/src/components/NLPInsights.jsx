import React, { useState, useEffect } from 'react';
import { Shield, Brain, AlertTriangle, CheckCircle, XCircle, Loader } from 'lucide-react';

const NLPInsights = ({ alert }) => {
  const [nlpAnalysis, setNlpAnalysis] = useState(null);
  const [threatIntel, setThreatIntel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [nlpAvailable, setNlpAvailable] = useState(true);

  useEffect(() => {
    checkNLPStatus();
  }, []);

  useEffect(() => {
    if (alert && nlpAvailable) {
      analyzeAlert();
    }
  }, [alert, nlpAvailable]);

  const checkNLPStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/nlp/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setNlpAvailable(data.nlp_available);
    } catch (err) {
      console.error('Error checking NLP status:', err);
      setNlpAvailable(false);
    }
  };

  const analyzeAlert = async () => {
    if (!alert?.description && !alert?.text) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      
      // Analyze alert text
      const alertText = alert.description || alert.text || '';
      const attackType = alert.attack_type || alert.type;

      const nlpResponse = await fetch('http://localhost:5000/api/nlp/analyze-alert', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: alertText,
          attack_type: attackType
        })
      });

      if (nlpResponse.ok) {
        const nlpData = await nlpResponse.json();
        setNlpAnalysis(nlpData);
      }

      // Enrich IP if available
      if (alert.src_ip) {
        const ipResponse = await fetch('http://localhost:5000/api/nlp/enrich-ip', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            ip: alert.src_ip
          })
        });

        if (ipResponse.ok) {
          const ipData = await ipResponse.json();
          setThreatIntel(ipData);
        }
      }
    } catch (err) {
      console.error('Error analyzing alert:', err);
      setError('Failed to analyze alert');
    } finally {
      setLoading(false);
    }
  };

  if (!nlpAvailable) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-center gap-2 text-gray-500">
          <Brain className="w-5 h-5" />
          <span className="text-sm">NLP analysis not available</span>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <div className="flex items-center justify-center gap-2 text-gray-500">
          <Loader className="w-5 h-5 animate-spin" />
          <span>Analyzing alert...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 rounded-lg p-4 border border-red-200">
        <div className="flex items-center gap-2 text-red-600">
          <XCircle className="w-5 h-5" />
          <span className="text-sm">{error}</span>
        </div>
      </div>
    );
  }

  if (!nlpAnalysis && !threatIntel) {
    return null;
  }

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-green-100 text-green-800 border-green-300',
      unknown: 'bg-gray-100 text-gray-800 border-gray-300'
    };
    return colors[severity] || colors.unknown;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getThreatColor = (score) => {
    if (score >= 70) return 'text-red-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-4">
      {/* NLP Analysis */}
      {nlpAnalysis?.success && (
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Brain className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">NLP Analysis</h3>
          </div>

          {/* Summary */}
          {nlpAnalysis.summary && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-900 font-medium">{nlpAnalysis.summary}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Severity */}
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">
                Detected Severity
              </label>
              <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border ${getSeverityColor(nlpAnalysis.analysis?.severity)}`}>
                <AlertTriangle className="w-4 h-4" />
                <span className="font-semibold uppercase text-sm">
                  {nlpAnalysis.analysis?.severity || 'Unknown'}
                </span>
              </div>
            </div>

            {/* Confidence */}
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">
                Confidence Score
              </label>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getConfidenceColor(nlpAnalysis.analysis?.confidence)}`}
                    style={{ 
                      width: `${(nlpAnalysis.analysis?.confidence || 0) * 100}%`,
                      backgroundColor: nlpAnalysis.analysis?.confidence >= 0.8 ? '#10b981' : 
                                     nlpAnalysis.analysis?.confidence >= 0.6 ? '#f59e0b' : '#ef4444'
                    }}
                  />
                </div>
                <span className={`text-sm font-semibold ${getConfidenceColor(nlpAnalysis.analysis?.confidence)}`}>
                  {((nlpAnalysis.analysis?.confidence || 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Attack Types */}
            {nlpAnalysis.analysis?.attack_types?.length > 0 && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-600 mb-2 block">
                  Detected Attack Types
                </label>
                <div className="flex flex-wrap gap-2">
                  {nlpAnalysis.analysis.attack_types.map((type, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium border border-purple-300"
                    >
                      {type.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Entities */}
            {nlpAnalysis.analysis?.entities && Object.keys(nlpAnalysis.analysis.entities).length > 0 && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-600 mb-2 block">
                  Extracted Entities
                </label>
                <div className="space-y-2">
                  {Object.entries(nlpAnalysis.analysis.entities).map(([type, values]) => (
                    <div key={type} className="flex items-start gap-2">
                      <span className="text-xs font-semibold text-gray-500 uppercase min-w-[80px]">
                        {type}:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {values.map((value, idx) => (
                          <code
                            key={idx}
                            className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-mono border border-gray-300"
                          >
                            {value}
                          </code>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Keywords */}
            {nlpAnalysis.analysis?.keywords?.length > 0 && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-600 mb-2 block">
                  Security Keywords
                </label>
                <div className="flex flex-wrap gap-2">
                  {nlpAnalysis.analysis.keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs border border-gray-300"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Threat Intelligence */}
      {threatIntel?.success && (
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">Threat Intelligence</h3>
          </div>

          {/* Summary */}
          {threatIntel.summary && (
            <div className="mb-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
              <p className="text-sm text-purple-900 font-medium">{threatIntel.summary}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* IP Address */}
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">
                IP Address
              </label>
              <code className="block px-3 py-2 bg-gray-100 text-gray-800 rounded font-mono text-sm border border-gray-300">
                {threatIntel.enrichment?.ip}
              </code>
            </div>

            {/* Reputation Score */}
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">
                Reputation Score
              </label>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full"
                    style={{ 
                      width: `${threatIntel.enrichment?.reputation_score || 0}%`,
                      backgroundColor: threatIntel.enrichment?.reputation_score >= 70 ? '#ef4444' : 
                                     threatIntel.enrichment?.reputation_score >= 40 ? '#f59e0b' : '#10b981'
                    }}
                  />
                </div>
                <span className={`text-sm font-semibold ${getThreatColor(threatIntel.enrichment?.reputation_score)}`}>
                  {threatIntel.enrichment?.reputation_score || 0}/100
                </span>
              </div>
            </div>

            {/* Malicious Status */}
            <div>
              <label className="text-sm font-medium text-gray-600 mb-2 block">
                Status
              </label>
              <div className="flex items-center gap-2">
                {threatIntel.enrichment?.is_malicious ? (
                  <>
                    <XCircle className="w-5 h-5 text-red-600" />
                    <span className="text-red-600 font-semibold">Malicious</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-green-600 font-semibold">Clean</span>
                  </>
                )}
              </div>
            </div>

            {/* Threat Categories */}
            {threatIntel.enrichment?.threat_categories?.length > 0 && (
              <div>
                <label className="text-sm font-medium text-gray-600 mb-2 block">
                  Threat Categories
                </label>
                <div className="flex flex-wrap gap-2">
                  {threatIntel.enrichment.threat_categories.map((category, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium border border-red-300"
                    >
                      {category}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Geolocation */}
            {threatIntel.enrichment?.geolocation && (
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-600 mb-2 block">
                  Geolocation
                </label>
                <p className="text-sm text-gray-700">
                  {threatIntel.enrichment.geolocation.city}, {threatIntel.enrichment.geolocation.country}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NLPInsights;
