const { useState, useEffect, useRef } = React;

const SOCDashboard = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ severity: '', status: '' });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Chart refs
  const threatTrendRef = useRef(null);
  const severityDistRef = useRef(null);
  const anomalyScoreRef = useRef(null);
  const threatTrendChart = useRef(null);
  const severityChart = useRef(null);
  const anomalyChart = useRef(null);

  const API_BASE = 'http://localhost:5000/api';
  const token = localStorage.getItem('token');

  // NLP Insights mock data (will be replaced with real API)
  const [nlpInsights, setNlpInsights] = useState([
    {
      id: 1,
      type: 'threat_intelligence',
      title: 'Emerging APT Campaign Detected',
      description: 'Pattern analysis indicates potential APT29 tactics involving PowerShell execution and lateral movement.',
      confidence: 0.87,
      severity: 'high',
      timestamp: new Date().toISOString()
    },
    {
      id: 2,
      type: 'behavioral_anomaly',
      title: 'Unusual Data Exfiltration Pattern',
      description: 'LSTM model detected abnormal data transfer volumes during off-hours from multiple endpoints.',
      confidence: 0.92,
      severity: 'critical',
      timestamp: new Date().toISOString()
    },
    {
      id: 3,
      type: 'vulnerability_correlation',
      title: 'CVE-2024-1234 Exploitation Attempt',
      description: 'Network traffic analysis suggests active exploitation of recently disclosed vulnerability.',
      confidence: 0.78,
      severity: 'medium',
      timestamp: new Date().toISOString()
    }
  ]);

  useEffect(() => {
    if (isLoggedIn) {
      fetchAlerts();
      fetchStats();
      const interval = setInterval(() => {
        fetchAlerts();
        fetchStats();
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [isLoggedIn, filters, currentPage, sortBy, sortOrder]);

  useEffect(() => {
    if (isLoggedIn && stats.total_alerts) {
      createCharts();
    }
    return () => {
      // Cleanup charts
      if (threatTrendChart.current) threatTrendChart.current.destroy();
      if (severityChart.current) severityChart.current.destroy();
      if (anomalyChart.current) anomalyChart.current.destroy();
    };
  }, [stats]);

  const createCharts = () => {
    // Threat Trend Chart
    if (threatTrendRef.current) {
      if (threatTrendChart.current) threatTrendChart.current.destroy();
      
      const ctx = threatTrendRef.current.getContext('2d');
      threatTrendChart.current = new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['6h ago', '5h ago', '4h ago', '3h ago', '2h ago', '1h ago', 'Now'],
          datasets: [{
            label: 'Threats Detected',
            data: [12, 19, 8, 15, 22, 18, 25],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.05)',
            tension: 0.4,
            fill: true,
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5
          }, {
            label: 'Anomalies',
            data: [5, 8, 3, 7, 12, 9, 15],
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.05)',
            tension: 0.4,
            fill: true,
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                usePointStyle: true,
                padding: 20,
                font: { size: 12 },
                color: '#4b5563'
              }
            },
            title: {
              display: true,
              text: 'Threat Detection Timeline',
              font: { size: 14, weight: '500' },
              color: '#374151'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: '#e5e7eb' },
              ticks: { color: '#6b7280', font: { size: 11 } }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#6b7280', font: { size: 11 } }
            }
          }
        }
      });
    }

    // Severity Distribution Chart
    if (severityDistRef.current) {
      if (severityChart.current) severityChart.current.destroy();
      
      const ctx = severityDistRef.current.getContext('2d');
      severityChart.current = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Critical', 'High', 'Medium', 'Low'],
          datasets: [{
            data: [
              stats.critical_alerts || 5,
              stats.high_alerts || 12,
              stats.medium_alerts || 8,
              stats.low_alerts || 15
            ],
            backgroundColor: ['#dc2626', '#f59e0b', '#facc15', '#4ade80'],
            borderWidth: 0,
            hoverBorderWidth: 4,
            hoverBorderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                usePointStyle: true,
                padding: 15,
                font: { size: 12 },
                color: '#4b5563'
              }
            },
            title: {
              display: true,
              text: 'Alert Severity Distribution',
              font: { size: 14, weight: '500' },
              color: '#374151'
            }
          }
        }
      });
    }

    // Anomaly Score Distribution
    if (anomalyScoreRef.current) {
      if (anomalyChart.current) anomalyChart.current.destroy();
      
      const ctx = anomalyScoreRef.current.getContext('2d');
      anomalyChart.current = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0'],
          datasets: [{
            label: 'Alert Count',
            data: [8, 15, 22, 18, 12],
            backgroundColor: ['#a7f3d0', '#a5f3fc', '#bfdbfe', '#ddd6fe', '#fecaca'],
            borderColor: ['#059669', '#0891b2', '#2563eb', '#7c3aed', '#dc2626'],
            borderWidth: 1,
            borderRadius: 4,
            hoverBackgroundColor: ['#6ee7b7', '#67e8f9', '#93c5fd', '#c4b5fd', '#fca5a5']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: {
              display: true,
              text: 'Anomaly Score Distribution',
              font: { size: 14, weight: '500' },
              color: '#374151'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: '#e5e7eb' },
              ticks: { color: '#6b7280', font: { size: 11 } }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#6b7280', font: { size: 11 } }
            }
          }
        }
      });
    }
  };

  const fetchAlerts = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: '10',
        offset: (currentPage - 1) * 10,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...filters
      });

      const response = await fetch(`${API_BASE}/alerts?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || data);
        setTotalPages(Math.ceil((data.total || data.length) / 10));
        setError('');
      }
    } catch (err) {
      setError('Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);
        setUser(data.user || username);
        setIsLoggedIn(true);
      } else {
        setError('Invalid credentials');
      }
    } catch (err) {
      setError('Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setUser('');
    setAlerts([]);
    setStats({});
  };

  const handleAlertAction = async (alertId, action) => {
    try {
      const response = await fetch(`${API_BASE}/alerts/${alertId}/action`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action })
      });

      if (response.ok) {
        fetchAlerts();
      }
    } catch (err) {
      console.error('Action failed:', err);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'bg-red-50 text-red-700 border-red-200';
      case 'high': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'medium': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'low': return 'bg-green-50 text-green-700 border-green-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getInsightIcon = (type) => {
    switch (type) {
      case 'threat_intelligence': return '🎯';
      case 'behavioral_anomaly': return '⚠️';
      case 'vulnerability_correlation': return '🔍';
      default: return '💡';
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white shadow-md rounded-xl p-8 w-full max-w-sm border border-gray-200">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-semibold text-gray-800 mb-2">SOC Assistant</h1>
            <p className="text-sm text-gray-500">Security Operations Center</p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field w-full px-4 py-3 text-gray-800 placeholder-gray-400 focus:outline-none"
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field w-full px-4 py-3 text-gray-800 placeholder-gray-400 focus:outline-none"
                required
              />
            </div>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 px-4 focus:outline-none disabled:opacity-50"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="header">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-800">SOC Dashboard</h1>
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-gray-500">Live</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-800 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Alerts</p>
                <p className="text-2xl font-semibold text-gray-800 mt-1">{stats.total_alerts || 0}</p>
              </div>
              <div className="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center">
                <span className="text-red-600 text-sm">🚨</span>
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Critical</p>
                <p className="text-2xl font-semibold text-red-600 mt-1">{stats.critical_alerts || 0}</p>
              </div>
              <div className="w-8 h-8 bg-orange-50 rounded-lg flex items-center justify-center">
                <span className="text-orange-600 text-sm">⚡</span>
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Avg Score</p>
                <p className="text-2xl font-semibold text-blue-600 mt-1">{(stats.avg_anomaly_score || 0).toFixed(2)}</p>
              </div>
              <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 text-sm">📊</span>
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Processed</p>
                <p className="text-2xl font-semibold text-green-600 mt-1">{stats.processed_sequences || 0}</p>
              </div>
              <div className="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center">
                <span className="text-green-600 text-sm">🔍</span>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="card p-6">
            <div className="chart-container">
              <canvas ref={threatTrendRef}></canvas>
            </div>
          </div>
          
          <div className="card p-6">
            <div className="chart-container">
              <canvas ref={severityDistRef}></canvas>
            </div>
          </div>
          
          <div className="card p-6">
            <div className="chart-container">
              <canvas ref={anomalyScoreRef}></canvas>
            </div>
          </div>
        </div>

        {/* NLP Insights Section */}
        <div className="card mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-800 flex items-center">
              <span className="text-lg mr-2">🧠</span>
              AI Security Insights
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {nlpInsights.map((insight) => (
                <div key={insight.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">{getInsightIcon(insight.type)}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(insight.severity)}`}>
                        {insight.severity.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {(insight.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                  <h3 className="font-medium text-gray-800 mb-2 text-sm">{insight.title}</h3>
                  <p className="text-xs text-gray-600 mb-3 leading-relaxed">{insight.description}</p>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">
                      {new Date(insight.timestamp).toLocaleTimeString()}
                    </span>
                    <button className="text-blue-600 hover:text-blue-700 text-xs font-medium transition-colors">
                      Investigate →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-800">Security Alerts</h2>
              <div className="flex space-x-3">
                <select
                  value={filters.severity}
                  onChange={(e) => setFilters({...filters, severity: e.target.value})}
                  className="input-field bg-white px-3 py-1 text-sm focus:outline-none"
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="input-field bg-white px-3 py-1 text-sm focus:outline-none"
                >
                  <option value="timestamp">Time</option>
                  <option value="severity">Severity</option>
                  <option value="anomaly_score">Anomaly Score</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alert</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Anomaly Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-8 text-center text-gray-500 text-sm">Loading alerts...</td>
                  </tr>
                ) : alerts.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-8 text-center text-gray-500 text-sm">No alerts found</td>
                  </tr>
                ) : (
                  alerts.map((alert) => (
                    <tr key={alert.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-800">{alert.alert}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <div className="text-sm text-gray-800">{alert.anomaly_score?.toFixed(2)}</div>
                          <div className="w-16 bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-500 h-1.5 rounded-full transition-all" 
                              style={{width: `${(alert.anomaly_score || 0) * 100}%`}}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{alert.user}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(alert.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex space-x-3">
                          <button
                            onClick={() => handleAlertAction(alert.id, 'flag')}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                          >
                            Flag
                          </button>
                          <button
                            onClick={() => handleAlertAction(alert.id, 'dismiss')}
                            className="text-gray-500 hover:text-gray-700 text-sm font-medium transition-colors"
                          >
                            Dismiss
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-3 border-t border-gray-200 flex justify-between items-center">
              <div className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 hover:bg-gray-100 transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 hover:bg-gray-100 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

ReactDOM.render(<SOCDashboard />, document.getElementById('root'));