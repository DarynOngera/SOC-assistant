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
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.4,
            fill: true
          }, {
            label: 'Anomalies',
            data: [5, 8, 3, 7, 12, 9, 15],
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
            },
            title: {
              display: true,
              text: 'Threat Detection Timeline'
            }
          },
          scales: {
            y: {
              beginAtZero: true
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
            backgroundColor: [
              '#dc2626',
              '#ea580c',
              '#d97706',
              '#65a30d'
            ],
            borderWidth: 2,
            borderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
            },
            title: {
              display: true,
              text: 'Alert Severity Distribution'
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
            backgroundColor: [
              '#10b981',
              '#06b6d4',
              '#3b82f6',
              '#8b5cf6',
              '#ef4444'
            ],
            borderColor: '#ffffff',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            title: {
              display: true,
              text: 'Anomaly Score Distribution'
            }
          },
          scales: {
            y: {
              beginAtZero: true
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
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
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
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="glass-effect rounded-2xl p-8 w-full max-w-md shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">SOC Assistant</h1>
            <p className="text-blue-100">Intelligent Security Operations Center</p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-300"
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-300"
                required
              />
            </div>
            
            {error && (
              <div className="bg-red-500/20 border border-red-300 text-red-100 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-white/20 hover:bg-white/30 text-white font-semibold py-3 px-4 rounded-lg transition duration-300 disabled:opacity-50"
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
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">SOC Dashboard</h1>
              <div className="ml-4 flex items-center">
                <div className="w-3 h-3 bg-green-400 rounded-full threat-pulse mr-2"></div>
                <span className="text-sm text-gray-600">Live Monitoring</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Welcome, {user}</span>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-300"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <span className="text-2xl">🚨</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Alerts</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_alerts || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <span className="text-2xl">⚡</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Critical</p>
                <p className="text-2xl font-bold text-red-600">{stats.critical_alerts || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-2xl">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Anomaly Score</p>
                <p className="text-2xl font-bold text-blue-600">{(stats.avg_anomaly_score || 0).toFixed(2)}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-2xl">🔍</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Processed</p>
                <p className="text-2xl font-bold text-green-600">{stats.processed_sequences || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="chart-container">
              <canvas ref={threatTrendRef}></canvas>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="chart-container">
              <canvas ref={severityDistRef}></canvas>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="chart-container">
              <canvas ref={anomalyScoreRef}></canvas>
            </div>
          </div>
        </div>

        {/* NLP Insights Section */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="text-2xl mr-2">🧠</span>
              AI-Powered Security Insights
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {nlpInsights.map((insight) => (
                <div key={insight.id} className="insight-card rounded-lg p-4 shadow-sm">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center">
                      <span className="text-xl mr-2">{getInsightIcon(insight.type)}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(insight.severity)}`}>
                        {insight.severity.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {(insight.confidence * 100).toFixed(0)}% confidence
                    </div>
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{insight.title}</h3>
                  <p className="text-sm text-gray-600 mb-3">{insight.description}</p>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">
                      {new Date(insight.timestamp).toLocaleTimeString()}
                    </span>
                    <button className="text-blue-600 hover:text-blue-800 text-xs font-medium">
                      Investigate →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">Security Alerts</h2>
              <div className="flex space-x-4">
                <select
                  value={filters.severity}
                  onChange={(e) => setFilters({...filters, severity: e.target.value})}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm"
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
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm"
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
                    <td colSpan="6" className="px-6 py-4 text-center text-gray-500">Loading alerts...</td>
                  </tr>
                ) : alerts.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 text-center text-gray-500">No alerts found</td>
                  </tr>
                ) : (
                  alerts.map((alert) => (
                    <tr key={alert.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{alert.alert}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="text-sm text-gray-900">{alert.anomaly_score?.toFixed(2)}</div>
                          <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-red-500 h-2 rounded-full" 
                              style={{width: `${(alert.anomaly_score || 0) * 100}%`}}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{alert.user}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(alert.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleAlertAction(alert.id, 'flag')}
                          className="text-red-600 hover:text-red-900 mr-3"
                        >
                          Flag
                        </button>
                        <button
                          onClick={() => handleAlertAction(alert.id, 'dismiss')}
                          className="text-green-600 hover:text-green-900"
                        >
                          Dismiss
                        </button>
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
              <div className="text-sm text-gray-700">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
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