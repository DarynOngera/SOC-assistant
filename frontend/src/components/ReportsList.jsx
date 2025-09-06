import React, { useState, useEffect } from 'react';
import { 
  FileText, Calendar, User, AlertTriangle, Eye, Download, 
  RefreshCw, Search, Filter, ChevronDown, ChevronUp 
} from 'lucide-react';

const ReportsList = ({ onSelectReport }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterBy, setFilterBy] = useState('all');

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/csv/reports', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to fetch reports');
      }

      setReports(result.reports);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getSeverityColor = (percentage) => {
    if (percentage > 20) return 'text-red-600 bg-red-100';
    if (percentage > 10) return 'text-orange-600 bg-orange-100';
    if (percentage > 5) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const filteredAndSortedReports = reports
    .filter(report => {
      const matchesSearch = report.file_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           report.report_id.toLowerCase().includes(searchTerm.toLowerCase());
      
      if (filterBy === 'all') return matchesSearch;
      if (filterBy === 'high-anomaly') return matchesSearch && report.anomaly_percentage > 10;
      if (filterBy === 'low-anomaly') return matchesSearch && report.anomaly_percentage <= 5;
      if (filterBy === 'medium-anomaly') return matchesSearch && report.anomaly_percentage > 5 && report.anomaly_percentage <= 10;
      
      return matchesSearch;
    })
    .sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      
      if (sortBy === 'timestamp') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatNumber = (num) => {
    return num.toLocaleString();
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mr-3" />
          <p className="text-gray-600">Loading reports...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Error Loading Reports</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <button
                onClick={fetchReports}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Analysis Reports</h2>
            <p className="text-gray-600 mt-1">
              {reports.length} report{reports.length !== 1 ? 's' : ''} available
            </p>
          </div>
          <button
            onClick={fetchReports}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>

        {/* Search and Filter */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Search by filename or report ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="relative">
            <Filter className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <select
              value={filterBy}
              onChange={(e) => setFilterBy(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
            >
              <option value="all">All Reports</option>
              <option value="high-anomaly">High Anomaly ({'>'}10%)</option>
              <option value="medium-anomaly">Medium Anomaly (5-10%)</option>
              <option value="low-anomaly">Low Anomaly ({'≤'}5%)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Reports List */}
      <div className="p-6">
        {filteredAndSortedReports.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">
              {searchTerm || filterBy !== 'all' ? 'No reports match your criteria' : 'No reports available'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Table Header */}
            <div className="hidden md:grid md:grid-cols-6 gap-4 pb-2 border-b border-gray-200 text-sm font-medium text-gray-500">
              <button
                onClick={() => handleSort('file_name')}
                className="text-left flex items-center hover:text-gray-700"
              >
                File Name
                {sortBy === 'file_name' && (
                  sortOrder === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                )}
              </button>
              <button
                onClick={() => handleSort('timestamp')}
                className="text-left flex items-center hover:text-gray-700"
              >
                Date
                {sortBy === 'timestamp' && (
                  sortOrder === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                )}
              </button>
              <button
                onClick={() => handleSort('total_records')}
                className="text-left flex items-center hover:text-gray-700"
              >
                Records
                {sortBy === 'total_records' && (
                  sortOrder === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                )}
              </button>
              <button
                onClick={() => handleSort('anomalies_detected')}
                className="text-left flex items-center hover:text-gray-700"
              >
                Anomalies
                {sortBy === 'anomalies_detected' && (
                  sortOrder === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                )}
              </button>
              <button
                onClick={() => handleSort('anomaly_percentage')}
                className="text-left flex items-center hover:text-gray-700"
              >
                Rate
                {sortBy === 'anomaly_percentage' && (
                  sortOrder === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                )}
              </button>
              <div>Actions</div>
            </div>

            {/* Reports */}
            {filteredAndSortedReports.map((report) => (
              <div
                key={report.report_id}
                className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
              >
                <div className="md:grid md:grid-cols-6 gap-4 items-center">
                  {/* File Name - Mobile/Desktop */}
                  <div className="mb-2 md:mb-0">
                    <div className="flex items-center">
                      <FileText className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="font-medium text-gray-900 truncate">
                        {report.file_name}
                      </span>
                    </div>
                    <div className="md:hidden text-xs text-gray-500 mt-1">
                      ID: {report.report_id.substring(0, 8)}...
                    </div>
                  </div>

                  {/* Date */}
                  <div className="mb-2 md:mb-0">
                    <div className="md:hidden text-xs text-gray-500 mb-1">Date:</div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-1 md:hidden" />
                      {formatDate(report.timestamp)}
                    </div>
                  </div>

                  {/* Records */}
                  <div className="mb-2 md:mb-0">
                    <div className="md:hidden text-xs text-gray-500 mb-1">Records:</div>
                    <div className="text-sm font-medium text-gray-900">
                      {formatNumber(report.total_records)}
                    </div>
                  </div>

                  {/* Anomalies */}
                  <div className="mb-2 md:mb-0">
                    <div className="md:hidden text-xs text-gray-500 mb-1">Anomalies:</div>
                    <div className="text-sm font-medium text-red-600">
                      {formatNumber(report.anomalies_detected)}
                    </div>
                  </div>

                  {/* Rate */}
                  <div className="mb-2 md:mb-0">
                    <div className="md:hidden text-xs text-gray-500 mb-1">Rate:</div>
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(report.anomaly_percentage)}`}>
                      {report.anomaly_percentage.toFixed(2)}%
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onSelectReport(report.report_id)}
                      className="flex items-center px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      View
                    </button>
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

export default ReportsList;
