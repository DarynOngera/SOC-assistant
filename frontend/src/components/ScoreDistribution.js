import React, { useState, useEffect } from 'react';
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';
import { io } from 'socket.io-client';

const ScoreDistribution = () => {
  const [distributionData, setDistributionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartType, setChartType] = useState('bar');
  const [isLiveMode, setIsLiveMode] = useState(true); // Always start in live mode
  const [simulationActive, setSimulationActive] = useState(false);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    // Start with live endpoint (will be empty initially)
    fetchLiveDistributionData();
    const interval = setInterval(fetchLiveDistributionData, 10000); // Check for updates every 10 seconds
    
    // Set up WebSocket listener for real-time updates
    const socket = io('http://localhost:5000');
    
    // Listen for batch alerts from simulation
    socket.on('alert_batch_generated', (data) => {
      console.log('ScoreDistribution: Batch alerts generated, refreshing...');
      fetchLiveDistributionData();
    });
    
    // Listen for live score distribution updates
    socket.on('live_score_distribution', (data) => {
      console.log('ScoreDistribution: Received live score distribution');
      if (isLiveMode) {
        updateChartData(data);
      }
      setSimulationActive(data.simulation_active);
    });
    
    // Listen for simulation start
    socket.on('simulation_started', (data) => {
      console.log('ScoreDistribution: Simulation started');
      setSimulationActive(true);
      setHasData(false); // Will populate as simulation runs
    });
    
    // Listen for simulation complete
    socket.on('mininet_complete', (data) => {
      console.log('ScoreDistribution: Simulation complete, showing final results');
      setSimulationActive(false);
      fetchLiveDistributionData(); // Get final distribution
    });
    
    // Listen for simulation stopped
    socket.on('simulation_stopped', (data) => {
      console.log('ScoreDistribution: Simulation stopped');
      setSimulationActive(false);
    });
    
    return () => {
      clearInterval(interval);
      socket.disconnect();
    };
  }, []); // Empty dependency array - setup once on mount

  const updateChartData = (data) => {
    // Check if we have data
    const hasDataFlag = data.has_data !== undefined ? data.has_data : (data.bins && data.bins.length > 0);
    setHasData(hasDataFlag);
    
    // Transform data for chart (will be empty array if no data)
    const chartData = data.bins.map((bin, index) => ({
      score: bin.toFixed(2),
      count: data.counts[index],
      range: `${(bin - 0.025).toFixed(2)}-${(bin + 0.025).toFixed(2)}`
    }));
    setDistributionData(chartData);
    setLoading(false);
  };

  const fetchLiveDistributionData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/score-distribution/live', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        updateChartData(data);
        setSimulationActive(data.simulation_active);
      }
    } catch (error) {
      console.error('Error fetching live distribution data:', error);
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 backdrop-blur-sm p-4 border border-slate-600 rounded-lg shadow-2xl">
          <p className="font-semibold text-white mb-2">Score Range: {data.range}</p>
          <p className="text-sm text-gray-300">Count: <span className="font-medium text-white">{data.count}</span></p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-white">Score Distribution</h3>
        </div>
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-white">Score Distribution</h3>
          {isLiveMode && (
            <span className="ml-2 px-2 py-1 bg-green-500/20 border border-green-500/50 rounded text-xs text-green-300 font-bold animate-pulse">
              {simulationActive ? '🔴 LIVE' : '📊 LIVE RESULTS'}
            </span>
          )}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setChartType('bar')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              chartType === 'bar' 
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30' 
                : 'bg-slate-700/50 text-gray-300 hover:bg-slate-600/50'
            }`}
          >
            Bar
          </button>
          <button
            onClick={() => setChartType('line')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              chartType === 'line' 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-200 text-gray-300 hover:bg-gray-300'
            }`}
          >
            Line
          </button>
        </div>
      </div>

      {/* Empty state message */}
      {!hasData && !simulationActive && (
        <div className="h-64 flex items-center justify-center bg-slate-800/30 rounded-lg border border-slate-700/50">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">No simulation data yet</p>
            <p className="text-gray-500 text-xs mt-1">Run a simulation to see score distribution</p>
          </div>
        </div>
      )}

      {/* Chart (shown when we have data or simulation is active) */}
      {(hasData || simulationActive) && (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'bar' ? (
              <BarChart data={distributionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis 
                dataKey="score" 
                tick={{ fontSize: 12, fill: '#cbd5e1' }}
                stroke="#cbd5e1"
                interval="preserveStartEnd"
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#cbd5e1' }}
                stroke="#cbd5e1"
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
              <Bar 
                dataKey="count" 
                radius={[8, 8, 0, 0]}
              >
                {distributionData.map((entry, index) => {
                  const score = parseFloat(entry.score);
                  let fill = '#10b981'; // Green for low scores (normal)
                  if (score >= 0.8) fill = '#ef4444'; // Red for critical
                  else if (score >= 0.6) fill = '#f59e0b'; // Orange for high
                  else if (score >= 0.3) fill = '#eab308'; // Yellow for medium
                  return <Cell key={`cell-${index}`} fill={fill} />;
                })}
              </Bar>
            </BarChart>
          ) : (
            <LineChart data={distributionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis 
                dataKey="score" 
                tick={{ fontSize: 12, fill: '#cbd5e1' }}
                stroke="#cbd5e1"
                interval="preserveStartEnd"
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#cbd5e1' }}
                stroke="#cbd5e1"
              />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(59, 130, 246, 0.3)' }} />
              <Line 
                type="monotone" 
                dataKey="count" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: '#1d4ed8' }}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
        </div>
      )}

      {/* Color Legend - only show if we have data */}
      {hasData && (
        <>
      <div className="flex flex-wrap gap-3 justify-center pt-3 border-t border-slate-700/50">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-xs text-gray-400">Normal (0.0-0.3)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <span className="text-xs text-gray-400">Medium (0.3-0.6)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-500"></div>
          <span className="text-xs text-gray-400">High (0.6-0.8)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-xs text-gray-400">Critical (0.8+)</span>
        </div>
      </div>

      {/* Distribution Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
        <div className="text-center p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <div className="text-2xl font-bold text-green-400">
            {distributionData.filter(d => parseFloat(d.score) < 0.3).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-400 mt-1">Normal Traffic</div>
          <div className="text-xs text-green-400">Low Risk</div>
        </div>
        <div className="text-center p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <div className="text-2xl font-bold text-yellow-400">
            {distributionData.filter(d => parseFloat(d.score) >= 0.3 && parseFloat(d.score) < 0.6).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-400 mt-1">Suspicious</div>
          <div className="text-xs text-yellow-400">Medium Risk</div>
        </div>
        <div className="text-center p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg">
          <div className="text-2xl font-bold text-orange-400">
            {distributionData.filter(d => parseFloat(d.score) >= 0.6 && parseFloat(d.score) < 0.8).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-400 mt-1">Likely Attack</div>
          <div className="text-xs text-orange-400">High Risk</div>
        </div>
        <div className="text-center p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="text-2xl font-bold text-red-400">
            {distributionData.filter(d => parseFloat(d.score) >= 0.8).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-400 mt-1">Confirmed Attack</div>
          <div className="text-xs text-red-400">Critical</div>
        </div>
      </div>
      </>
      )}
    </div>
  );
};

export default ScoreDistribution;
