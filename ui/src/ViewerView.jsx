// ViewerView.jsx - Viewer-specific dashboard using React.createElement
const ViewerView = () => {
  const [dashboardData, setDashboardData] = React.useState({
    totalAlerts: 0,
    criticalAlerts: 0,
    systemStatus: 'Operational',
    lastUpdate: new Date().toLocaleString()
  });
  const [recentAlerts, setRecentAlerts] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/alerts', {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        const alerts = data.alerts || [];
        setDashboardData({
          totalAlerts: alerts.length,
          criticalAlerts: alerts.filter(a => a.severity === 'critical').length,
          systemStatus: 'Operational',
          lastUpdate: new Date().toLocaleString()
        });
        setRecentAlerts(alerts.slice(0, 5));
      } else {
        setError('Failed to fetch dashboard data');
      }
    } catch (err) {
      setError('Error loading dashboard: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return React.createElement('div', {
      className: 'flex items-center justify-center h-64'
    }, React.createElement('div', {
      className: 'text-lg'
    }, 'Loading viewer dashboard...'));
  }

  if (error) {
    return React.createElement('div', {
      className: 'bg-red-50 border border-red-200 rounded-lg p-4'
    }, React.createElement('div', {
      className: 'text-red-800'
    }, 'Error: ' + error));
  }

  return React.createElement('div', {
    className: 'space-y-6'
  }, [
    React.createElement('div', {
      key: 'header',
      className: 'bg-white rounded-lg shadow-sm border p-6'
    }, React.createElement('div', {
      className: 'flex items-center space-x-3'
    }, [
      React.createElement('span', {
        key: 'icon',
        className: 'text-2xl'
      }, '👁️'),
      React.createElement('div', {
        key: 'text'
      }, [
        React.createElement('h1', {
          key: 'title',
          className: 'text-2xl font-bold text-gray-900'
        }, 'Viewer Dashboard'),
        React.createElement('p', {
          key: 'subtitle',
          className: 'text-gray-600'
        }, 'Read-only view of security status and alerts')
      ])
    ])),

    // Simple status cards for viewer
    React.createElement('div', {
      key: 'status',
      className: 'grid grid-cols-1 md:grid-cols-2 gap-4'
    }, [
      React.createElement('div', {
        key: 'alerts',
        className: 'bg-white rounded-lg shadow p-6'
      }, React.createElement('div', {
        className: 'text-center'
      }, [
        React.createElement('div', {
          key: 'icon',
          className: 'w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center mb-2 mx-auto'
        }, React.createElement('span', { className: 'text-white text-sm font-bold' }, '!')),
        React.createElement('p', {
          key: 'label',
          className: 'text-sm font-medium text-gray-600'
        }, 'Total Alerts'),
        React.createElement('p', {
          key: 'value',
          className: 'text-2xl font-bold text-blue-600'
        }, dashboardData.totalAlerts)
      ])),

      React.createElement('div', {
        key: 'critical',
        className: 'bg-white rounded-lg shadow p-6'
      }, React.createElement('div', {
        className: 'text-center'
      }, [
        React.createElement('div', {
          key: 'icon',
          className: 'w-8 h-8 bg-red-600 rounded-full flex items-center justify-center mb-2 mx-auto'
        }, React.createElement('span', { className: 'text-white text-sm font-bold' }, 'H')),
        React.createElement('p', {
          key: 'label',
          className: 'text-sm font-medium text-gray-600'
        }, 'Critical Alerts'),
        React.createElement('p', {
          key: 'value',
          className: 'text-2xl font-bold text-red-600'
        }, dashboardData.criticalAlerts)
      ]))
    ]),

    // Recent alerts
    React.createElement('div', {
      key: 'alerts',
      className: 'bg-white rounded-lg shadow'
    }, [
      React.createElement('div', {
        key: 'header',
        className: 'p-4 border-b'
      }, React.createElement('h3', {
        className: 'text-lg font-semibold'
      }, 'Recent Security Alerts')),
      React.createElement('div', {
        key: 'content',
        className: 'divide-y divide-gray-200'
      }, recentAlerts.length > 0 ? recentAlerts.map((alert, index) =>
        React.createElement('div', {
          key: index,
          className: 'p-4'
        }, React.createElement('div', {
          className: 'flex items-center justify-between'
        }, [
          React.createElement('div', {
            key: 'info',
            className: 'flex-1'
          }, [
            React.createElement('span', {
              key: 'severity',
              className: `px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`
            }, alert.severity?.toUpperCase() || 'UNKNOWN'),
            React.createElement('p', {
              key: 'desc',
              className: 'text-sm text-gray-600 mt-1'
            }, alert.description || 'Security event detected')
          ]),
          React.createElement('div', {
            key: 'readonly',
            className: 'text-xs text-gray-500'
          }, 'Read Only')
        ]))
      ) : [
        React.createElement('div', {
          key: 'empty',
          className: 'p-8 text-center text-gray-500'
        }, [
          React.createElement('div', {
            key: 'icon',
            className: 'w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mb-4 mx-auto'
          }, React.createElement('span', { className: 'text-white text-lg font-bold' }, '✓')),
          React.createElement('p', { key: 'msg' }, 'No recent alerts - System operating normally')
        ])
      ])
    ])
  ]);
};

// Export to global scope
window.ViewerView = ViewerView;
