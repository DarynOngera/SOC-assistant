import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, TrendingDown, Minus, Clock, AlertTriangle, Activity } from 'lucide-react';
import { io } from 'socket.io-client';

const AttackTrends = () => {
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState(24); // hours
  const [granularity, setGranularity] = useState('30min');

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchTrendsData = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:5000/api/attack-trends?hours=${timeRange}&granularity=${granularity}`,
        { headers: getAuthHeaders() }
      );

      if (response.ok) {
        const data = await response.json();
        setTrendsData(data);
        setError(null);
      } else {
        throw new Error('Failed to fetch attack trends data');
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching attack trends:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrendsData();
  }, [timeRange, granularity]);

  useEffect(() => {
    const interval = setInterval(fetchTrendsData, 60000); // Refresh every minute
    
    // Set up WebSocket listener for real-time updates
    const socket = io('http://localhost:5000');
    
    // Debounce timer to batch multiple updates
    let refreshTimer = null;
    
    // Listen for new alerts and update trends immediately
    socket.on('new_alerts', (data) => {
      console.log('AttackTrends: Received new alerts:', data.alerts?.length);
      // Batch updates to avoid rapid refreshes
      if (data.alerts && data.alerts.length > 0) {
        if (refreshTimer) clearTimeout(refreshTimer);
        refreshTimer = setTimeout(() => {
          fetchTrendsData();
          refreshTimer = null;
        }, 2000); // Wait 2 seconds to batch updates
      }
    });
    
    // Listen for batch alerts from simulation
    socket.on('alert_batch_generated', (data) => {
      console.log('AttackTrends: Batch alerts generated:', data.count);
      // Immediate refresh for batch operations
      if (refreshTimer) clearTimeout(refreshTimer);
      fetchTrendsData();
    });
    
    return () => {
      clearInterval(interval);
      socket.disconnect();
      if (refreshTimer) clearTimeout(refreshTimer);
    };
  }, [timeRange, granularity]);

  const getTrendIcon = (direction) => {
    switch (direction) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-green-500" />;
      case 'stable':
        return <Minus className="h-4 w-4 text-yellow-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTrendColor = (direction) => {
    switch (direction) {
      case 'increasing':
        return 'text-red-600 bg-red-100';
      case 'decreasing':
        return 'text-green-600 bg-green-100';
      case 'stable':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-400 bg-slate-700/50';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (granularity === '30min' || granularity === 'hour') {
      return new Date(timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        month: 'short',
        day: 'numeric'
      });
    } else {
      return new Date(timestamp).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-2 text-gray-400">Loading attack trends...</span>
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

  if (!trendsData || trendsData.trends.length === 0) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Attack Trends</h3>
          <Clock className="h-5 w-5 text-gray-400" />
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <TrendingUp className="h-12 w-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-400">No trend data available</p>
            <p className="text-sm text-gray-400">Start monitoring to see attack trends</p>
          </div>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = trendsData.trends.map(item => ({
    ...item,
    formattedTime: formatTimestamp(item.timestamp)
  }));

  // Get unique attack types for line colors
  const attackTypes = [...new Set(trendsData.trends.flatMap(t => Object.keys(t.attack_types)))];
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899'];

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow p-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Attack Trends</h3>
          <p className="text-sm text-gray-400">
            {trendsData.summary.total_attacks} attacks over {trendsData.time_range}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1 text-sm text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
          >
            <option value={6}>6 Hours</option>
            <option value={12}>12 Hours</option>
            <option value={24}>24 Hours</option>
            <option value={48}>48 Hours</option>
            <option value={168}>7 Days</option>
          </select>
          
          {/* Granularity Selector */}
          <select
            value={granularity}
            onChange={(e) => setGranularity(e.target.value)}
            className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1 text-sm text-white focus:ring-2 focus:ring-blue-500 transition-all duration-200"
          >
            <option value="30min">30 Minutes</option>
            <option value="hour">Hourly</option>
            <option value="day">Daily</option>
          </select>
        </div>
      </div>

      {/* Trend Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{trendsData.summary.total_attacks}</div>
              <div className="text-sm text-gray-400">Total Attacks</div>
            </div>
            <Activity className="h-8 w-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-slate-900/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center">
                {getTrendIcon(trendsData.summary.trend_direction)}
                <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${getTrendColor(trendsData.summary.trend_direction)}`}>
                  {trendsData.summary.trend_direction}
                </span>
              </div>
              <div className="text-sm text-gray-400 mt-1">
                {Math.abs(trendsData.summary.trend_percentage)}% change
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{trendsData.summary.unique_attack_types}</div>
              <div className="text-sm text-gray-400">Attack Types</div>
            </div>
            <AlertTriangle className="h-8 w-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-slate-900/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-lg font-bold text-white">
                {trendsData.summary.peak_hour ? formatTimestamp(trendsData.summary.peak_hour) : 'N/A'}
              </div>
              <div className="text-sm text-gray-400">Peak Activity</div>
            </div>
            <Clock className="h-8 w-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Main Trends Chart */}
      <div className="mb-6">
        <h4 className="text-md font-semibold text-white mb-4">Attack Volume Over Time</h4>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis 
              dataKey="formattedTime" 
              fontSize={12}
              angle={-45}
              textAnchor="end"
              height={60}
              stroke="#cbd5e1"
              tick={{ fill: '#cbd5e1' }}
            />
            <YAxis 
              stroke="#cbd5e1"
              tick={{ fill: '#cbd5e1' }}
            />
            <Tooltip 
              labelFormatter={(label) => `Time: ${label}`}
              formatter={(value, name) => [value, name]}
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px', color: '#e2e8f0' }}
              labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
              cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
            />
            <Area 
              type="monotone" 
              dataKey="total_attacks" 
              stroke="#3b82f6" 
              fill="#3b82f6" 
              fillOpacity={0.3}
              name="Total Attacks"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Attack Type Breakdown */}
      {attackTypes.length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-semibold text-white mb-4">Attack Types Over Time</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis 
                dataKey="formattedTime" 
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={60}
                stroke="#cbd5e1"
                tick={{ fill: '#cbd5e1' }}
              />
              <YAxis 
                stroke="#cbd5e1"
                tick={{ fill: '#cbd5e1' }}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px', color: '#e2e8f0' }}
                labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
                cursor={{ stroke: 'rgba(59, 130, 246, 0.3)' }}
              />
              <Legend 
                wrapperStyle={{ color: '#e2e8f0' }}
                iconType="line"
              />
              {attackTypes.slice(0, 7).map((attackType, index) => (
                <Line
                  key={attackType}
                  type="monotone"
                  dataKey={`attack_types.${attackType}`}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  name={attackType}
                  connectNulls={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Recent Attacks */}
      {trendsData.summary.top_recent_attacks && trendsData.summary.top_recent_attacks.length > 0 && (
        <div>
          <h4 className="text-md font-semibold text-white mb-4">Most Active Attack Types</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {trendsData.summary.top_recent_attacks.map((attack, index) => (
              <div key={attack.type} className="border border-slate-600/50 rounded-lg p-3 bg-slate-900/30">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm truncate" title={attack.type}>
                    {attack.type}
                  </span>
                  <span className="text-lg font-bold text-blue-400">
                    {attack.count}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  Recent activity
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-1.5 mt-2">
                  <div 
                    className="bg-blue-500 h-1.5 rounded-full" 
                    style={{ 
                      width: `${(attack.count / Math.max(...trendsData.summary.top_recent_attacks.map(a => a.count))) * 100}%` 
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AttackTrends;
