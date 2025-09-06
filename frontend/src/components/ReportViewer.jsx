import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Eye, Calendar, User, AlertTriangle, 
  CheckCircle, BarChart3, TrendingUp, Shield, Info,
  ChevronDown, ChevronRight, RefreshCw
} from 'lucide-react';

const ReportViewer = ({ report, onClose }) => {
  const [activeTab, setActiveTab] = useState('summary');
  const [expandedSections, setExpandedSections] = useState({
    recommendations: true,
    detailed: false,
    raw: false
  });

  if (!report) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 text-center">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No report selected</p>
      </div>
    );
  }

  const downloadReport = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:5000/api/csv/reports/${report.report_id}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `anomaly_report_${report.report_id}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const formatPercentage = (value) => `${value.toFixed(2)}%`;
  const formatNumber = (value) => value.toLocaleString();

  const getSeverityColor = (percentage) => {
    if (percentage > 20) return 'text-red-600 bg-red-100';
    if (percentage > 10) return 'text-orange-600 bg-orange-100';
    if (percentage > 5) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const renderSummaryTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm text-blue-600 font-medium">Total Records</p>
              <p className="text-2xl font-bold text-blue-900">
                {formatNumber(report.summary_statistics.total_records_analyzed)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-red-50 p-4 rounded-lg">
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-red-600 mr-3" />
            <div>
              <p className="text-sm text-red-600 font-medium">Anomalies Detected</p>
              <p className="text-2xl font-bold text-red-900">
                {formatNumber(report.summary_statistics.anomalies_detected)}
              </p>
            </div>
          </div>
        </div>

        <div className={`p-4 rounded-lg ${getSeverityColor(report.summary_statistics.anomaly_rate_percentage)}`}>
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 mr-3" />
            <div>
              <p className="text-sm font-medium">Anomaly Rate</p>
              <p className="text-2xl font-bold">
                {formatPercentage(report.summary_statistics.anomaly_rate_percentage)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm text-green-600 font-medium">Normal Records</p>
              <p className="text-2xl font-bold text-green-900">
                {formatNumber(report.summary_statistics.normal_records)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* File Information */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">File Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p><strong>Filename:</strong> {report.file_info.filename}</p>
            <p><strong>File Size:</strong> {(report.file_info.file_size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          <div>
            <p><strong>Analyzed By:</strong> {report.file_info.analyzed_by}</p>
            <p><strong>Analysis Date:</strong> {new Date(report.timestamp).toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Model Performance */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Model Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded">
            <p className="text-2xl font-bold text-blue-600">
              {report.summary_statistics.model_performance.high_confidence_anomalies}
            </p>
            <p className="text-sm text-blue-700">High Confidence</p>
            <p className="text-xs text-gray-600">(Score {'>'}  0.8)</p>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded">
            <p className="text-2xl font-bold text-yellow-600">
              {report.summary_statistics.model_performance.medium_confidence_anomalies}
            </p>
            <p className="text-sm text-yellow-700">Medium Confidence</p>
            <p className="text-xs text-gray-600">(Score 0.5-0.8)</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded">
            <p className="text-2xl font-bold text-gray-600">
              {report.summary_statistics.model_performance.low_confidence_anomalies}
            </p>
            <p className="text-sm text-gray-700">Low Confidence</p>
            <p className="text-xs text-gray-600">(Score 0.3-0.5)</p>
          </div>
        </div>
      </div>

      {/* Visualization */}
      {report.visualizations && report.visualizations.main_analysis && (
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Analysis Visualization</h3>
          <div className="text-center">
            <img 
              src={`data:image/png;base64,${report.visualizations.main_analysis}`}
              alt="Anomaly Analysis Charts"
              className="max-w-full h-auto mx-auto rounded-lg shadow-sm"
            />
          </div>
        </div>
      )}
    </div>
  );

  const renderRecommendationsTab = () => (
    <div className="space-y-4">
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
        <div className="flex">
          <Info className="w-5 h-5 text-blue-400 mt-0.5 mr-3" />
          <div>
            <h3 className="text-lg font-medium text-blue-800">Actionable Recommendations</h3>
            <p className="text-blue-700 text-sm mt-1">
              Based on the analysis results, here are recommended next steps:
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {report.recommendations.map((recommendation, index) => (
          <div key={index} className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start">
              <div className="bg-blue-100 rounded-full p-2 mr-3 mt-1">
                <span className="text-blue-600 font-semibold text-sm">{index + 1}</span>
              </div>
              <p className="text-gray-800 flex-1">{recommendation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderDetailsTab = () => (
    <div className="space-y-6">
      {/* Data Quality Assessment */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Data Quality Assessment</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p><strong>Original Records:</strong> {formatNumber(report.detailed_analysis.data_quality_assessment.original_records)}</p>
            <p><strong>Processed Records:</strong> {formatNumber(report.detailed_analysis.data_quality_assessment.processed_records)}</p>
          </div>
          <div>
            <p><strong>Features Analyzed:</strong> {report.detailed_analysis.data_quality_assessment.features_analyzed}</p>
            <p><strong>Data Completeness:</strong> 
              <span className={`ml-2 px-2 py-1 rounded text-xs ${
                report.detailed_analysis.data_quality_assessment.data_completeness === 'Good' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {report.detailed_analysis.data_quality_assessment.data_completeness}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Anomaly Patterns */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Anomaly Patterns</h3>
        <div className="space-y-2 text-sm">
          <p><strong>Distribution Type:</strong> {report.detailed_analysis.anomaly_patterns.distribution_type}</p>
          <p><strong>Score Concentration:</strong> {report.detailed_analysis.anomaly_patterns.score_concentration}</p>
          <p><strong>Potential Attack Indicators:</strong> 
            <span className={`ml-2 px-2 py-1 rounded text-xs ${
              report.detailed_analysis.anomaly_patterns.potential_attack_indicators 
                ? 'bg-red-100 text-red-800' 
                : 'bg-green-100 text-green-800'
            }`}>
              {report.detailed_analysis.anomaly_patterns.potential_attack_indicators ? 'Yes' : 'No'}
            </span>
          </p>
        </div>
      </div>

      {/* Score Statistics */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Score Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center p-2 bg-gray-50 rounded">
            <p className="font-semibold text-gray-900">{report.summary_statistics.score_statistics.mean_score.toFixed(3)}</p>
            <p className="text-gray-600">Mean</p>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <p className="font-semibold text-gray-900">{report.summary_statistics.score_statistics.median_score.toFixed(3)}</p>
            <p className="text-gray-600">Median</p>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <p className="font-semibold text-gray-900">{report.summary_statistics.score_statistics.percentile_95.toFixed(3)}</p>
            <p className="text-gray-600">95th %ile</p>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <p className="font-semibold text-gray-900">{report.summary_statistics.score_statistics.max_score.toFixed(3)}</p>
            <p className="text-gray-600">Maximum</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Anomaly Detection Report</h2>
            <p className="text-gray-600 mt-1">
              Report ID: {report.report_id} • Generated: {new Date(report.timestamp).toLocaleString()}
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={downloadReport}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {[
            { id: 'summary', label: 'Summary', icon: BarChart3 },
            { id: 'recommendations', label: 'Recommendations', icon: Shield },
            { id: 'details', label: 'Details', icon: Eye }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4 mr-2" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'summary' && renderSummaryTab()}
        {activeTab === 'recommendations' && renderRecommendationsTab()}
        {activeTab === 'details' && renderDetailsTab()}
      </div>
    </div>
  );
};

export default ReportViewer;
