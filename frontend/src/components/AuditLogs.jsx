import React, { useState, useEffect } from 'react';
import { 
  Activity, Filter, Download, Calendar, User, AlertTriangle,
  Shield, Eye, Search, ChevronLeft, ChevronRight, FileText, Database, FileSpreadsheet, File
} from 'lucide-react';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    username: '',
    event_type: '',
    start_date: '',
    end_date: '',
    limit: 50,
    offset: 0
  });
  const [summary, setSummary] = useState(null);
  const [securityAlerts, setSecurityAlerts] = useState([]);

  useEffect(() => {
    fetchAuditLogs();
    fetchAuditSummary();
    fetchSecurityAlerts();
  }, [filters]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchAuditLogs = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await fetch(`http://localhost:5000/api/admin/audit?${params}`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      } else {
        setError('Failed to fetch audit logs');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditSummary = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/audit/summary?days=30', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Failed to fetch audit summary:', err);
    }
  };

  const fetchSecurityAlerts = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/security-alerts?days=7', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setSecurityAlerts(data.alerts || []);
      }
    } catch (err) {
      console.error('Failed to fetch security alerts:', err);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      offset: 0 // Reset pagination when filters change
    }));
  };

  const handlePageChange = (direction) => {
    const newOffset = direction === 'next' 
      ? filters.offset + filters.limit
      : Math.max(0, filters.offset - filters.limit);
    
    setFilters(prev => ({ ...prev, offset: newOffset }));
  };

  const getEventTypeColor = (eventType) => {
    const colors = {
      'login_success': 'bg-green-100 text-green-800',
      'login_failed': 'bg-red-100 text-red-800',
      'logout': 'bg-slate-700/50 text-gray-800',
      'user_created': 'bg-blue-100 text-blue-800',
      'user_updated': 'bg-yellow-100 text-yellow-800',
      'user_deleted': 'bg-red-100 text-red-800',
      'alert_flagged': 'bg-orange-100 text-orange-800',
      'alert_dismissed': 'bg-purple-100 text-purple-800',
      'threshold_changed': 'bg-indigo-100 text-indigo-800',
      'unauthorized_access': 'bg-red-100 text-red-800',
      'mfa_enabled': 'bg-green-100 text-green-800',
      'mfa_disabled': 'bg-yellow-100 text-yellow-800'
    };
    return colors[eventType] || 'bg-slate-700/50 text-gray-800';
  };

  const formatEventType = (eventType) => {
    return eventType.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'high': 'bg-red-100 text-red-800 border-red-200',
      'medium': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'low': 'bg-blue-100 text-blue-800 border-blue-200'
    };
    return colors[severity] || 'bg-slate-700/50 text-gray-800 border-slate-700/50';
  };

  // Export Button Component
  const ExportButton = ({ filters }) => {
    const [showExportModal, setShowExportModal] = useState(false);
    const [exportFormats, setExportFormats] = useState([]);
    const [exportConfig, setExportConfig] = useState({
      format: 'json',
      severity: '',
      includeSummary: true
    });
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
      if (showExportModal) {
        fetchExportFormats();
      }
    }, [showExportModal]);

    const fetchExportFormats = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/admin/audit/export/formats', {
          headers: getAuthHeaders()
        });
        if (response.ok) {
          const data = await response.json();
          setExportFormats(data.formats || []);
        }
      } catch (error) {
        console.error('Error fetching export formats:', error);
      }
    };

    const handleExport = async () => {
      setExporting(true);
      try {
        const params = new URLSearchParams();
        
        // Add current filters
        if (filters.username) params.append('username', filters.username);
        if (filters.event_type) params.append('event_type', filters.event_type);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        
        // Add export config
        params.append('format', exportConfig.format);
        if (exportConfig.severity) params.append('severity', exportConfig.severity);
        params.append('include_summary', exportConfig.includeSummary.toString());

        const response = await fetch(`http://localhost:5000/api/admin/audit/export?${params.toString()}`, {
          headers: getAuthHeaders()
        });

        if (response.ok) {
          if (exportConfig.format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data.data, null, 2)], { 
              type: 'application/json' 
            });
            downloadFile(blob, data.filename);
          } else {
            const blob = await response.blob();
            const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 
                            `audit_export.${exportConfig.format}`;
            downloadFile(blob, filename);
          }
          setShowExportModal(false);
        } else {
          const error = await response.json();
          alert(`Export failed: ${error.error}`);
        }
      } catch (error) {
        console.error('Export error:', error);
        alert('Export failed. Please try again.');
      } finally {
        setExporting(false);
      }
    };

    const downloadFile = (blob, filename) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    };

    const getFormatIcon = (format) => {
      switch (format) {
        case 'json': return <Database className="w-4 h-4" />;
        case 'csv': return <FileText className="w-4 h-4" />;
        case 'excel': return <FileSpreadsheet className="w-4 h-4" />;
        case 'pdf': return <File className="w-4 h-4" />;
        default: return <Download className="w-4 h-4" />;
      }
    };

    return (
      <>
        <button
          onClick={() => setShowExportModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Download className="w-4 h-4" />
          Export Data
        </button>

        {/* Export Modal */}
        {showExportModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 w-full max-w-md mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-white">Export Audit Data</h3>
                <button
                  onClick={() => setShowExportModal(false)}
                  className="text-gray-400 hover:text-gray-400"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                {/* Format Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Export Format
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {exportFormats.map((format) => (
                      <button
                        key={format.value}
                        onClick={() => setExportConfig(prev => ({ ...prev, format: format.value }))}
                        className={`p-2 border rounded-lg flex items-center gap-2 text-sm transition-colors ${
                          exportConfig.format === format.value
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-slate-600/50 hover:border-gray-400'
                        }`}
                      >
                        {getFormatIcon(format.value)}
                        {format.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Severity Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Severity Filter (Optional)
                  </label>
                  <select
                    value={exportConfig.severity}
                    onChange={(e) => setExportConfig(prev => ({ ...prev, severity: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-600/50 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Severity Levels</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                {/* Include Summary */}
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={exportConfig.includeSummary}
                      onChange={(e) => setExportConfig(prev => ({ ...prev, includeSummary: e.target.checked }))}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-600/50 rounded"
                    />
                    <span className="text-sm text-gray-300">Include summary statistics</span>
                  </label>
                </div>

                {/* Current Filters Info */}
                <div className="bg-slate-900/50 p-3 rounded-lg">
                  <p className="text-sm font-medium text-gray-300 mb-1">Current Filters:</p>
                  <div className="text-xs text-gray-400 space-y-1">
                    {filters.username && <p>Username: {filters.username}</p>}
                    {filters.event_type && <p>Event Type: {filters.event_type}</p>}
                    {filters.start_date && <p>Start Date: {filters.start_date}</p>}
                    {filters.end_date && <p>End Date: {filters.end_date}</p>}
                    {!filters.username && !filters.event_type && !filters.start_date && !filters.end_date && (
                      <p>No filters applied - exporting all data</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowExportModal(false)}
                  className="px-4 py-2 text-gray-400 hover:text-gray-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleExport}
                  disabled={exporting}
                  className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
                    exporting
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  {exporting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      Export
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center">
            <Activity className="h-6 w-6 mr-2" />
            Audit Logs
          </h2>
          <p className="text-gray-400">Monitor all system activities and security events</p>
        </div>
        <ExportButton filters={filters} />
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Total Events (30d)</p>
                <p className="text-2xl font-bold text-white">{summary.total_events}</p>
              </div>
            </div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <User className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Successful Logins</p>
                <p className="text-2xl font-bold text-white">{summary.login_stats?.successful || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Failed Logins</p>
                <p className="text-2xl font-bold text-white">{summary.login_stats?.failed || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Success Rate</p>
                <p className="text-2xl font-bold text-white">{summary.login_stats?.success_rate || 0}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Security Alerts */}
      {securityAlerts && securityAlerts.length > 0 && (
        <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            Security Alerts (Last 7 Days)
          </h3>
          <div className="space-y-3">
            {securityAlerts.slice(0, 5).map((alert, index) => (
              <div key={alert.id || `${alert.timestamp}-${index}-${Math.random()}`} className={`p-3 rounded-md border ${getSeverityColor(alert.severity)}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{formatEventType(alert.type)}</p>
                    <p className="text-sm opacity-75">User: {alert.username || 'Unknown'}</p>
                    {alert.details && (
                      <p className="text-xs mt-1 opacity-75">
                        {JSON.stringify(alert.details)}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-slate-800/50 backdrop-blur-sm p-4 rounded-lg shadow-sm border">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Username</label>
            <input
              type="text"
              value={filters.username}
              onChange={(e) => handleFilterChange('username', e.target.value)}
              placeholder="Filter by username"
              className="w-full px-3 py-2 border border-slate-600/50 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Event Type</label>
            <select
              value={filters.event_type}
              onChange={(e) => handleFilterChange('event_type', e.target.value)}
              className="w-full px-3 py-2 border border-slate-600/50 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Events</option>
              <option value="login_success">Login Success</option>
              <option value="login_failed">Login Failed</option>
              <option value="user_created">User Created</option>
              <option value="user_updated">User Updated</option>
              <option value="user_deleted">User Deleted</option>
              <option value="alert_flagged">Alert Flagged</option>
              <option value="alert_dismissed">Alert Dismissed</option>
              <option value="unauthorized_access">Unauthorized Access</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Start Date</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-slate-600/50 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">End Date</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-slate-600/50 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Limit</label>
            <select
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-slate-600/50 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs Table */}
      <div className="bg-slate-800/50 backdrop-blur-sm shadow-sm rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700/50">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-white">Audit Events</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handlePageChange('prev')}
                disabled={filters.offset === 0}
                className="p-2 text-gray-400 hover:text-gray-400 disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-400">
                {filters.offset + 1} - {filters.offset + Math.min(filters.limit, logs?.length || 0)}
              </span>
              <button
                onClick={() => handlePageChange('next')}
                disabled={(logs?.length || 0) < filters.limit}
                className="p-2 text-gray-400 hover:text-gray-400 disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-700/50">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Event
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-slate-800/50 backdrop-blur-sm divide-y divide-slate-700/50">
                {(logs || []).map((log, index) => (
                  <tr key={log.id || `${log.timestamp}-${index}-${Math.random()}`} className="hover:bg-slate-900/50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEventTypeColor(log.event_type)}`}>
                        {formatEventType(log.event_type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {log.username || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {log.ip_address || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        log.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.success ? 'Success' : 'Failed'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-400 max-w-xs truncate">
                      {log.details && Object.keys(log.details).length > 0 
                        ? JSON.stringify(log.details)
                        : log.error_message || 'N/A'
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {(!logs || logs.length === 0) && (
              <div className="text-center py-12">
                <Activity className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-white">No audit logs found</h3>
                <p className="mt-1 text-sm text-gray-400">
                  Try adjusting your filter criteria.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogs;
