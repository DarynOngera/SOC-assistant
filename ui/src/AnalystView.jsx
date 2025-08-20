// AnalystView.jsx - Analyst-specific dashboard using React.createElement
const AnalystView = () => {
  const [alerts, setAlerts] = React.useState([]);
  const [filteredAlerts, setFilteredAlerts] = React.useState([]);
  const [filterSeverity, setFilterSeverity] = React.useState('all');
  const [filterStatus, setFilterStatus] = React.useState('all');
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [selectedAlert, setSelectedAlert] = React.useState(null);

  React.useEffect(() => {
    fetchAlerts();
  }, []);

  React.useEffect(() => {
    applyFilters();
  }, [alerts, filterSeverity, filterStatus]);

  const fetchAlerts = async () => {
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
        setAlerts(data.alerts || []);
      } else {
        setError('Failed to fetch alerts');
      }
    } catch (err) {
      setError('Error loading alerts: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = alerts;
    
    if (filterSeverity !== 'all') {
      filtered = filtered.filter(alert => alert.severity === filterSeverity);
    }
    
    if (filterStatus !== 'all') {
      filtered = filtered.filter(alert => alert.status === filterStatus);
    }
    
    setFilteredAlerts(filtered);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'text-red-600 bg-red-50';
      case 'investigating': return 'text-yellow-600 bg-yellow-50';
      case 'resolved': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return React.createElement('div', {
      className: 'flex items-center justify-center h-64'
    }, React.createElement('div', {
      className: 'text-lg'
    }, 'Loading analyst dashboard...'));
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
    // Header
    React.createElement('div', {
      key: 'header',
      className: 'bg-white rounded-lg shadow-sm border p-6'
    }, React.createElement('div', {
      className: 'flex items-center space-x-3'
    }, [
      React.createElement('span', {
        key: 'icon',
        className: 'text-2xl'
      }, '🔍'),
      React.createElement('div', {
        key: 'text'
      }, [
        React.createElement('h1', {
          key: 'title',
          className: 'text-2xl font-bold text-gray-900'
        }, 'Analyst Dashboard'),
        React.createElement('p', {
          key: 'subtitle',
          className: 'text-gray-600'
        }, 'Security analysis and alert management')
      ])
    ])),

    // Quick Stats
    React.createElement('div', {
      key: 'stats',
      className: 'grid grid-cols-1 md:grid-cols-4 gap-6'
    }, [
      React.createElement('div', {
        key: 'critical',
        className: 'bg-white rounded-lg shadow-sm border p-6'
      }, React.createElement('div', {
        className: 'flex items-center'
      }, [
        React.createElement('span', {
          key: 'icon',
          className: 'text-2xl mr-4'
        }, React.createElement('div', { className: 'w-6 h-6 bg-yellow-600 rounded-full flex items-center justify-center' }, React.createElement('span', { className: 'text-white text-xs font-bold' }, '!'))),
        React.createElement('div', {
          key: 'content'
        }, [
          React.createElement('p', {
            key: 'label',
            className: 'text-sm font-medium text-gray-600'
          }, 'Critical Alerts'),
          React.createElement('p', {
            key: 'value',
            className: 'text-2xl font-bold text-gray-900'
          }, alerts.filter(a => a.severity === 'critical').length)
        ])
      ])),

      React.createElement('div', {
        key: 'investigating',
        className: 'bg-white rounded-lg shadow-sm border p-6'
      }, React.createElement('div', {
        className: 'flex items-center'
      }, [
        React.createElement('span', {
          key: 'icon',
          className: 'text-2xl mr-4'
        }, React.createElement('div', { className: 'w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center' }, React.createElement('span', { className: 'text-white text-xs font-bold' }, 'A'))),
        React.createElement('div', {
          key: 'content'
        }, [
          React.createElement('p', {
            key: 'label',
            className: 'text-sm font-medium text-gray-600'
          }, 'Active Investigations'),
          React.createElement('p', {
            key: 'value',
            className: 'text-2xl font-bold text-gray-900'
          }, alerts.filter(a => a.status === 'investigating').length)
        ])
      ])),

      React.createElement('div', {
        key: 'pending',
        className: 'bg-white rounded-lg shadow-sm border p-6'
      }, React.createElement('div', {
        className: 'flex items-center'
      }, [
        React.createElement('div', {
          key: 'icon',
          className: 'w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center'
        }, React.createElement('span', { className: 'text-white text-xs font-bold' }, 'S')),
        React.createElement('div', {
          key: 'content'
        }, [
          React.createElement('p', {
            key: 'label',
            className: 'text-sm font-medium text-gray-600'
          }, 'Pending Review'),
          React.createElement('p', {
            key: 'value',
            className: 'text-2xl font-bold text-gray-900'
          }, alerts.filter(a => a.status === 'open').length)
        ])
      ])),

      React.createElement('div', {
        key: 'resolved',
        className: 'bg-white rounded-lg shadow-sm border p-6'
      }, React.createElement('div', {
        className: 'flex items-center'
      }, [
        React.createElement('span', {
          key: 'icon',
          className: 'text-2xl mr-4'
        }, React.createElement('div', { className: 'w-6 h-6 bg-green-600 rounded-full flex items-center justify-center' }, React.createElement('span', { className: 'text-white text-xs font-bold' }, '✓'))),
        React.createElement('div', {
          key: 'content'
        }, [
          React.createElement('p', {
            key: 'label',
            className: 'text-sm font-medium text-gray-600'
          }, 'Resolved Today'),
          React.createElement('p', {
            key: 'value',
            className: 'text-2xl font-bold text-gray-900'
          }, alerts.filter(a => a.status === 'resolved').length)
        ])
      ]))
    ]),

    // Chart.js Data Visualization Charts
    React.createElement('div', {
      key: 'charts',
      className: 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6'
    }, [
      // Doughnut Chart - Alert Severity Distribution
      React.createElement('div', {
        key: 'severity-doughnut',
        className: 'bg-white rounded-lg shadow-sm border p-6'
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-lg font-semibold mb-4 flex items-center'
        }, [
          React.createElement('span', { key: 'icon', className: 'text-xl mr-2' }, '🍩'),
          React.createElement('span', { key: 'text' }, 'Alert Severity Distribution')
        ]),
        React.createElement('div', {
          key: 'chart-container',
          className: 'chart-container'
        }, [
          React.createElement('canvas', {
            key: 'doughnut-canvas',
            id: 'severityChart',
            ref: (canvas) => {
              if (canvas && window.Chart) {
                // Destroy existing chart if it exists
                if (window.severityChartInstance) {
                  window.severityChartInstance.destroy();
                }
                
                const ctx = canvas.getContext('2d');
                const severityData = [
                  alerts.filter(a => a.severity === 'critical').length,
                  alerts.filter(a => a.severity === 'high').length,
                  alerts.filter(a => a.severity === 'medium').length,
                  alerts.filter(a => a.severity === 'low').length
                ];
                
                window.severityChartInstance = new Chart(ctx, {
                  type: 'doughnut',
                  data: {
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                      data: severityData,
                      backgroundColor: [
                        '#dc2626', // Critical - Red
                        '#ea580c', // High - Orange
                        '#ca8a04', // Medium - Yellow
                        '#2563eb'  // Low - Blue
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
                        labels: {
                          padding: 20,
                          usePointStyle: true
                        }
                      },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                          }
                        }
                      }
                    }
                  }
                });
              }
            }
          })
        ])
      ]),

      // Line Chart - Threat Activity Over Time
      React.createElement('div', {
        key: 'timeline-line',
        className: 'bg-white rounded-lg shadow-sm border p-6'
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-lg font-semibold mb-4 flex items-center'
        }, [
          React.createElement('div', { key: 'icon', className: 'w-5 h-5 bg-green-600 rounded mr-2' }),
          React.createElement('span', { key: 'text' }, 'Threat Activity Timeline')
        ]),
        React.createElement('div', {
          key: 'chart-container',
          className: 'chart-container'
        }, [
          React.createElement('canvas', {
            key: 'line-canvas',
            id: 'timelineChart',
            ref: (canvas) => {
              if (canvas && window.Chart) {
                // Destroy existing chart if it exists
                if (window.timelineChartInstance) {
                  window.timelineChartInstance.destroy();
                }
                
                const ctx = canvas.getContext('2d');
                const timeData = [
                  { time: '00:00', threats: 5 },
                  { time: '04:00', threats: 8 },
                  { time: '08:00', threats: 12 },
                  { time: '12:00', threats: 15 },
                  { time: '16:00', threats: 18 },
                  { time: '20:00', threats: 10 },
                  { time: '24:00', threats: 7 }
                ];
                
                window.timelineChartInstance = new Chart(ctx, {
                  type: 'line',
                  data: {
                    labels: timeData.map(d => d.time),
                    datasets: [{
                      label: 'Threat Count',
                      data: timeData.map(d => d.threats),
                      borderColor: '#3b82f6',
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      borderWidth: 3,
                      fill: true,
                      tension: 0.4,
                      pointBackgroundColor: '#3b82f6',
                      pointBorderColor: '#ffffff',
                      pointBorderWidth: 2,
                      pointRadius: 6
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        grid: {
                          color: '#e5e7eb'
                        },
                        ticks: {
                          color: '#6b7280'
                        }
                      },
                      x: {
                        grid: {
                          color: '#e5e7eb'
                        },
                        ticks: {
                          color: '#6b7280'
                        }
                      }
                    }
                  }
                });
              }
            }
          })
        ])
      ]),

      // Bar Chart - Attack Types
      React.createElement('div', {
        key: 'attack-types-bar',
        className: 'bg-white rounded-lg shadow-sm border p-6'
      }, [
        React.createElement('h3', {
          key: 'title',
          className: 'text-lg font-semibold mb-4 flex items-center'
        }, [
          React.createElement('div', { key: 'icon', className: 'w-5 h-5 bg-blue-600 rounded mr-2' }),
          React.createElement('span', { key: 'text' }, 'Attack Types Distribution')
        ]),
        React.createElement('div', {
          key: 'chart-container',
          className: 'chart-container'
        }, [
          React.createElement('canvas', {
            key: 'bar-canvas',
            id: 'attackTypesChart',
            ref: (canvas) => {
              if (canvas && window.Chart) {
                // Destroy existing chart if it exists
                if (window.attackTypesChartInstance) {
                  window.attackTypesChartInstance.destroy();
                }
                
                const ctx = canvas.getContext('2d');
                const attackData = [
                  { type: 'Malware', count: alerts.filter(a => a.type?.includes('malware')).length || 15 },
                  { type: 'Phishing', count: alerts.filter(a => a.type?.includes('phishing')).length || 12 },
                  { type: 'DDoS', count: alerts.filter(a => a.type?.includes('ddos')).length || 8 },
                  { type: 'Intrusion', count: alerts.filter(a => a.type?.includes('intrusion')).length || 6 },
                  { type: 'Data Breach', count: alerts.filter(a => a.type?.includes('breach')).length || 4 }
                ];
                
                window.attackTypesChartInstance = new Chart(ctx, {
                  type: 'bar',
                  data: {
                    labels: attackData.map(d => d.type),
                    datasets: [{
                      label: 'Attack Count',
                      data: attackData.map(d => d.count),
                      backgroundColor: [
                        '#ef4444', // Red
                        '#f97316', // Orange
                        '#eab308', // Yellow
                        '#3b82f6', // Blue
                        '#8b5cf6'  // Purple
                      ],
                      borderColor: [
                        '#dc2626',
                        '#ea580c',
                        '#ca8a04',
                        '#2563eb',
                        '#7c3aed'
                      ],
                      borderWidth: 2,
                      borderRadius: 4
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        grid: {
                          color: '#e5e7eb'
                        },
                        ticks: {
                          color: '#6b7280'
                        }
                      },
                      x: {
                        grid: {
                          display: false
                        },
                        ticks: {
                          color: '#6b7280',
                          maxRotation: 45
                        }
                      }
                    }
                  }
                });
              }
            }
          })
        ])
      ])
    ]),

    // Threat Action Tools
    React.createElement('div', {
      key: 'threat-actions',
      className: 'bg-white rounded-lg shadow-sm border p-6'
    }, [
      React.createElement('h3', {
        key: 'title',
        className: 'text-lg font-semibold mb-4 flex items-center'
      }, [
        React.createElement('span', { key: 'icon', className: 'text-xl mr-2' }, '⚔️'),
        React.createElement('span', { key: 'text' }, 'Threat Response Actions')
      ]),
      React.createElement('div', {
        key: 'actions',
        className: 'grid grid-cols-2 md:grid-cols-4 gap-4'
      }, [
        React.createElement('button', {
          key: 'block-ip',
          className: 'bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-lg flex flex-col items-center space-y-2 transition-colors',
          onClick: () => alert('IP Blocking initiated - Feature coming in Sprint 3')
        }, [
          React.createElement('div', { key: 'icon', className: 'w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center' }, React.createElement('span', { className: 'text-white text-sm font-bold' }, 'B')),
          React.createElement('span', { key: 'text', className: 'text-sm' }, 'Block IP')
        ]),

        React.createElement('button', {
          key: 'quarantine',
          className: 'bg-orange-600 hover:bg-orange-700 text-white font-medium py-3 px-4 rounded-lg flex flex-col items-center space-y-2 transition-colors',
          onClick: () => alert('Quarantine initiated - Feature coming in Sprint 3')
        }, [
          React.createElement('div', { key: 'icon', className: 'w-8 h-8 bg-orange-600 rounded-lg flex items-center justify-center' }, React.createElement('span', { className: 'text-white text-sm font-bold' }, 'Q')),
          React.createElement('span', { key: 'text', className: 'text-sm' }, 'Quarantine')
        ]),

        React.createElement('button', {
          key: 'investigate',
          className: 'bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg flex flex-col items-center space-y-2 transition-colors',
          onClick: () => alert('Deep investigation started - Feature coming in Sprint 4')
        }, [
          React.createElement('div', { key: 'icon', className: 'w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center' }, React.createElement('span', { className: 'text-white text-sm font-bold' }, 'I')),
          React.createElement('span', { key: 'text', className: 'text-sm' }, 'Investigate')
        ]),

        React.createElement('button', {
          key: 'escalate',
          className: 'bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-lg flex flex-col items-center space-y-2 transition-colors',
          onClick: () => alert('Escalation to SOC Manager initiated')
        }, [
          React.createElement('div', { key: 'icon', className: 'w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center' }, React.createElement('span', { className: 'text-white text-sm font-bold' }, 'E')),
          React.createElement('span', { key: 'text', className: 'text-sm' }, 'Escalate')
        ])
      ])
    ]),

    // AI-Powered Threat Intelligence
    React.createElement('div', {
      key: 'ai-intelligence',
      className: 'bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow-sm border p-6'
    }, [
      React.createElement('h3', {
        key: 'title',
        className: 'text-lg font-semibold mb-4 flex items-center'
      }, [
        React.createElement('div', { key: 'icon', className: 'w-5 h-5 bg-purple-600 rounded mr-2' }),
        React.createElement('span', { key: 'text' }, 'AI Threat Intelligence')
      ]),
      React.createElement('div', {
        key: 'insights',
        className: 'grid grid-cols-1 md:grid-cols-3 gap-4'
      }, [
        React.createElement('div', {
          key: 'risk-score',
          className: 'bg-white rounded-lg p-4 text-center'
        }, [
          React.createElement('div', { key: 'score', className: 'text-3xl font-bold text-red-600' }, '8.7'),
          React.createElement('div', { key: 'label', className: 'text-sm text-gray-600' }, 'Risk Score'),
          React.createElement('div', { key: 'trend', className: 'text-xs text-red-500 mt-1' }, '↑ +0.3 from yesterday')
        ]),
        React.createElement('div', {
          key: 'threat-types',
          className: 'bg-white rounded-lg p-4 text-center'
        }, [
          React.createElement('div', { key: 'count', className: 'text-3xl font-bold text-orange-600' }, '5'),
          React.createElement('div', { key: 'label', className: 'text-sm text-gray-600' }, 'Active Threat Types'),
          React.createElement('div', { key: 'types', className: 'text-xs text-gray-500 mt-1' }, 'Malware, Phishing, DDoS')
        ]),
        React.createElement('div', {
          key: 'predictions',
          className: 'bg-white rounded-lg p-4 text-center'
        }, [
          React.createElement('div', { key: 'percent', className: 'text-3xl font-bold text-blue-600' }, '23%'),
          React.createElement('div', { key: 'label', className: 'text-sm text-gray-600' }, 'Attack Likelihood'),
          React.createElement('div', { key: 'time', className: 'text-xs text-blue-500 mt-1' }, 'Next 4 hours')
        ])
      ])
    ]),

    // Filters
    React.createElement('div', {
      key: 'filters',
      className: 'bg-white rounded-lg shadow-sm border p-6'
    }, React.createElement('div', {
      className: 'flex items-center space-x-4'
    }, [
      React.createElement('span', {
        key: 'icon',
        className: 'text-xl'
      }, '🔽'),
      React.createElement('div', {
        key: 'controls',
        className: 'flex space-x-4'
      }, [
        React.createElement('div', {
          key: 'severity'
        }, [
          React.createElement('label', {
            key: 'label',
            className: 'block text-sm font-medium text-gray-700 mb-1'
          }, 'Severity'),
          React.createElement('select', {
            key: 'select',
            value: filterSeverity,
            onChange: (e) => setFilterSeverity(e.target.value),
            className: 'border border-gray-300 rounded-md px-3 py-2 text-sm'
          }, [
            React.createElement('option', { key: 'all', value: 'all' }, 'All Severities'),
            React.createElement('option', { key: 'critical', value: 'critical' }, 'Critical'),
            React.createElement('option', { key: 'high', value: 'high' }, 'High'),
            React.createElement('option', { key: 'medium', value: 'medium' }, 'Medium'),
            React.createElement('option', { key: 'low', value: 'low' }, 'Low')
          ])
        ]),
        React.createElement('div', {
          key: 'status'
        }, [
          React.createElement('label', {
            key: 'label',
            className: 'block text-sm font-medium text-gray-700 mb-1'
          }, 'Status'),
          React.createElement('select', {
            key: 'select',
            value: filterStatus,
            onChange: (e) => setFilterStatus(e.target.value),
            className: 'border border-gray-300 rounded-md px-3 py-2 text-sm'
          }, [
            React.createElement('option', { key: 'all', value: 'all' }, 'All Statuses'),
            React.createElement('option', { key: 'open', value: 'open' }, 'Open'),
            React.createElement('option', { key: 'investigating', value: 'investigating' }, 'Investigating'),
            React.createElement('option', { key: 'resolved', value: 'resolved' }, 'Resolved')
          ])
        ])
      ])
    ])),

    // Alerts Table
    React.createElement('div', {
      key: 'alerts',
      className: 'bg-white rounded-lg shadow-sm border'
    }, [
      React.createElement('div', {
        key: 'header',
        className: 'px-6 py-4 border-b border-gray-200'
      }, React.createElement('h2', {
        className: 'text-lg font-semibold text-gray-900'
      }, 'Security Alerts')),
      React.createElement('div', {
        key: 'table-container',
        className: 'overflow-x-auto'
      }, React.createElement('table', {
        className: 'min-w-full divide-y divide-gray-200'
      }, [
        React.createElement('thead', {
          key: 'thead',
          className: 'bg-gray-50'
        }, React.createElement('tr', {}, [
          React.createElement('th', {
            key: 'alert',
            className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'
          }, 'Alert'),
          React.createElement('th', {
            key: 'severity',
            className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'
          }, 'Severity'),
          React.createElement('th', {
            key: 'status',
            className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'
          }, 'Status'),
          React.createElement('th', {
            key: 'time',
            className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'
          }, 'Time'),
          React.createElement('th', {
            key: 'actions',
            className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'
          }, 'Actions')
        ])),
        React.createElement('tbody', {
          key: 'tbody',
          className: 'bg-white divide-y divide-gray-200'
        }, filteredAlerts.map((alert, index) => 
          React.createElement('tr', {
            key: index,
            className: 'hover:bg-gray-50'
          }, [
            React.createElement('td', {
              key: 'alert',
              className: 'px-6 py-4 whitespace-nowrap'
            }, [
              React.createElement('div', {
                key: 'type',
                className: 'text-sm font-medium text-gray-900'
              }, alert.type),
              React.createElement('div', {
                key: 'desc',
                className: 'text-sm text-gray-500'
              }, alert.description)
            ]),
            React.createElement('td', {
              key: 'severity',
              className: 'px-6 py-4 whitespace-nowrap'
            }, React.createElement('span', {
              className: `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`
            }, alert.severity)),
            React.createElement('td', {
              key: 'status',
              className: 'px-6 py-4 whitespace-nowrap'
            }, React.createElement('span', {
              className: `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`
            }, alert.status)),
            React.createElement('td', {
              key: 'time',
              className: 'px-6 py-4 whitespace-nowrap text-sm text-gray-500'
            }, new Date(alert.timestamp).toLocaleString()),
            React.createElement('td', {
              key: 'actions',
              className: 'px-6 py-4 whitespace-nowrap text-sm font-medium'
            }, [
              React.createElement('button', {
                key: 'view',
                className: 'text-blue-600 hover:text-blue-900 mr-3'
              }, React.createElement('div', { className: 'w-4 h-4 bg-blue-600 rounded-full' })),
              React.createElement('button', {
                key: 'resolve',
                className: 'text-green-600 hover:text-green-900'
              }, React.createElement('div', { className: 'w-4 h-4 bg-green-600 rounded-full' }))
            ])
          ])
        ))
      ]))
    ])
  ]);
};

// Export to global scope
window.AnalystView = AnalystView;
