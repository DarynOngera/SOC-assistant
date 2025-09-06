import React, { useState, useEffect } from 'react';
import { AlertTriangle, Shield, Clock, Target, TrendingUp, Eye, Flag, X, CheckCircle } from 'lucide-react';

const ThreatTriage = () => {
  const [triageData, setTriageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPriority, setSelectedPriority] = useState('high');

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchTriageData = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/threat-triage', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setTriageData(data);
        setError(null);
      } else {
        throw new Error('Failed to fetch threat triage data');
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching threat triage:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAlertAction = async (alertId, action) => {
    try {
      const response = await fetch(`http://localhost:5000/api/alerts/${alertId}/${action}`, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        // Refresh triage data after action
        fetchTriageData();
      }
    } catch (err) {
      console.error(`Error ${action}ing alert:`, err);
    }
  };

  useEffect(() => {
    fetchTriageData();
    const interval = setInterval(fetchTriageData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'text-red-700 bg-red-100 border-red-200';
      case 'medium':
        return 'text-orange-700 bg-orange-100 border-orange-200';
      case 'low':
        return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      default:
        return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getRecommendationIcon = (type) => {
    switch (type) {
      case 'immediate_action':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'pattern_detected':
        return <TrendingUp className="h-4 w-4 text-orange-500" />;
      case 'suspicious_source':
        return <Shield className="h-4 w-4 text-yellow-500" />;
      default:
        return <Target className="h-4 w-4 text-blue-500" />;
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-2 text-gray-600">Loading threat triage...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <AlertTriangle className="h-8 w-8 text-red-500 mr-2" />
          <span className="text-red-600">Error: {error}</span>
        </div>
      </div>
    );
  }

  if (!triageData || triageData.summary.total_active_alerts === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Threat Triage</h3>
          <Shield className="h-5 w-5 text-gray-400" />
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <CheckCircle className="h-12 w-12 text-green-300 mx-auto mb-2" />
            <p className="text-gray-500">No active threats to triage</p>
            <p className="text-sm text-gray-400">All alerts have been processed</p>
          </div>
        </div>
      </div>
    );
  }

  const currentAlerts = triageData[`${selectedPriority}_priority`] || [];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Threat Triage</h3>
          <p className="text-sm text-gray-500">
            {triageData.summary.total_active_alerts} active alerts requiring attention
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Avg Priority Score:</span>
          <span className="font-semibold text-indigo-600">
            {triageData.summary.average_priority_score}/100
          </span>
        </div>
      </div>

      {/* Priority Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          onClick={() => setSelectedPriority('high')}
          className={`p-4 rounded-lg border-2 text-left transition-colors ${
            selectedPriority === 'high' 
              ? 'border-red-300 bg-red-50' 
              : 'border-gray-200 hover:border-red-200'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-red-600">
                {triageData.summary.high_priority_count}
              </div>
              <div className="text-sm text-gray-600">High Priority</div>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </button>

        <button
          onClick={() => setSelectedPriority('medium')}
          className={`p-4 rounded-lg border-2 text-left transition-colors ${
            selectedPriority === 'medium' 
              ? 'border-orange-300 bg-orange-50' 
              : 'border-gray-200 hover:border-orange-200'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-orange-600">
                {triageData.summary.medium_priority_count}
              </div>
              <div className="text-sm text-gray-600">Medium Priority</div>
            </div>
            <Target className="h-8 w-8 text-orange-500" />
          </div>
        </button>

        <button
          onClick={() => setSelectedPriority('low')}
          className={`p-4 rounded-lg border-2 text-left transition-colors ${
            selectedPriority === 'low' 
              ? 'border-yellow-300 bg-yellow-50' 
              : 'border-gray-200 hover:border-yellow-200'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-yellow-600">
                {triageData.summary.low_priority_count}
              </div>
              <div className="text-sm text-gray-600">Low Priority</div>
            </div>
            <Eye className="h-8 w-8 text-yellow-500" />
          </div>
        </button>
      </div>

      {/* Recommendations */}
      {triageData.summary.recommendations && triageData.summary.recommendations.length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-semibold text-gray-900 mb-3">Recommendations</h4>
          <div className="space-y-2">
            {triageData.summary.recommendations.map((rec, index) => (
              <div key={index} className="flex items-center p-3 bg-blue-50 border border-blue-200 rounded-lg">
                {getRecommendationIcon(rec.type)}
                <span className="ml-3 text-sm text-gray-700">{rec.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-md font-semibold text-gray-900 capitalize">
            {selectedPriority} Priority Alerts
          </h4>
          {triageData.summary.most_common_attack && (
            <div className="text-sm text-gray-600">
              Most Common: <span className="font-medium">{triageData.summary.most_common_attack}</span>
            </div>
          )}
        </div>

        {currentAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-300 mx-auto mb-2" />
            <p className="text-gray-500">No {selectedPriority} priority alerts</p>
          </div>
        ) : (
          <div className="space-y-3">
            {currentAlerts.map((alert) => (
              <div 
                key={alert.id} 
                className={`border-2 rounded-lg p-4 ${getPriorityColor(alert.priority_level)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className="font-medium text-gray-900">{alert.attack_type}</span>
                      <span className="text-sm text-gray-500">
                        Score: {alert.priority_score}/100
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Source:</span>
                        <div className="font-mono">{alert.source_ip}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Destination:</span>
                        <div className="font-mono">{alert.destination_ip}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Anomaly Score:</span>
                        <div className="font-semibold">{alert.anomaly_score}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Time:</span>
                        <div>{formatTimestamp(alert.timestamp)}</div>
                      </div>
                    </div>

                    <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                      <span>Protocol: {alert.protocol}</span>
                      <span>Port: {alert.dst_port}</span>
                      <span>Confidence: {alert.confidence}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleAlertAction(alert.id, 'flag')}
                      className="p-2 text-orange-600 hover:bg-orange-100 rounded"
                      title="Flag alert"
                    >
                      <Flag className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleAlertAction(alert.id, 'dismiss')}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                      title="Dismiss alert"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Priority Score Bar */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Priority Score</span>
                    <span>{alert.priority_score}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        alert.priority_level === 'high' ? 'bg-red-500' :
                        alert.priority_level === 'medium' ? 'bg-orange-500' : 'bg-yellow-500'
                      }`}
                      style={{ width: `${alert.priority_score}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ThreatTriage;
