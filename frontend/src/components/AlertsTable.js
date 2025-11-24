import React, { useState, useMemo } from 'react';
import { Flag, X, ChevronDown, ChevronUp, Search } from 'lucide-react';

const AlertsTable = ({ alerts, onAlertAction }) => {
  const [sortField, setSortField] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const filteredAndSortedAlerts = useMemo(() => {
    let filtered = alerts.filter(alert => {
      const matchesSearch = !searchTerm || 
        alert.source_ip.includes(searchTerm) ||
        alert.destination_ip.includes(searchTerm) ||
        alert.attack_type.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesSeverity = !filterSeverity || alert.severity === filterSeverity;
      const matchesStatus = !filterStatus || alert.status === filterStatus;
      
      return matchesSearch && matchesSeverity && matchesStatus;
    });

    return filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];
      
      if (sortField === 'timestamp') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }
      
      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }, [alerts, sortField, sortDirection, filterSeverity, filterStatus, searchTerm]);

  const paginatedAlerts = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredAndSortedAlerts.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredAndSortedAlerts, currentPage]);

  const totalPages = Math.ceil(filteredAndSortedAlerts.length / itemsPerPage);

  const getSeverityBadge = (severity) => {
    const badges = {
      critical: 'badge badge-critical',
      high: 'badge badge-high',
      medium: 'badge badge-medium',
      low: 'badge badge-low'
    };
    return badges[severity] || 'badge bg-gray-100 text-gray-800';
  };

  const getStatusBadge = (status) => {
    const badges = {
      new: 'badge bg-blue-100 text-blue-800',
      flagged: 'badge bg-purple-100 text-purple-800',
      dismissed: 'badge bg-gray-100 text-gray-800'
    };
    return badges[status] || 'badge bg-gray-100 text-gray-800';
  };

  const formatTimestamp = (timestamp) => {
    // Parse ISO timestamp (handles UTC properly)
    const date = new Date(timestamp);
    
    // Validate date
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    
    return date.toLocaleString();
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? 
      <ChevronUp className="h-4 w-4" /> : 
      <ChevronDown className="h-4 w-4" />;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Alert Prioritization</h3>
        <div className="text-sm text-gray-400">
          {filteredAndSortedAlerts.length} of {alerts.length} alerts
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search by IP address or attack type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          />
        </div>
        
        <select
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="flagged">Flagged</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-700/50">
          <thead className="bg-slate-900/50">
            <tr>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/30 transition-colors"
                onClick={() => handleSort('timestamp')}
              >
                <div className="flex items-center space-x-1">
                  <span>Timestamp</span>
                  <SortIcon field="timestamp" />
                </div>
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/30 transition-colors"
                onClick={() => handleSort('severity')}
              >
                <div className="flex items-center space-x-1">
                  <span>Severity</span>
                  <SortIcon field="severity" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Source IP
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Destination IP
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Attack Type
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/30 transition-colors"
                onClick={() => handleSort('anomaly_score')}
              >
                <div className="flex items-center space-x-1">
                  <span>Score</span>
                  <SortIcon field="anomaly_score" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-slate-800/30 divide-y divide-slate-700/50">
            {paginatedAlerts.map((alert, index) => (
              <tr key={`alert-${alert.alert_id}-${alert.timestamp}-${index}`} className="hover:bg-slate-700/30 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatTimestamp(alert.timestamp)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={getSeverityBadge(alert.severity)}>
                    {alert.severity}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-300">
                  {alert.source_ip}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-300">
                  {alert.destination_ip}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {alert.attack_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-1 bg-slate-700/50 rounded-full h-2 mr-2">
                      <div
                        className={`h-2 rounded-full ${
                          alert.anomaly_score >= 0.8 ? 'bg-danger-500' :
                          alert.anomaly_score >= 0.6 ? 'bg-warning-500' :
                          alert.anomaly_score >= 0.4 ? 'bg-yellow-500' : 'bg-success-500'
                        }`}
                        style={{ width: `${alert.anomaly_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-400 min-w-[3rem]">
                      {alert.anomaly_score}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={getStatusBadge(alert.status)}>
                    {alert.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onAlertAction(alert.alert_id, 'flag')}
                      disabled={alert.status === 'flagged'}
                      className="text-warning-600 hover:text-warning-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                      title="Flag Alert"
                    >
                      <Flag className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onAlertAction(alert.alert_id, 'dismiss')}
                      disabled={alert.status === 'dismissed'}
                      className="text-gray-600 hover:text-gray-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                      title="Dismiss Alert"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-300">
            Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredAndSortedAlerts.length)} of {filteredAndSortedAlerts.length} results
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600/50 transition-all duration-200"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm text-gray-300">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 bg-slate-700/50 border border-slate-600/50 rounded-lg text-sm text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600/50 transition-all duration-200"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsTable;
