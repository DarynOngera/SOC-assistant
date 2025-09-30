import React, { useState, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Loader, X } from 'lucide-react';

const CSVUpload = ({ onUploadSuccess, onAnalysisComplete }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, success, error
  const [analysisStatus, setAnalysisStatus] = useState('idle'); // idle, analyzing, success, error
  const [uploadedFile, setUploadedFile] = useState(null);
  const [error, setError] = useState('');
  const [sampleSize, setSampleSize] = useState('');

  const handleFile = async (file) => {
    // Validate file
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }

    if (file.size > 100 * 1024 * 1024) { // 100MB limit
      setError('File size must be less than 100MB');
      return;
    }

    setError('');
    setUploadStatus('uploading');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/csv/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      setUploadStatus('success');
      setUploadedFile(result.file_info);
      
      if (onUploadSuccess) {
        onUploadSuccess(result.file_info);
      }

    } catch (err) {
      setError(err.message);
      setUploadStatus('error');
    }
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!uploadedFile) return;

    setAnalysisStatus('analyzing');
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/csv/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_id: uploadedFile.file_id,
          sample_size: sampleSize ? parseInt(sampleSize) : undefined
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Analysis failed');
      }

      setAnalysisStatus('success');
      
      if (onAnalysisComplete) {
        onAnalysisComplete(result.report);
      }

    } catch (err) {
      setError(err.message);
      setAnalysisStatus('error');
    }
  };

  const resetUpload = () => {
    setUploadedFile(null);
    setUploadStatus('idle');
    setAnalysisStatus('idle');
    setError('');
    setSampleSize('');
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">CSV Anomaly Detection</h2>
        <p className="text-gray-400">Upload a CSV file to detect anomalies using trained ML models</p>
      </div>

      {!uploadedFile ? (
        // Upload Section
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-blue-400 bg-blue-50' 
              : 'border-slate-600/50 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={uploadStatus === 'uploading'}
          />
          
          <div className="space-y-4">
            {uploadStatus === 'uploading' ? (
              <div className="flex flex-col items-center">
                <Loader className="w-12 h-12 text-blue-500 animate-spin mb-2" />
                <p className="text-lg font-medium text-white">Uploading...</p>
              </div>
            ) : (
              <>
                <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                <div>
                  <p className="text-lg font-medium text-white">
                    Drop your CSV file here, or click to browse
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    Maximum file size: 100MB
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      ) : (
        // File Uploaded Section
        <div className="space-y-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 mr-3" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-green-800">File Uploaded Successfully</h3>
                <div className="mt-2 text-sm text-green-700">
                  <p><strong>Filename:</strong> {uploadedFile.filename}</p>
                  <p><strong>Size:</strong> {formatFileSize(uploadedFile.file_size)}</p>
                  <p><strong>Uploaded:</strong> {new Date(uploadedFile.upload_timestamp).toLocaleString()}</p>
                </div>
              </div>
              <button
                onClick={resetUpload}
                className="text-green-500 hover:text-green-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Analysis Configuration */}
          <div className="bg-slate-900/50 rounded-lg p-4">
            <h3 className="text-lg font-medium text-white mb-4">Analysis Configuration</h3>
            <div className="space-y-4">
              <div>
                <label htmlFor="sampleSize" className="block text-sm font-medium text-gray-300 mb-1">
                  Sample Size (optional)
                </label>
                <input
                  type="number"
                  id="sampleSize"
                  value={sampleSize}
                  onChange={(e) => setSampleSize(e.target.value)}
                  placeholder="Leave empty to analyze all rows (max 100,000)"
                  className="w-full px-3 py-2 border border-slate-600/50 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="100"
                  max="100000"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Limit the number of rows to analyze for faster processing
                </p>
              </div>
            </div>
          </div>

          {/* Analyze Button */}
          <div className="flex justify-center">
            <button
              onClick={handleAnalyze}
              disabled={analysisStatus === 'analyzing'}
              className={`px-6 py-3 rounded-lg font-medium text-white transition-colors ${
                analysisStatus === 'analyzing'
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {analysisStatus === 'analyzing' ? (
                <div className="flex items-center">
                  <Loader className="w-4 h-4 animate-spin mr-2" />
                  Analyzing...
                </div>
              ) : (
                <div className="flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                  Analyze for Anomalies
                </div>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Success */}
      {analysisStatus === 'success' && (
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-blue-800">Analysis Complete</h3>
              <p className="text-sm text-blue-700 mt-1">
                Anomaly detection analysis has been completed successfully. Check the results below.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CSVUpload;
