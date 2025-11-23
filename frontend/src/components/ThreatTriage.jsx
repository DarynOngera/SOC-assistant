import React, { useState, useEffect } from 'react';
import { AlertTriangle, Shield, Clock, Target, TrendingUp, Eye, Flag, X, CheckCircle, 
         ArrowUp, UserPlus, Search, FileText, Users, ChevronDown, ChevronUp } from 'lucide-react';
import { io } from 'socket.io-client';

const ThreatTriage = () => {
  const [triageData, setTriageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPriority, setSelectedPriority] = useState('high');
  const [selectedAlerts, setSelectedAlerts] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [analysts, setAnalysts] = useState([]);
  const [showTriageModal, setShowTriageModal] = useState(false);
  const [currentAlert, setCurrentAlert] = useState(null);
  const [triageAction, setTriageAction] = useState(null);

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

  const fetchAnalysts = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/analysts', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysts(data.analysts || []);
      }
    } catch (err) {
      console.error('Error fetching analysts:', err);
    }
  };

  const handleAlertAction = async (alertId, action, actionData = {}) => {
    try {
      const response = await fetch(`http://localhost:5000/api/alerts/${alertId}/${action}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(actionData)
      });

      if (response.ok) {
        // Refresh triage data after action
        fetchTriageData();
        setShowTriageModal(false);
        setCurrentAlert(null);
        setTriageAction(null);
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error || 'Action failed'}`);
      }
    } catch (err) {
      console.error(`Error ${action}ing alert:`, err);
      alert(`Error: Failed to ${action} alert`);
    }
  };

  const handleBulkAction = async (action, actionData = {}) => {
    if (selectedAlerts.length === 0) {
      alert('Please select alerts first');
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/api/alerts/bulk-triage', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          alert_ids: selectedAlerts,
          action: action,
          action_data: actionData
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Bulk action completed: ${result.successful} successful, ${result.failed} failed`);
        fetchTriageData();
        setSelectedAlerts([]);
        setShowBulkActions(false);
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error || 'Bulk action failed'}`);
      }
    } catch (err) {
      console.error(`Error in bulk ${action}:`, err);
      alert(`Error: Failed to perform bulk ${action}`);
    }
  };

  const openTriageModal = (alert, action) => {
    setCurrentAlert(alert);
    setTriageAction(action);
    setShowTriageModal(true);
  };

  const handleAlertSelection = (alertId) => {
    setSelectedAlerts(prev => 
      prev.includes(alertId) 
        ? prev.filter(id => id !== alertId)
        : [...prev, alertId]
    );
  };

  const selectAllAlerts = () => {
    const currentAlerts = triageData[`${selectedPriority}_priority`] || [];
    const allIds = currentAlerts.map(alert => alert.id);
    setSelectedAlerts(prev => 
      prev.length === allIds.length ? [] : allIds
    );
  };

  useEffect(() => {
    fetchTriageData();
    fetchAnalysts();
    
    // Set up polling as fallback
    const interval = setInterval(fetchTriageData, 30000); // Refresh every 30 seconds
    
    // Set up WebSocket for real-time updates
    const socket = io('http://localhost:5000');
    
    // Listen for new alerts and update triage immediately
    socket.on('new_alerts', (data) => {
      console.log('ThreatTriage: Received new alerts, refreshing...');
      fetchTriageData();
    });
    
    // Listen for alerts updates
    socket.on('alerts_update', (data) => {
      console.log('ThreatTriage: Alerts updated, refreshing...');
      fetchTriageData();
    });
    
    // Listen for batch alerts from simulation
    socket.on('alert_batch_generated', (data) => {
      console.log('ThreatTriage: Batch alerts generated, refreshing...');
      fetchTriageData();
    });
    
    return () => {
      clearInterval(interval);
      socket.disconnect();
    };
  }, []);

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'text-red-300 bg-red-900/30 border-red-500/30';
      case 'medium':
        return 'text-orange-300 bg-orange-900/30 border-orange-500/30';
      case 'low':
        return 'text-yellow-300 bg-yellow-900/30 border-yellow-500/30';
      default:
        return 'text-gray-300 bg-slate-700/50 border-slate-700/50';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'text-red-300 bg-red-600/20 border border-red-500/30';
      case 'high':
        return 'text-orange-300 bg-orange-600/20 border border-orange-500/30';
      case 'medium':
        return 'text-yellow-300 bg-yellow-600/20 border border-yellow-500/30';
      case 'low':
        return 'text-green-300 bg-green-600/20 border border-green-500/30';
      default:
        return 'text-gray-400 bg-slate-700/50';
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
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-2 text-gray-400">Loading threat triage...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <AlertTriangle className="h-8 w-8 text-red-500 mr-2" />
          <span className="text-red-600">Error: {error}</span>
        </div>
      </div>
    );
  }

  if (!triageData || triageData.summary.total_active_alerts === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Threat Triage</h3>
          <Shield className="h-5 w-5 text-gray-400" />
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <CheckCircle className="h-12 w-12 text-green-300 mx-auto mb-2" />
            <p className="text-gray-400">No active threats to triage</p>
            <p className="text-sm text-gray-400">All alerts have been processed</p>
          </div>
        </div>
      </div>
    );
  }

  const currentAlerts = triageData[`${selectedPriority}_priority`] || [];

  // Triage Modal Component
  const TriageModal = () => {
    const [formData, setFormData] = useState({});

    if (!showTriageModal || !currentAlert || !triageAction) return null;

    const handleSubmit = (e) => {
      e.preventDefault();
      handleAlertAction(currentAlert.id, triageAction, formData);
    };

    const renderModalContent = () => {
      switch (triageAction) {
        case 'escalate':
          return (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Escalate To
                </label>
                <select
                  value={formData.escalated_to || 'Senior Analyst'}
                  onChange={(e) => setFormData({...formData, escalated_to: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                >
                  <option value="Senior Analyst">Senior Analyst</option>
                  <option value="SOC Manager">SOC Manager</option>
                  <option value="Security Team Lead">Security Team Lead</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Escalation Reason
                </label>
                <textarea
                  value={formData.reason || ''}
                  onChange={(e) => setFormData({...formData, reason: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                  rows={3}
                  placeholder="Explain why this alert needs escalation..."
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.priority_increase !== false}
                  onChange={(e) => setFormData({...formData, priority_increase: e.target.checked})}
                  className="mr-2"
                />
                <label className="text-sm text-gray-300">Increase priority level</label>
              </div>
            </div>
          );

        case 'assign':
          return (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Assign To
                </label>
                <select
                  value={formData.assigned_to || ''}
                  onChange={(e) => setFormData({...formData, assigned_to: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                  required
                >
                  <option value="">Select an analyst...</option>
                  {analysts.map(analyst => (
                    <option key={analyst.username} value={analyst.username}>
                      {analyst.full_name} ({analyst.role})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Assignment Notes
                </label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                  rows={3}
                  placeholder="Add any specific instructions or context..."
                />
              </div>
            </div>
          );

        case 'investigate':
          return (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Investigation Priority
                </label>
                <select
                  value={formData.priority || 'medium'}
                  onChange={(e) => setFormData({...formData, priority: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Initial Investigation Notes
                </label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                  rows={4}
                  placeholder="Document initial findings, investigation plan, or relevant context..."
                />
              </div>
            </div>
          );

        case 'resolve':
          return (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Resolution Type
                </label>
                <select
                  value={formData.resolution_type || 'resolved'}
                  onChange={(e) => setFormData({...formData, resolution_type: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                >
                  <option value="resolved">Resolved</option>
                  <option value="false_positive">False Positive</option>
                  <option value="duplicate">Duplicate</option>
                  <option value="no_action_required">No Action Required</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Resolution Notes *
                </label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                  rows={3}
                  placeholder="Explain how the alert was resolved..."
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Action Taken
                </label>
                <textarea
                  value={formData.action_taken || ''}
                  onChange={(e) => setFormData({...formData, action_taken: e.target.value})}
                  className="w-full p-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                  rows={2}
                  placeholder="Describe any remediation actions taken..."
                />
              </div>
            </div>
          );

        default:
          return <div>Unknown action</div>;
      }
    };

    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-slate-800 border border-slate-700/50 rounded-lg shadow-2xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white capitalize">
              {triageAction} Alert #{currentAlert.id}
            </h3>
            <button
              onClick={() => setShowTriageModal(false)}
              className="text-gray-400 hover:text-gray-400"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="mb-4 p-3 bg-slate-900/50 rounded-lg">
            <div className="text-sm text-gray-400">
              <div><strong>Attack Type:</strong> {currentAlert.attack_type}</div>
              <div><strong>Source:</strong> {currentAlert.source_ip}</div>
              <div><strong>Severity:</strong> {currentAlert.severity}</div>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            {renderModalContent()}
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={() => setShowTriageModal(false)}
                className="px-4 py-2 text-gray-300 bg-slate-700/50 border border-slate-600/50 rounded-lg hover:bg-slate-600/50 transition-all duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all duration-200 shadow-lg shadow-blue-500/30"
              >
                {triageAction === 'resolve' ? 'Resolve' : 
                 triageAction === 'escalate' ? 'Escalate' :
                 triageAction === 'assign' ? 'Assign' : 'Start Investigation'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Threat Triage</h3>
          <p className="text-sm text-gray-400">
            {triageData.summary.total_active_alerts} active alerts requiring attention
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-400">Avg Priority Score:</span>
            <span className="font-semibold text-blue-400">
              {triageData.summary.average_priority_score}/100
            </span>
          </div>
          {selectedAlerts.length > 0 && (
            <button
              onClick={() => setShowBulkActions(!showBulkActions)}
              className="flex items-center space-x-2 px-3 py-1 bg-blue-600/20 text-blue-300 rounded-lg hover:bg-blue-600/30 transition-all duration-200 border border-blue-500/30"
            >
              <Users className="h-4 w-4" />
              <span>Bulk Actions ({selectedAlerts.length})</span>
              {showBulkActions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Bulk Actions Panel */}
      {showBulkActions && selectedAlerts.length > 0 && (
        <div className="mb-6 p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-white">Bulk Actions</h4>
            <span className="text-sm text-gray-400">{selectedAlerts.length} alerts selected</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleBulkAction('flag')}
              className="flex items-center space-x-1 px-3 py-1 bg-orange-600/20 text-orange-300 rounded-lg hover:bg-orange-600/30 transition-all duration-200 border border-orange-500/30"
            >
              <Flag className="h-4 w-4" />
              <span>Flag All</span>
            </button>
            <button
              onClick={() => handleBulkAction('dismiss')}
              className="flex items-center space-x-1 px-3 py-1 bg-slate-700/50 text-gray-300 rounded-lg hover:bg-slate-600/50 transition-all duration-200 border border-slate-600/50"
            >
              <X className="h-4 w-4" />
              <span>Dismiss All</span>
            </button>
            <button
              onClick={() => {
                const assignedTo = prompt('Assign to (username):');
                if (assignedTo) handleBulkAction('assign', { assigned_to: assignedTo });
              }}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-600/20 text-blue-300 rounded-lg hover:bg-blue-600/30 transition-all duration-200 border border-blue-500/30"
            >
              <UserPlus className="h-4 w-4" />
              <span>Assign All</span>
            </button>
          </div>
        </div>
      )}

      {/* Priority Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          onClick={() => setSelectedPriority('high')}
          className={`p-4 rounded-lg border-2 text-left transition-all duration-200 ${
            selectedPriority === 'high' 
              ? 'border-red-500/50 bg-red-900/20 shadow-lg shadow-red-500/20' 
              : 'border-slate-700/50 bg-slate-900/30 hover:border-red-500/30'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-red-600">
                {triageData.summary.high_priority_count}
              </div>
              <div className="text-sm text-gray-400">High Priority</div>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </button>

        <button
          onClick={() => setSelectedPriority('medium')}
          className={`p-4 rounded-lg border-2 text-left transition-all duration-200 ${
            selectedPriority === 'medium' 
              ? 'border-orange-500/50 bg-orange-900/20 shadow-lg shadow-orange-500/20' 
              : 'border-slate-700/50 bg-slate-900/30 hover:border-orange-500/30'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-orange-600">
                {triageData.summary.medium_priority_count}
              </div>
              <div className="text-sm text-gray-400">Medium Priority</div>
            </div>
            <Target className="h-8 w-8 text-orange-500" />
          </div>
        </button>

        <button
          onClick={() => setSelectedPriority('low')}
          className={`p-4 rounded-lg border-2 text-left transition-all duration-200 ${
            selectedPriority === 'low' 
              ? 'border-yellow-500/50 bg-yellow-900/20 shadow-lg shadow-yellow-500/20' 
              : 'border-slate-700/50 bg-slate-900/30 hover:border-yellow-500/30'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-yellow-600">
                {triageData.summary.low_priority_count}
              </div>
              <div className="text-sm text-gray-400">Low Priority</div>
            </div>
            <Eye className="h-8 w-8 text-yellow-500" />
          </div>
        </button>
      </div>

      {/* Recommendations */}
      {triageData.summary.recommendations && triageData.summary.recommendations.length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-semibold text-white mb-3">Recommendations</h4>
          <div className="space-y-2">
            {triageData.summary.recommendations.map((rec, index) => (
              <div key={index} className="flex items-center p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                {getRecommendationIcon(rec.type)}
                <span className="ml-3 text-sm text-gray-300">{rec.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-md font-semibold text-white capitalize">
            {selectedPriority} Priority Alerts
          </h4>
          {triageData.summary.most_common_attack && (
            <div className="text-sm text-gray-400">
              Most Common: <span className="font-medium">{triageData.summary.most_common_attack}</span>
            </div>
          )}
        </div>

        {currentAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-300 mx-auto mb-2" />
            <p className="text-gray-400">No {selectedPriority} priority alerts</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Select All Checkbox */}
            <div className="flex items-center space-x-3 pb-2 border-b border-slate-700/50">
              <input
                type="checkbox"
                checked={selectedAlerts.length === currentAlerts.length && currentAlerts.length > 0}
                onChange={selectAllAlerts}
                className="rounded"
              />
              <span className="text-sm text-gray-400">
                Select All ({currentAlerts.length} alerts)
              </span>
            </div>

            {currentAlerts.map((alert) => (
              <div 
                key={alert.id} 
                className={`border-2 rounded-lg p-4 ${getPriorityColor(alert.priority_level)} ${
                  selectedAlerts.includes(alert.id) ? 'ring-2 ring-indigo-300' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {/* Selection Checkbox */}
                    <input
                      type="checkbox"
                      checked={selectedAlerts.includes(alert.id)}
                      onChange={() => handleAlertSelection(alert.id)}
                      className="mt-1 rounded"
                    />

                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="font-medium text-white">{alert.attack_type}</span>
                        <span className="text-sm text-gray-400">
                          Score: {alert.priority_score}/100
                        </span>
                        {alert.status && alert.status !== 'new' && (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-blue-600/20 text-blue-300 border border-blue-500/30">
                            {alert.status.toUpperCase()}
                          </span>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Source:</span>
                          <div className="font-mono text-gray-300">{alert.source_ip}</div>
                        </div>
                        <div>
                          <span className="text-gray-400">Destination:</span>
                          <div className="font-mono text-gray-300">{alert.destination_ip}</div>
                        </div>
                        <div>
                          <span className="text-gray-400">Anomaly Score:</span>
                          <div className="font-semibold text-white">{alert.anomaly_score}</div>
                        </div>
                        <div>
                          <span className="text-gray-400">Time:</span>
                          <div className="text-gray-300">{formatTimestamp(alert.timestamp)}</div>
                        </div>
                      </div>

                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-400">
                        <span>Protocol: {alert.protocol}</span>
                        <span>Port: {alert.dst_port}</span>
                        <span>Confidence: {alert.confidence}</span>
                        {alert.assigned_to && (
                          <span className="text-blue-400">Assigned to: {alert.assigned_to}</span>
                        )}
                      </div>

                      {/* Investigation Status */}
                      {alert.investigation_started && (
                        <div className="mt-2 p-2 bg-blue-900/20 border border-blue-500/30 rounded text-sm">
                          <div className="flex items-center space-x-2">
                            <Search className="h-4 w-4 text-blue-600" />
                            <span className="text-blue-300 font-medium">
                              Investigation in progress by {alert.investigator}
                            </span>
                          </div>
                          {alert.investigation_notes && (
                            <div className="mt-1 text-blue-400 text-xs">
                              Latest: {alert.investigation_notes.split('\n').pop()}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Enhanced Action Buttons */}
                  <div className="flex items-center space-x-1 ml-4">
                    <button
                      onClick={() => openTriageModal(alert, 'escalate')}
                      className="p-2 text-red-400 hover:bg-red-600/20 rounded transition-colors border border-transparent hover:border-red-500/30"
                      title="Escalate alert"
                    >
                      <ArrowUp className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => openTriageModal(alert, 'assign')}
                      className="p-2 text-blue-400 hover:bg-blue-600/20 rounded transition-colors border border-transparent hover:border-blue-500/30"
                      title="Assign alert"
                    >
                      <UserPlus className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => openTriageModal(alert, 'investigate')}
                      className="p-2 text-purple-400 hover:bg-purple-600/20 rounded transition-colors border border-transparent hover:border-purple-500/30"
                      title="Start investigation"
                    >
                      <Search className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => openTriageModal(alert, 'resolve')}
                      className="p-2 text-green-400 hover:bg-green-600/20 rounded transition-colors border border-transparent hover:border-green-500/30"
                      title="Resolve alert"
                    >
                      <CheckCircle className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleAlertAction(alert.id, 'flag')}
                      className="p-2 text-orange-400 hover:bg-orange-600/20 rounded transition-colors border border-transparent hover:border-orange-500/30"
                      title="Flag alert"
                    >
                      <Flag className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleAlertAction(alert.id, 'dismiss')}
                      className="p-2 text-gray-400 hover:bg-slate-700/50 rounded"
                      title="Dismiss alert"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Priority Score Bar */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Priority Score</span>
                    <span>{alert.priority_score}/100</span>
                  </div>
                  <div className="w-full bg-slate-700/50 rounded-full h-2">
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

      {/* Triage Modal */}
      <TriageModal />
    </div>
  );
};

export default ThreatTriage;
