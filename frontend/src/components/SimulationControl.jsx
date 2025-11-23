import React, { useState, useEffect } from 'react';
import { Play, Square, Zap, Shield, Brain, CheckCircle } from 'lucide-react';
import io from 'socket.io-client';

const SimulationControl = () => {
  const [simulationStatus, setSimulationStatus] = useState({ active: false });
  const [availableAttacks, setAvailableAttacks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMode, setSelectedMode] = useState('normal');
  const [selectedAttack, setSelectedAttack] = useState('syn_flood');
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [socket, setSocket] = useState(null);
  const [notification, setNotification] = useState(null);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    fetchSimulationStatus();
    fetchAvailableAttacks();
    
    // Initialize WebSocket connection
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);
    
    // Listen for simulation start
    newSocket.on('simulation_started', (data) => {
      setNotification({
        type: 'info',
        message: `Starting ${data.attack_type || 'normal traffic'} simulation...`
      });
      setTimeout(() => setNotification(null), 3000);
    });
    
    // Listen for progress updates
    newSocket.on('mininet_progress', (data) => {
      setProgress(data.progress);
      setProgressMessage(data.message);
    });
    
    // Listen for completion
    newSocket.on('mininet_complete', (data) => {
      setSimulationStatus(prev => ({ ...prev, active: false }));
      setProgress(100);
      setProgressMessage('Completed!');
      setAlertCount(data.alert_count || 0);
      
      // Show success notification
      setNotification({
        type: 'success',
        message: `✅ Generated ${data.alert_count || 0} alerts!`
      });
      
      // Reset progress after delay
      setTimeout(() => {
        setProgress(0);
        setProgressMessage('');
        setNotification(null);
      }, 5000);
    });
    
    // Listen for batch alerts generated
    newSocket.on('alert_batch_generated', (data) => {
      setNotification({
        type: 'success',
        message: `🚨 ${data.count} new alerts detected!`
      });
      setTimeout(() => setNotification(null), 4000);
    });
    
    // Listen for simulation notifications
    newSocket.on('simulation_notification', (data) => {
      setNotification({
        type: data.type,
        message: `${data.title}: ${data.message}`
      });
      setTimeout(() => setNotification(null), 5000);
    });
    
    // Listen for errors
    newSocket.on('mininet_error', (data) => {
      setSimulationStatus(prev => ({ ...prev, active: false }));
      setProgress(0);
      setProgressMessage('');
      setNotification({
        type: 'error',
        message: `❌ ${data.message}`
      });
      setTimeout(() => setNotification(null), 5000);
    });
    
    return () => {
      newSocket.disconnect();
    };
  }, []);

  const fetchSimulationStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/mininet/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSimulationStatus(data);
      }
    } catch (error) {
      console.error('Error fetching simulation status:', error);
    }
  };

  const fetchAvailableAttacks = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/mininet/attacks', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAvailableAttacks(data.attacks || []);
      }
    } catch (error) {
      console.error('Error fetching available attacks:', error);
    }
  };

  const startSimulation = async () => {
    setLoading(true);
    setProgress(0);
    setProgressMessage('Starting PCAP replay...');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/mininet/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mode: selectedMode,
          attack_type: selectedMode === 'attack' ? selectedAttack : null,
          duration: 5
        })
      });
      
      const result = await response.json();
      if (result.success) {
        setSimulationStatus({ active: true, mode: selectedMode });
      } else {
        setProgress(0);
        setProgressMessage('');
      }
    } catch (error) {
      console.error('Error starting simulation:', error);
      setProgress(0);
      setProgressMessage('');
    } finally {
      setLoading(false);
    }
  };

  const stopSimulation = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/mininet/stop', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const result = await response.json();
      if (result.success) {
        setSimulationStatus(prev => ({ ...prev, active: false }));
      }
    } catch (error) {
      console.error('Error stopping simulation:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-6">
      {/* Notification Toast */}
      {notification && (
        <div className={`mb-4 p-3 rounded-lg border animate-pulse ${
          notification.type === 'success' ? 'bg-green-900/30 border-green-500/50 text-green-300' :
          notification.type === 'error' ? 'bg-red-900/30 border-red-500/50 text-red-300' :
          'bg-blue-900/30 border-blue-500/50 text-blue-300'
        }`}>
          <p className="text-sm font-medium">{notification.message}</p>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">PCAP Replay Simulation</h3>
          {alertCount > 0 && (
            <span className="ml-2 px-2 py-1 bg-red-500/20 border border-red-500/50 rounded text-xs text-red-300 font-bold animate-pulse">
              {alertCount} alerts
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${simulationStatus.active ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}></div>
          <span className="text-sm text-gray-400">{simulationStatus.active ? 'Running' : 'Stopped'}</span>
        </div>
      </div>

      {/* Progress Bar */}
      {(simulationStatus.active || progress > 0) && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-purple-400" />
              {progressMessage || 'Processing...'}
            </span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Mode</label>
          <select
            value={selectedMode}
            onChange={(e) => setSelectedMode(e.target.value)}
            className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600"
            disabled={simulationStatus.active || loading}
          >
            <option value="normal">Normal Traffic</option>
            <option value="attack">Attack</option>
          </select>
        </div>
        
        {selectedMode === 'attack' && (
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Attack Type</label>
            <select
              value={selectedAttack}
              onChange={(e) => setSelectedAttack(e.target.value)}
              className="w-full bg-gray-700 text-white px-3 py-2 rounded text-sm border border-gray-600"
              disabled={simulationStatus.active || loading}
            >
              {availableAttacks.map(attack => (
                <option key={attack} value={attack}>
                  {attack.replace('_', ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        {!simulationStatus.active ? (
          <button
            onClick={startSimulation}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 transition-all duration-200 shadow-lg shadow-green-500/30 text-sm font-medium"
          >
            <Play className="h-4 w-4" />
            {loading ? 'Starting...' : 'Start'}
          </button>
        ) : (
          <button
            onClick={stopSimulation}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-red-600 to-rose-600 text-white rounded-lg hover:from-red-700 hover:to-rose-700 disabled:opacity-50 transition-all duration-200 shadow-lg shadow-red-500/30 text-sm font-medium"
          >
            <Square className="h-4 w-4" />
            {loading ? 'Stopping...' : 'Stop'}
          </button>
        )}
      </div>

      {/* Model Info */}
      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle className="h-4 w-4 text-green-400" />
          <span className="text-xs font-medium text-gray-400">ML Model: Random Forest</span>
        </div>
        <div className="grid grid-cols-4 gap-2 text-center">
          <div>
            <div className="text-xs text-gray-500">Accuracy</div>
            <div className="text-sm font-bold text-green-400">95.25%</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Precision</div>
            <div className="text-sm font-bold text-blue-400">98.84%</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Recall</div>
            <div className="text-sm font-bold text-purple-400">95.53%</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">F1</div>
            <div className="text-sm font-bold text-yellow-400">97.16%</div>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="mt-3 p-3 bg-blue-900/20 border border-blue-700/30 rounded-lg">
        <p className="text-xs text-blue-300">
          <strong>PCAP Replay:</strong> Processes real network traffic through trained ML model. 
          Normal traffic generates few alerts, attacks generate many.
        </p>
      </div>
    </div>
  );
};

export default SimulationControl;
