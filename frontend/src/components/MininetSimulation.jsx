import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Square, 
  RefreshCw, 
  Settings, 
  AlertTriangle, 
  Shield, 
  Clock,
  Activity,
  Zap,
  Network,
  Target,
  CheckCircle,
  Brain
} from 'lucide-react';
import io from 'socket.io-client';

const MininetSimulation = () => {
  const [simulationStatus, setSimulationStatus] = useState({
    active: false,
    mode: null,
    simulation: null,
    duration: 0,
    elapsed: 0,
    remaining: 0,
    pid: null
  });
  const [availableAttacks, setAvailableAttacks] = useState([]);
  const [attackDescriptions, setAttackDescriptions] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedMode, setSelectedMode] = useState('normal');
  const [selectedAttack, setSelectedAttack] = useState('syn_flood');
  const [duration, setDuration] = useState(5);
  const [showSettings, setShowSettings] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    fetchSimulationStatus();
    fetchAvailableAttacks();
    
    // Initialize WebSocket connection
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);
    
    // Listen for progress updates
    newSocket.on('mininet_progress', (data) => {
      console.log('Progress update:', data);
      setProgress(data.progress);
      setProgressMessage(data.message);
    });
    
    // Listen for completion
    newSocket.on('mininet_complete', (data) => {
      console.log('Simulation complete:', data);
      setSimulationStatus(prev => ({
        ...prev,
        active: false,
        elapsed: prev.duration,
        remaining: 0
      }));
      setProgress(100);
      setProgressMessage('Simulation completed!');
      alert(`✅ ${data.message}`);
      
      // Reset progress after a delay
      setTimeout(() => {
        setProgress(0);
        setProgressMessage('');
      }, 3000);
    });
    
    // Listen for errors
    newSocket.on('mininet_error', (data) => {
      console.error('Simulation error:', data);
      setSimulationStatus(prev => ({ ...prev, active: false }));
      setProgress(0);
      setProgressMessage('');
      alert(`❌ Error: ${data.message}`);
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
        setAttackDescriptions(data.descriptions || {});
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
          duration: duration
        })
      });
      
      const result = await response.json();
      if (result.success) {
        // Update status immediately
        setSimulationStatus({
          active: true,
          mode: selectedMode,
          simulation: selectedMode === 'attack' ? selectedAttack : 'normal_traffic',
          duration: duration,
          elapsed: 0,
          remaining: duration,
          pid: null
        });
        
        // Show success message
        const modeText = selectedMode === 'attack' 
          ? `${selectedAttack.replace('_', ' ').toUpperCase()} attack` 
          : 'Normal traffic';
        alert(`🎬 ${modeText} PCAP replay started! Processing with trained ML model...`);
      } else {
        alert(`Failed to start simulation: ${result.message}`);
        setProgress(0);
        setProgressMessage('');
      }
    } catch (error) {
      console.error('Error starting simulation:', error);
      alert('Error starting simulation');
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
        // Update status immediately
        setSimulationStatus(prev => ({
          ...prev,
          active: false,
          elapsed: prev.duration,
          remaining: 0
        }));
        alert('Simulation stopped successfully!');
      } else {
        alert(`Failed to stop simulation: ${result.message}`);
      }
    } catch (error) {
      console.error('Error stopping simulation:', error);
      alert('Error stopping simulation');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = async (mode) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/mininet/switch-mode', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mode: mode,
          attack_type: mode === 'attack' ? selectedAttack : null
        })
      });
      
      const result = await response.json();
      if (result.success) {
        await fetchSimulationStatus();
      } else {
        alert(`Failed to switch mode: ${result.message}`);
      }
    } catch (error) {
      console.error('Error switching mode:', error);
      alert('Error switching mode');
    } finally {
      setLoading(false);
    }
  };

  const exportTopology = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/mininet/export-topology', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const result = await response.json();
      if (result.success) {
        alert(`Topology exported successfully to: ${result.file}`);
      } else {
        alert(`Failed to export topology: ${result.message}`);
      }
    } catch (error) {
      console.error('Error exporting topology:', error);
      alert('Error exporting topology');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = () => {
    if (!simulationStatus.active) return 'text-gray-400';
    if (simulationStatus.mode === 'attack') return 'text-red-400';
    return 'text-green-400';
  };

  const getStatusIcon = () => {
    if (!simulationStatus.active) return <Square className="h-5 w-5" />;
    if (simulationStatus.mode === 'attack') return <AlertTriangle className="h-5 w-5" />;
    return <Shield className="h-5 w-5" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Mininet Network Simulation</h2>
          <p className="text-gray-400">Control and monitor network traffic simulation</p>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
        >
          <Settings className="h-4 w-4" />
          Settings
        </button>
      </div>

      {/* Current Status */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Simulation Status</h3>
          <button
            onClick={fetchSimulationStatus}
            className="p-2 text-gray-400 hover:text-white"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <p className="text-sm text-gray-400">Status</p>
              <p className={`font-semibold ${getStatusColor()}`}>
                {simulationStatus.active ? 'Running' : 'Stopped'}
              </p>
            </div>
          </div>
          
          {simulationStatus.active && (
            <>
              <div className="flex items-center gap-3">
                <Network className="h-5 w-5 text-blue-400" />
                <div>
                  <p className="text-sm text-gray-400">Mode</p>
                  <p className="font-semibold text-white capitalize">
                    {simulationStatus.mode} 
                    {simulationStatus.simulation && simulationStatus.simulation !== 'normal_traffic' && 
                      ` (${simulationStatus.simulation.replace('_', ' ')})`
                    }
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-yellow-400" />
                <div>
                  <p className="text-sm text-gray-400">Time Remaining</p>
                  <p className="font-semibold text-white">
                    {formatTime(simulationStatus.remaining)}
                  </p>
                </div>
              </div>
            </>
          )}
        </div>

        {(simulationStatus.active || progress > 0) && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-purple-400" />
                {progressMessage || 'Processing with ML model...'}
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
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">Simulation Settings</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Simulation Mode
              </label>
              <select
                value={selectedMode}
                onChange={(e) => setSelectedMode(e.target.value)}
                className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
                disabled={simulationStatus.active}
              >
                <option value="normal">Normal Traffic</option>
                <option value="attack">Attack Simulation</option>
              </select>
            </div>
            
            {selectedMode === 'attack' && (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Attack Type
                </label>
                <select
                  value={selectedAttack}
                  onChange={(e) => setSelectedAttack(e.target.value)}
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
                  disabled={simulationStatus.active}
                >
                  {availableAttacks.map(attack => (
                    <option key={attack} value={attack}>
                      {attack.replace('_', ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
                {selectedAttack && attackDescriptions[selectedAttack] && (
                  <p className="text-sm text-gray-400 mt-2">
                    {attackDescriptions[selectedAttack]}
                  </p>
                )}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Duration (seconds)
              </label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                min="5"
                max="60"
                step="5"
                className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
                disabled={simulationStatus.active}
              />
              <p className="text-xs text-gray-500 mt-1">
                ⚡ Instant simulation: Alerts generated immediately! Duration is just for visual progress.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Control Buttons */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">Simulation Control</h3>
        
        <div className="flex flex-wrap gap-4">
          {!simulationStatus.active ? (
            <button
              onClick={startSimulation}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              {loading ? 'Starting...' : 'Start Simulation'}
            </button>
          ) : (
            <button
              onClick={stopSimulation}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              <Square className="h-4 w-4" />
              {loading ? 'Stopping...' : 'Stop Simulation'}
            </button>
          )}
          
          <button
            onClick={() => switchMode('normal')}
            disabled={loading || (simulationStatus.active && simulationStatus.mode === 'normal')}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Shield className="h-4 w-4" />
            Normal Mode
          </button>
          
          <button
            onClick={() => switchMode('attack')}
            disabled={loading || (simulationStatus.active && simulationStatus.mode === 'attack')}
            className="flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            <Zap className="h-4 w-4" />
            Attack Mode
          </button>
          
          <button
            onClick={exportTopology}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            <Activity className="h-4 w-4" />
            Export Topology
          </button>
        </div>
      </div>

      {/* Attack Types Reference */}
      {availableAttacks.length > 0 && (
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">Available Attack Types</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableAttacks.map(attack => (
              <div key={attack} className="bg-gray-700 p-4 rounded-lg">
                <h4 className="font-semibold text-white mb-2">
                  {attack.replace('_', ' ').toUpperCase()}
                </h4>
                <p className="text-sm text-gray-400">
                  {attackDescriptions[attack] || 'No description available'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PCAP Replay Info */}
      <div className="bg-blue-900 border border-blue-600 p-4 rounded-lg">
        <div className="flex items-start gap-3">
          <Brain className="h-5 w-5 text-blue-400 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-200 mb-2">🎬 PCAP Replay Mode with Trained ML Model</h4>
            <ul className="text-sm text-blue-300 space-y-1">
              <li>• <strong>Normal Traffic:</strong> Replays real network PCAP files (web browsing, SSH, DNS, etc.)</li>
              <li>• <strong>Attack Traffic:</strong> Replays attack PCAPs (SYN flood, port scan, UDP flood, etc.)</li>
              <li>• <strong>ML Detection:</strong> Uses trained Random Forest model (95.25% accuracy) to detect anomalies</li>
              <li>• <strong>Instant Results:</strong> Processes PCAP in 5-10 seconds and generates real alerts</li>
              <li>• <strong>Model Features:</strong> Analyzes 24 network features (ACK count, ports, packet sizes, etc.)</li>
            </ul>
          </div>
        </div>
      </div>
      
      {/* Model Performance */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-400" />
          Trained Model Performance
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-700 p-4 rounded">
            <p className="text-sm text-gray-400">Accuracy</p>
            <p className="text-2xl font-bold text-green-400">95.25%</p>
          </div>
          <div className="bg-gray-700 p-4 rounded">
            <p className="text-sm text-gray-400">Precision</p>
            <p className="text-2xl font-bold text-blue-400">98.84%</p>
          </div>
          <div className="bg-gray-700 p-4 rounded">
            <p className="text-sm text-gray-400">Recall</p>
            <p className="text-2xl font-bold text-purple-400">95.53%</p>
          </div>
          <div className="bg-gray-700 p-4 rounded">
            <p className="text-sm text-gray-400">F1 Score</p>
            <p className="text-2xl font-bold text-yellow-400">97.16%</p>
          </div>
        </div>
        <p className="text-sm text-gray-400 mt-4">
          Model trained on 3,156 network flows with 5 attack types and 5 normal traffic patterns.
        </p>
      </div>
    </div>
  );
};

export default MininetSimulation;
