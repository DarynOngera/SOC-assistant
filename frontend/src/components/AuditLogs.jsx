import React, { useState, useEffect } from 'react';
import { 
  Activity, Filter, Download, Calendar, User, AlertTriangle,
  Shield, Eye, Search, ChevronLeft, ChevronRight
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
      'logout': 'bg-gray-100 text-gray-800',
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
    return colors[eventType] || 'bg-gray-100 text-gray-800';
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
    return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Activity className="h-6 w-6 mr-2" />
            Audit Logs
          </h2>
          <p className="text-gray-600">Monitor all system activities and security events</p>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Events (30d)</p>
                <p className="text-2xl font-bold text-gray-900">{summary.total_events}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <User className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Successful Logins</p>
                <p className="text-2xl font-bold text-gray-900">{summary.login_stats?.successful || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Failed Logins</p>
                <p className="text-2xl font-bold text-gray-900">{summary.login_stats?.failed || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">{summary.login_stats?.success_rate || 0}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Security Alerts */}
      {securityAlerts && securityAlerts.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
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
                    <p className="text-xs text-gray-500 mt-1">
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
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              type="text"
              value={filters.username}
              onChange={(e) => handleFilterChange('username', e.target.value)}
              placeholder="Filter by username"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
            <select
              value={filters.event_type}
              onChange={(e) => handleFilterChange('event_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Limit</label>
            <select
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
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
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">Audit Events</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handlePageChange('prev')}
                disabled={filters.offset === 0}
                className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-500">
                {filters.offset + 1} - {filters.offset + Math.min(filters.limit, logs?.length || 0)}
              </span>
              <button
                onClick={() => handlePageChange('next')}
                disabled={(logs?.length || 0) < filters.limit}
                className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
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
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Event
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(logs || []).map((log, index) => (
                  <tr key={log.id || `${log.timestamp}-${index}-${Math.random()}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEventTypeColor(log.event_type)}`}>
                        {formatEventType(log.event_type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.username || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        log.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {log.success ? 'Success' : 'Failed'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
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
                <h3 className="mt-2 text-sm font-medium text-gray-900">No audit logs found</h3>
                <p className="mt-1 text-sm text-gray-500">
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
