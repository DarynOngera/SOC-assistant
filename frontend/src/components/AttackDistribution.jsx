import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Shield, AlertTriangle, TrendingUp, Activity } from 'lucide-react';
import { io } from 'socket.io-client';

const AttackDistribution = () => {
  const [distributionData, setDistributionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('pie'); // 'pie' or 'bar'

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchDistributionData = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/attack-distribution', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setDistributionData(data);
        setError(null);
      } else {
        throw new Error('Failed to fetch attack distribution data');
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching attack distribution:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDistributionData();
    const interval = setInterval(fetchDistributionData, 30000); // Refresh every 30 seconds
    
    // Set up WebSocket listener for real-time updates
    const socket = io('http://localhost:5000');
    
    // Debounce timer to batch multiple updates
    let refreshTimer = null;
    
    // Listen for new alerts and update distribution immediately
    socket.on('new_alerts', (data) => {
      console.log('AttackDistribution: Received new alerts:', data.alerts?.length);
      // Batch updates to avoid rapid refreshes
      if (data.alerts && data.alerts.length > 0) {
        if (refreshTimer) clearTimeout(refreshTimer);
        refreshTimer = setTimeout(() => {
          fetchDistributionData();
          refreshTimer = null;
        }, 2000); // Wait 2 seconds to batch updates
      }
    });
    
    // Listen for alerts updates
    socket.on('alerts_update', (data) => {
      console.log('AttackDistribution: Alerts updated');
      if (data.alerts && data.alerts.length > 0) {
        if (refreshTimer) clearTimeout(refreshTimer);
        refreshTimer = setTimeout(() => {
          fetchDistributionData();
          refreshTimer = null;
        }, 2000);
      }
    });
    
    // Listen for batch alerts from simulation
    socket.on('alert_batch_generated', (data) => {
      console.log('AttackDistribution: Batch alerts generated:', data.count);
      // Immediate refresh for batch operations
      if (refreshTimer) clearTimeout(refreshTimer);
      fetchDistributionData();
    });
    
    return () => {
      clearInterval(interval);
      socket.disconnect();
      if (refreshTimer) clearTimeout(refreshTimer);
    };
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-2 text-gray-400">Loading attack distribution...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <AlertTriangle className="h-8 w-8 text-red-500 mr-2" />
          <span className="text-red-600">Error: {error}</span>
        </div>
      </div>
    );
  }

  if (!distributionData || distributionData.total_attacks === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Attack Type Distribution</h3>
          <Activity className="h-5 w-5 text-gray-400" />
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Shield className="h-12 w-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-400">No attack data available</p>
            <p className="text-sm text-gray-400">Start monitoring to see attack distribution</p>
          </div>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const chartData = Object.entries(distributionData.distribution).map(([attackType, data]) => ({
    name: attackType,
    count: data.count,
    percentage: data.percentage,
    threatScore: data.threat_score,
    severityBreakdown: data.severity_breakdown
  }));

  // Colors for different attack types
  const COLORS = [
    '#ef4444', // red-500
    '#f97316', // orange-500
    '#eab308', // yellow-500
    '#22c55e', // green-500
    '#3b82f6', // blue-500
    '#8b5cf6', // violet-500
    '#ec4899', // pink-500
    '#06b6d4', // cyan-500
    '#84cc16', // lime-500
    '#f59e0b'  // amber-500
  ];

  const getThreatLevelColor = (threatScore) => {
    if (threatScore >= 3.5) return 'text-red-600 bg-red-100';
    if (threatScore >= 2.5) return 'text-orange-600 bg-orange-100';
    if (threatScore >= 1.5) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getThreatLevelText = (threatScore) => {
    if (threatScore >= 3.5) return 'Critical';
    if (threatScore >= 2.5) return 'High';
    if (threatScore >= 1.5) return 'Medium';
    return 'Low';
  };

  const renderCustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 backdrop-blur-sm p-4 border border-slate-600 rounded-lg shadow-2xl">
          <p className="font-semibold text-white mb-2">{label}</p>
          <p className="text-sm text-gray-300">Count: <span className="font-medium text-white">{data.count}</span></p>
          <p className="text-sm text-gray-300">Percentage: <span className="font-medium text-white">{data.percentage}%</span></p>
          <p className="text-sm text-gray-300">Threat Score: <span className="font-medium text-white">{data.threatScore}</span></p>
          <div className="mt-3 pt-2 border-t border-slate-600">
            <p className="text-xs font-medium text-gray-400 mb-2">Severity Breakdown:</p>
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-300">Critical:</span>
                <span className="text-red-400 font-medium">{data.severityBreakdown.critical}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">High:</span>
                <span className="text-orange-400 font-medium">{data.severityBreakdown.high}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Medium:</span>
                <span className="text-yellow-400 font-medium">{data.severityBreakdown.medium}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Low:</span>
                <span className="text-green-400 font-medium">{data.severityBreakdown.low}</span>
              </div>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Attack Type Distribution</h3>
          <p className="text-sm text-gray-400">
            {distributionData.total_attacks} attacks in the last {distributionData.time_range}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('pie')}
            className={`px-3 py-1 rounded text-sm ${
              viewMode === 'pie' 
                ? 'bg-indigo-100 text-indigo-700' 
                : 'text-gray-400 hover:bg-slate-700/50'
            }`}
          >
            Pie Chart
          </button>
          <button
            onClick={() => setViewMode('bar')}
            className={`px-3 py-1 rounded text-sm ${
              viewMode === 'bar' 
                ? 'bg-indigo-100 text-indigo-700' 
                : 'text-gray-400 hover:bg-slate-700/50'
            }`}
          >
            Bar Chart
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={300}>
            {viewMode === 'pie' ? (
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => {
                    return (
                      <text 
                        x={0} 
                        y={0} 
                        fill="#e2e8f0" 
                        textAnchor="middle" 
                        dominantBaseline="central"
                        style={{ fontSize: '12px', fontWeight: '500' }}
                      >
                        {`${name}: ${percentage}%`}
                      </text>
                    );
                  }}
                  outerRadius={100}
                  dataKey="count"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={renderCustomTooltip} />
              </PieChart>
            ) : (
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  fontSize={12}
                  stroke="#cbd5e1"
                  tick={{ fill: '#cbd5e1' }}
                />
                <YAxis 
                  stroke="#cbd5e1"
                  tick={{ fill: '#cbd5e1' }}
                />
                <Tooltip content={renderCustomTooltip} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Top Threats Summary */}
        <div className="space-y-4">
          <h4 className="text-md font-semibold text-white">Top Threats</h4>
          {distributionData.top_threats.slice(0, 5).map((attackType, index) => {
            const data = distributionData.distribution[attackType];
            return (
              <div key={attackType} className="border border-slate-600/50 rounded-lg p-3 bg-slate-900/30">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm truncate" title={attackType}>
                    {attackType}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getThreatLevelColor(data.threat_score)}`}>
                    {getThreatLevelText(data.threat_score)}
                  </span>
                </div>
                <div className="flex justify-between text-sm text-gray-400">
                  <span>{data.count} attacks</span>
                  <span>{data.percentage}%</span>
                </div>
                <div className="mt-2">
                  <div className="flex justify-between text-xs">
                    <span>Threat Score:</span>
                    <span className="font-medium">{data.threat_score}/4.0</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div 
                      className="bg-indigo-600 h-1.5 rounded-full" 
                      style={{ width: `${(data.threat_score / 4) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-white">{distributionData.total_attacks}</div>
          <div className="text-sm text-gray-400">Total Attacks</div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-white">{Object.keys(distributionData.distribution).length}</div>
          <div className="text-sm text-gray-400">Attack Types</div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-indigo-600">{distributionData.top_threats[0] || 'N/A'}</div>
          <div className="text-sm text-gray-400">Top Threat</div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-white">{distributionData.time_range}</div>
          <div className="text-sm text-gray-400">Time Range</div>
        </div>
      </div>
    </div>
  );
};

export default AttackDistribution;
