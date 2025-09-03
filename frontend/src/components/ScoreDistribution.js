import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';

const ScoreDistribution = () => {
  const [distributionData, setDistributionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartType, setChartType] = useState('bar');

  useEffect(() => {
    fetchDistributionData();
    const interval = setInterval(fetchDistributionData, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDistributionData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/score-distribution');
      if (response.ok) {
        const data = await response.json();
        
        // Transform data for chart
        const chartData = data.bins.map((bin, index) => ({
          score: bin.toFixed(2),
          count: data.counts[index],
          range: `${(bin - 0.025).toFixed(2)}-${(bin + 0.025).toFixed(2)}`
        }));
        
        setDistributionData(chartData);
      }
    } catch (error) {
      console.error('Error fetching distribution data:', error);
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">Score Range: {data.range}</p>
          <p className="text-primary-600">Count: {data.count}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Score Distribution</h3>
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
          <BarChart3 className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Score Distribution</h3>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setChartType('bar')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              chartType === 'bar' 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Bar
          </button>
          <button
            onClick={() => setChartType('line')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              chartType === 'line' 
                ? 'bg-primary-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Line
          </button>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={distributionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="score" 
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="count" 
                fill="#3b82f6"
                radius={[2, 2, 0, 0]}
              />
            </BarChart>
          ) : (
            <LineChart data={distributionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="score" 
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
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

      {/* Distribution Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-2xl font-bold text-success-600">
            {distributionData.filter(d => parseFloat(d.score) < 0.3).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-500">Low Risk (0.0-0.3)</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {distributionData.filter(d => parseFloat(d.score) >= 0.3 && parseFloat(d.score) < 0.6).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-500">Medium Risk (0.3-0.6)</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-warning-600">
            {distributionData.filter(d => parseFloat(d.score) >= 0.6 && parseFloat(d.score) < 0.8).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-500">High Risk (0.6-0.8)</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-danger-600">
            {distributionData.filter(d => parseFloat(d.score) >= 0.8).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-xs text-gray-500">Critical (0.8+)</div>
        </div>
      </div>
    </div>
  );
};

export default ScoreDistribution;
