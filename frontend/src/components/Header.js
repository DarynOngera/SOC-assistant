import React from 'react';
import { Shield, Activity, Play, Square } from 'lucide-react';

const Header = ({ isConnected, onStartMonitoring, onStopMonitoring }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">SOC Dashboard</h1>
              <p className="text-sm text-gray-500">Real-time Anomaly Detection System</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              <div className={`status-indicator ${isConnected ? 'status-online' : 'status-offline'}`}></div>
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            {/* Monitoring Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={onStartMonitoring}
                className="flex items-center space-x-1 bg-success-600 hover:bg-success-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                <Play className="h-4 w-4" />
                <span>Start</span>
              </button>
              <button
                onClick={onStopMonitoring}
                className="flex items-center space-x-1 bg-danger-600 hover:bg-danger-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                <Square className="h-4 w-4" />
                <span>Stop</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
