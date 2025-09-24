import React, { useState, useEffect } from 'react';
import { Download, Calendar, Filter, FileText, Database, FileSpreadsheet, File } from 'lucide-react';

const AuditExport = () => {
  const [exportFormats, setExportFormats] = useState([]);
  const [eventTypes, setEventTypes] = useState([]);
  const [severityLevels, setSeverityLevels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exportConfig, setExportConfig] = useState({
    format: 'json',
    startDate: '',
    endDate: '',
    eventType: '',
    username: '',
    severity: '',
    includeSummary: true
  });

  useEffect(() => {
    fetchExportFormats();
  }, []);

  const fetchExportFormats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/audit/export/formats', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setExportFormats(data.formats || []);
        setEventTypes(data.event_types || []);
        setSeverityLevels(data.severity_levels || []);
      }
    } catch (error) {
      console.error('Error fetching export formats:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setExportConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleExport = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      
      // Add non-empty parameters
      Object.entries(exportConfig).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
          if (key === 'includeSummary') {
            params.append('include_summary', value.toString());
          } else if (key === 'startDate') {
            params.append('start_date', value);
          } else if (key === 'endDate') {
            params.append('end_date', value);
          } else if (key === 'eventType') {
            params.append('event_type', value);
          } else {
            params.append(key, value);
          }
        }
      });

      const response = await fetch(`/api/admin/audit/export?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        if (exportConfig.format === 'json') {
          // Handle JSON response
          const data = await response.json();
          const blob = new Blob([JSON.stringify(data.data, null, 2)], { 
            type: 'application/json' 
          });
          downloadFile(blob, data.filename);
        } else {
          // Handle file download
          const blob = await response.blob();
          const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 
                          `audit_export.${exportConfig.format}`;
          downloadFile(blob, filename);
        }
      } else {
        const error = await response.json();
        alert(`Export failed: ${error.error}`);
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    } finally {
      setLoading(false);
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

  const setQuickDateRange = (days) => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    setExportConfig(prev => ({
      ...prev,
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0]
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-6">
        <Download className="w-5 h-5 text-blue-600" />
        <h2 className="text-xl font-semibold text-gray-800">Export Audit Data</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Export Format Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Export Format
          </label>
          <div className="grid grid-cols-2 gap-2">
            {exportFormats.map((format) => (
              <button
                key={format.value}
                onClick={() => handleInputChange('format', format.value)}
                className={`p-3 border rounded-lg flex items-center gap-2 transition-colors ${
                  exportConfig.format === format.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {getFormatIcon(format.value)}
                <div className="text-left">
                  <div className="font-medium">{format.label}</div>
                  <div className="text-xs text-gray-500">{format.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Calendar className="w-4 h-4 inline mr-1" />
            Date Range
          </label>
          <div className="space-y-2">
            <div className="flex gap-2">
              <input
                type="date"
                value={exportConfig.startDate}
                onChange={(e) => handleInputChange('startDate', e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Start Date"
              />
              <input
                type="date"
                value={exportConfig.endDate}
                onChange={(e) => handleInputChange('endDate', e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="End Date"
              />
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setQuickDateRange(7)}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
              >
                Last 7 days
              </button>
              <button
                onClick={() => setQuickDateRange(30)}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
              >
                Last 30 days
              </button>
              <button
                onClick={() => setQuickDateRange(90)}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
              >
                Last 90 days
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Filter className="w-4 h-4 inline mr-1" />
            Filters
          </label>
          <div className="space-y-2">
            <select
              value={exportConfig.eventType}
              onChange={(e) => handleInputChange('eventType', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Event Types</option>
              {eventTypes.map((type) => (
                <option key={type} value={type}>
                  {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>

            <select
              value={exportConfig.severity}
              onChange={(e) => handleInputChange('severity', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severity Levels</option>
              {severityLevels.map((level) => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>

            <input
              type="text"
              value={exportConfig.username}
              onChange={(e) => handleInputChange('username', e.target.value)}
              placeholder="Filter by username (optional)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Export Options
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exportConfig.includeSummary}
                onChange={(e) => handleInputChange('includeSummary', e.target.checked)}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">Include summary statistics</span>
            </label>
          </div>
        </div>
      </div>

      {/* Export Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleExport}
          disabled={loading}
          className={`px-6 py-2 rounded-md font-medium flex items-center gap-2 ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Exporting...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              Export Data
            </>
          )}
        </button>
      </div>

      {/* Format Information */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Export Format Information</h3>
        <div className="text-xs text-gray-600 space-y-1">
          {exportFormats.find(f => f.value === exportConfig.format) && (
            <p>
              <strong>{exportFormats.find(f => f.value === exportConfig.format).label}:</strong>{' '}
              {exportFormats.find(f => f.value === exportConfig.format).description}
            </p>
          )}
          <p>
            <strong>Note:</strong> Large exports may take some time to process. 
            PDF exports are limited to the first 100 records for readability.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuditExport;
