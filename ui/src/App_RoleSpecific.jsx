const { useState, useEffect } = React;

// Import role-specific components
const SuperAdminView = window.SuperAdminView;
const AnalystView = window.AnalystView;
const ViewerView = window.ViewerView;

const SOCDashboard = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE = 'http://localhost:5000/api';
  const [token, setToken] = useState(localStorage.getItem('token'));

  // Check for existing session on load
  useEffect(() => {
    const validateSession = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const response = await fetch(`${API_BASE}/validate-token`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${storedToken}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            setToken(storedToken);
            setUser(data.user);
            setUserRole(data.role);
            setIsLoggedIn(true);
          } else {
            localStorage.removeItem('token');
            setToken(null);
          }
        } catch (error) {
          console.error('Session validation failed:', error);
          localStorage.removeItem('token');
          setToken(null);
        }
      }
    };

    // Add a small delay to ensure all components are loaded
    setTimeout(() => {
      validateSession();
    }, 100);
  }, []);

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
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        setUserRole(data.role);
        setIsLoggedIn(true);
        setUsername('');
        setPassword('');
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Invalid credentials');
      }
    } catch (err) {
      setError('Login failed. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setUserRole(null);
    setIsLoggedIn(false);
    setUsername('');
    setPassword('');
  };

  // Render role-specific dashboard
  const renderRoleSpecificDashboard = () => {
    console.log('Rendering dashboard for role:', userRole);
    console.log('Available components:', { SuperAdminView, AnalystView, ViewerView });
    console.log('Window components:', { 
      SuperAdminView: window.SuperAdminView, 
      AnalystView: window.AnalystView, 
      ViewerView: window.ViewerView 
    });
    
    if (!userRole) return React.createElement('div', { className: 'p-4' }, 'Loading user role...');

    // Simple fallback dashboard for testing
    const createFallbackDashboard = (roleName) => {
      return React.createElement('div', { className: 'p-6 bg-white rounded-lg shadow' }, 
        React.createElement('h2', { className: 'text-2xl font-bold mb-4' }, `${roleName} Dashboard`),
        React.createElement('p', { className: 'text-gray-600 mb-4' }, `Welcome, ${user}! You are logged in as ${roleName}.`),
        React.createElement('div', { className: 'grid grid-cols-1 md:grid-cols-3 gap-4' },
          React.createElement('div', { className: 'bg-blue-50 p-4 rounded' },
            React.createElement('h3', { className: 'font-semibold' }, 'System Status'),
            React.createElement('p', { className: 'text-sm text-gray-600' }, 'All systems operational')
          ),
          React.createElement('div', { className: 'bg-green-50 p-4 rounded' },
            React.createElement('h3', { className: 'font-semibold' }, 'Active Alerts'),
            React.createElement('p', { className: 'text-sm text-gray-600' }, '12 alerts pending')
          ),
          React.createElement('div', { className: 'bg-yellow-50 p-4 rounded' },
            React.createElement('h3', { className: 'font-semibold' }, 'Last Update'),
            React.createElement('p', { className: 'text-sm text-gray-600' }, new Date().toLocaleString())
          )
        ),
        React.createElement('button', { 
          className: 'mt-4 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded',
          onClick: handleLogout 
        }, 'Logout')
      );
    };

    switch (userRole) {
      case 'super_admin':
        if (window.SuperAdminView) {
          try {
            return React.createElement(window.SuperAdminView, { token, onLogout: handleLogout });
          } catch (error) {
            console.error('Error rendering SuperAdminView:', error);
            return createFallbackDashboard('Super Admin');
          }
        } else {
          return createFallbackDashboard('Super Admin');
        }
      
      case 'analyst':
        if (window.AnalystView) {
          try {
            return React.createElement(window.AnalystView, { token, onLogout: handleLogout });
          } catch (error) {
            console.error('Error rendering AnalystView:', error);
            return createFallbackDashboard('Analyst');
          }
        } else {
          return createFallbackDashboard('Analyst');
        }
      
      case 'viewer':
        if (window.ViewerView) {
          try {
            return React.createElement(window.ViewerView, { token, onLogout: handleLogout });
          } catch (error) {
            console.error('Error rendering ViewerView:', error);
            return createFallbackDashboard('Viewer');
          }
        } else {
          return createFallbackDashboard('Viewer');
        }
      
      default:
        return React.createElement('div', { className: 'p-4 text-red-600' }, `Unknown role: ${userRole}`);
    }
  };

  // Login Form
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
              <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">SOC Assistant</h2>
            <p className="mt-2 text-sm text-gray-600">Sign in to your security dashboard</p>
          </div>
          
          <form className="mt-8 space-y-6" onSubmit={handleLogin}>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            
            <div>
              <label htmlFor="username" className="sr-only">Username</label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Username"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="text-center text-sm text-gray-600">
            <div className="mt-4 p-4 bg-white rounded-lg shadow-sm">
              <p className="font-medium mb-2">Test Accounts:</p>
              <div className="space-y-1 text-xs">
                <div><strong>Super Admin:</strong> admin / SecurePass123!</div>
                <div><strong>Analyst:</strong> analyst / Analyst123!</div>
                <div><strong>Viewer:</strong> viewer / Viewer123!</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main Dashboard with role-specific content
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">SOC Assistant</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm">
                <span className="text-gray-600">Welcome, </span>
                <span className="font-medium text-gray-900">{user}</span>
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  {userRole?.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderRoleSpecificDashboard()}
      </main>
    </div>
  );
};

// Use React 18 createRoot API
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(SOCDashboard));
