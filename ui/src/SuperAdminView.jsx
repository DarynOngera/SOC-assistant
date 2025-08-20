// Super Admin Dashboard View
const { useState, useEffect } = React;

const SuperAdminView = ({ token, onLogout }) => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalAlerts: 0,
    systemHealth: 'Good',
    lastBackup: 'N/A'
  });
  const [showUserManager, setShowUserManager] = useState(false);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch admin stats:', error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [token]);

  return React.createElement('div', { className: 'space-y-6' },
    // Header
    React.createElement('div', { className: 'bg-red-50 border border-red-200 rounded-lg p-4' },
      React.createElement('div', { className: 'flex items-center space-x-2' },
        React.createElement('div', { className: 'h-6 w-6 bg-red-600 rounded flex items-center justify-center' },
          React.createElement('span', { className: 'text-white text-xs font-bold' }, '')
        ),
        React.createElement('h2', { className: 'text-xl font-bold text-red-800' }, 'Super Administrator Dashboard')
      ),
      React.createElement('p', { className: 'text-red-600 mt-1' }, 'Full system control and management')
    ),

    // Quick Stats
    React.createElement('div', { className: 'grid grid-cols-1 md:grid-cols-4 gap-4' },
      React.createElement('div', { className: 'bg-white rounded-lg shadow p-6' },
        React.createElement('div', { className: 'flex items-center justify-between' },
          React.createElement('div', null,
            React.createElement('p', { className: 'text-sm font-medium text-gray-600' }, 'Total Users'),
            React.createElement('p', { className: 'text-2xl font-bold text-gray-900' }, stats.totalUsers)
          ),
          React.createElement('div', { className: 'h-8 w-8 bg-blue-100 rounded flex items-center justify-center' },
            React.createElement('span', { className: 'text-blue-600 text-sm' }, '')
          )
        )
      ),

      React.createElement('div', { className: 'bg-white rounded-lg shadow p-6' },
        React.createElement('div', { className: 'flex items-center justify-between' },
          React.createElement('div', null,
            React.createElement('p', { className: 'text-sm font-medium text-gray-600' }, 'Total Alerts'),
            React.createElement('p', { className: 'text-2xl font-bold text-gray-900' }, stats.totalAlerts)
          ),
          React.createElement('div', { className: 'h-8 w-8 bg-orange-100 rounded flex items-center justify-center' },
            React.createElement('span', { className: 'text-orange-600 text-sm' }, '')
          )
        )
      ),

      React.createElement('div', { className: 'bg-white rounded-lg shadow p-6' },
        React.createElement('div', { className: 'flex items-center justify-between' },
          React.createElement('div', null,
            React.createElement('p', { className: 'text-sm font-medium text-gray-600' }, 'System Health'),
            React.createElement('p', { className: 'text-2xl font-bold text-green-600' }, stats.systemHealth)
          ),
          React.createElement('div', { className: 'h-8 w-8 bg-green-100 rounded flex items-center justify-center' },
            React.createElement('span', { className: 'text-green-600 text-sm' }, '')
          )
        )
      ),

      React.createElement('div', { className: 'bg-white rounded-lg shadow p-6' },
        React.createElement('div', { className: 'flex items-center justify-between' },
          React.createElement('div', null,
            React.createElement('p', { className: 'text-sm font-medium text-gray-600' }, 'Last Backup'),
            React.createElement('p', { className: 'text-sm font-bold text-gray-900' }, stats.lastBackup)
          ),
          React.createElement('div', { className: 'h-8 w-8 bg-purple-100 rounded flex items-center justify-center' },
            React.createElement('span', { className: 'text-purple-600 text-sm' }, '')
          )
        )
      )
    ),

    // Action Buttons
    React.createElement('div', { className: 'grid grid-cols-1 md:grid-cols-3 gap-4' },
      React.createElement('button', {
        onClick: () => setShowUserManager(!showUserManager),
        className: 'bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors'
      },
        React.createElement('span', { className: 'text-lg' }, ''),
        React.createElement('span', null, 'Manage Users')
      ),

      React.createElement('button', {
        className: 'bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors'
      },
        React.createElement('span', { className: 'text-lg' }, ''),
        React.createElement('span', null, 'System Settings')
      ),

      React.createElement('button', {
        className: 'bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors'
      },
        React.createElement('span', { className: 'text-lg' }, ''),
        React.createElement('span', null, 'Database Management')
      )
    ),

    // User Manager
    showUserManager && React.createElement('div', { className: 'bg-white rounded-lg shadow-lg' },
      React.createElement('div', { className: 'p-4 border-b' },
        React.createElement('h3', { className: 'text-lg font-semibold' }, 'User Management')
      ),
      React.createElement('div', { className: 'p-4' },
        React.createElement('div', { className: 'text-center py-8' },
          React.createElement('div', { className: 'text-6xl mb-4' }, ''),
          React.createElement('p', { className: 'text-gray-600' }, 'User management interface will be integrated here'),
          React.createElement('button', {
            onClick: () => setShowUserManager(false),
            className: 'mt-4 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded'
          }, 'Close')
        )
      )
    ),

    // System Logs Preview
    React.createElement('div', { className: 'bg-white rounded-lg shadow' },
      React.createElement('div', { className: 'p-4 border-b' },
        React.createElement('h3', { className: 'text-lg font-semibold' }, 'Recent System Activity')
      ),
      React.createElement('div', { className: 'p-4' },
        React.createElement('div', { className: 'space-y-2' },
          React.createElement('div', { className: 'flex items-center justify-between py-2 border-b' },
            React.createElement('span', { className: 'text-sm text-gray-600' }, 'User login: admin'),
            React.createElement('span', { className: 'text-xs text-gray-400' }, '2 minutes ago')
          ),
          React.createElement('div', { className: 'flex items-center justify-between py-2' },
            React.createElement('span', { className: 'text-sm text-gray-600' }, 'System backup completed'),
            React.createElement('span', { className: 'text-xs text-gray-400' }, '1 hour ago')
          ),
          React.createElement('div', { className: 'flex items-center justify-between py-2' },
            React.createElement('span', { className: 'text-sm text-gray-600' }, 'Database optimization'),
            React.createElement('span', { className: 'text-xs text-gray-400' }, '3 hours ago')
          )
        )
      )
    )
  );
};

// Export to global scope
window.SuperAdminView = SuperAdminView;
