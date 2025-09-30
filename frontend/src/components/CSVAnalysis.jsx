import React, { useState, useEffect } from 'react';
import CSVUpload from './CSVUpload';
import ReportViewer from './ReportViewer';
import ReportsList from './ReportsList';
import { FileText, Upload, List, ArrowLeft } from 'lucide-react';

const CSVAnalysis = () => {
  const [activeView, setActiveView] = useState('upload'); // upload, reports, report-detail
  const [currentReport, setCurrentReport] = useState(null);
  const [refreshReports, setRefreshReports] = useState(0);

  const handleUploadSuccess = (fileInfo) => {
    console.log('File uploaded successfully:', fileInfo);
  };

  const handleAnalysisComplete = (report) => {
    setCurrentReport(report);
    setActiveView('report-detail');
    setRefreshReports(prev => prev + 1); // Trigger reports list refresh
  };

  const handleSelectReport = async (reportId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:5000/api/csv/reports/${reportId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const report = await response.json();
        setCurrentReport(report);
        setActiveView('report-detail');
      }
    } catch (error) {
      console.error('Failed to fetch report:', error);
    }
  };

  const handleBackToReports = () => {
    setCurrentReport(null);
    setActiveView('reports');
  };

  const handleBackToUpload = () => {
    setCurrentReport(null);
    setActiveView('upload');
  };

  return (
    <div className="min-h-screen bg-slate-900/50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Navigation Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">CSV Anomaly Analysis</h1>
              <p className="text-gray-400 mt-1">
                Upload CSV files to detect anomalies and generate comprehensive reports
              </p>
            </div>
            
            {/* Navigation Tabs */}
            <div className="flex space-x-1 bg-gray-200 rounded-lg p-1">
              <button
                onClick={() => setActiveView('upload')}
                className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeView === 'upload'
                    ? 'bg-slate-800/50 backdrop-blur-sm text-blue-600 shadow-sm'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload
              </button>
              <button
                onClick={() => setActiveView('reports')}
                className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeView === 'reports'
                    ? 'bg-slate-800/50 backdrop-blur-sm text-blue-600 shadow-sm'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <List className="w-4 h-4 mr-2" />
                Reports
              </button>
            </div>
          </div>

          {/* Breadcrumb for report detail view */}
          {activeView === 'report-detail' && (
            <div className="mt-4 flex items-center text-sm text-gray-400">
              <button
                onClick={handleBackToReports}
                className="flex items-center hover:text-gray-300"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back to Reports
              </button>
              <span className="mx-2">/</span>
              <span>Report Details</span>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {activeView === 'upload' && (
            <CSVUpload
              onUploadSuccess={handleUploadSuccess}
              onAnalysisComplete={handleAnalysisComplete}
            />
          )}

          {activeView === 'reports' && (
            <ReportsList
              key={refreshReports}
              onSelectReport={handleSelectReport}
            />
          )}

          {activeView === 'report-detail' && currentReport && (
            <ReportViewer
              report={currentReport}
              onClose={handleBackToReports}
            />
          )}
        </div>

        {/* Help Section */}
        {activeView === 'upload' && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">How to Use CSV Analysis</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-800">
              <div>
                <h4 className="font-medium mb-2">1. Upload Your CSV</h4>
                <p>Drag and drop or select a CSV file containing network traffic or security data. Maximum file size is 100MB.</p>
              </div>
              <div>
                <h4 className="font-medium mb-2">2. Configure Analysis</h4>
                <p>Optionally set a sample size to limit the number of rows processed for faster analysis on large datasets.</p>
              </div>
              <div>
                <h4 className="font-medium mb-2">3. Review Results</h4>
                <p>Get detailed anomaly detection results with visualizations, statistics, and actionable recommendations.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CSVAnalysis;
