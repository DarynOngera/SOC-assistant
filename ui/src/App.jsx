const App = () => {
    const [loggedIn, setLoggedIn] = React.useState(false);
    const [username, setUsername] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [token, setToken] = React.useState('');
    const [alerts, setAlerts] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState('');
    const [sortField, setSortField] = React.useState('anomaly_score');
    const [sortDirection, setSortDirection] = React.useState('desc');

    const API_BASE = 'http://localhost:5000/api';

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                setToken(data.token);
                setLoggedIn(true);
                localStorage.setItem('token', data.token);
                await fetchAlerts(data.token);
            } else {
                setError(data.message || 'Login failed');
            }
        } catch (err) {
            setError('Network error. Please check if the server is running.');
        } finally {
            setLoading(false);
        }
    };

    const fetchAlerts = async (authToken = token) => {
        try {
            const response = await fetch(`${API_BASE}/alerts`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });
            
            if (response.ok) {
                const alertsData = await response.json();
                setAlerts(alertsData);
            }
        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        }
    };

    const handleAlertAction = async (alertId, action) => {
        try {
            const response = await fetch(`${API_BASE}/alerts/${alertId}/action`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ action }),
            });
            
            if (response.ok) {
                // Update local state to reflect the action
                setAlerts(alerts.map(alert => 
                    alert.id === alertId 
                        ? { ...alert, status: action === 'dismiss' ? 'dismissed' : 'flagged' }
                        : alert
                ));
            }
        } catch (err) {
            console.error('Failed to perform action:', err);
        }
    };

    const handleLogout = () => {
        setLoggedIn(false);
        setUsername('');
        setPassword('');
        setToken('');
        setAlerts([]);
        localStorage.removeItem('token');
    };

    const handleSort = (field) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const sortedAlerts = [...alerts].sort((a, b) => {
        let aVal = a[sortField];
        let bVal = b[sortField];
        
        if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }
        
        if (sortDirection === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });

    // Check for stored token on component mount
    React.useEffect(() => {
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
            setToken(storedToken);
            setLoggedIn(true);
            fetchAlerts(storedToken);
        }
    }, []);

    const getSeverityColor = (severity) => {
        switch (severity?.toLowerCase()) {
            case 'critical': return 'text-red-600 bg-red-100';
            case 'high': return 'text-orange-600 bg-orange-100';
            case 'medium': return 'text-yellow-600 bg-yellow-100';
            case 'low': return 'text-green-600 bg-green-100';
            default: return 'text-gray-600 bg-gray-100';
        }
    };

    if (!loggedIn) {
        return (
            <div className="flex items-center justify-center h-screen bg-gray-100">
                <form className="bg-white p-8 rounded shadow-md w-96" onSubmit={handleLogin}>
                    <h1 className="text-2xl font-bold mb-4 text-center">SOC Assistant Login</h1>
                    {error && (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                            {error}
                        </div>
                    )}
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
                            Username
                        </label>
                        <input
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                            id="username"
                            type="text"
                            placeholder="Username (try: admin)"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            disabled={loading}
                        />
                    </div>
                    <div className="mb-6">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
                            Password
                        </label>
                        <input
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
                            id="password"
                            type="password"
                            placeholder="Password (try: password123)"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={loading}
                        />
                    </div>
                    <div className="flex items-center justify-between">
                        <button
                            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 w-full"
                            type="submit"
                            disabled={loading}
                        >
                            {loading ? 'Signing In...' : 'Sign In'}
                        </button>
                    </div>
                </form>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800">SOC Alert Dashboard</h1>
                    <p className="text-gray-600">Welcome, {username}</p>
                </div>
                <button
                    className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                    onClick={handleLogout}
                >
                    Logout
                </button>
            </div>
            
            <div className="bg-white shadow-lg rounded-lg overflow-hidden">
                <table className="min-w-full table-auto">
                    <thead>
                        <tr className="bg-gray-800 text-white uppercase text-sm leading-normal">
                            <th 
                                className="py-3 px-6 text-left cursor-pointer hover:bg-gray-700"
                                onClick={() => handleSort('timestamp')}
                            >
                                Timestamp {sortField === 'timestamp' && (sortDirection === 'asc' ? '↑' : '↓')}
                            </th>
                            <th 
                                className="py-3 px-6 text-left cursor-pointer hover:bg-gray-700"
                                onClick={() => handleSort('severity')}
                            >
                                Severity {sortField === 'severity' && (sortDirection === 'asc' ? '↑' : '↓')}
                            </th>
                            <th className="py-3 px-6 text-left">Alert Description</th>
                            <th 
                                className="py-3 px-6 text-center cursor-pointer hover:bg-gray-700"
                                onClick={() => handleSort('anomaly_score')}
                            >
                                Anomaly Score {sortField === 'anomaly_score' && (sortDirection === 'asc' ? '↑' : '↓')}
                            </th>
                            <th className="py-3 px-6 text-left">Source IP</th>
                            <th className="py-3 px-6 text-center">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="text-gray-600 text-sm font-light">
                        {sortedAlerts.map((alert) => (
                            <tr key={alert.id} className={`border-b border-gray-200 hover:bg-gray-50 ${alert.status === 'dismissed' ? 'opacity-50' : ''}`}>
                                <td className="py-3 px-6 text-left whitespace-nowrap font-medium">
                                    {alert.timestamp}
                                </td>
                                <td className="py-3 px-6 text-left">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                                        {alert.severity}
                                    </span>
                                </td>
                                <td className="py-3 px-6 text-left">{alert.alert}</td>
                                <td className="py-3 px-6 text-center">
                                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                                        alert.anomaly_score >= 0.8 ? 'bg-red-100 text-red-800' :
                                        alert.anomaly_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-green-100 text-green-800'
                                    }`}>
                                        {(alert.anomaly_score * 100).toFixed(1)}%
                                    </span>
                                </td>
                                <td className="py-3 px-6 text-left font-mono text-xs">
                                    {alert.source_ip}
                                </td>
                                <td className="py-3 px-6 text-center">
                                    {alert.status === 'active' ? (
                                        <div className="flex space-x-2 justify-center">
                                            <button 
                                                className="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-3 rounded text-xs"
                                                onClick={() => handleAlertAction(alert.id, 'flag')}
                                            >
                                                Flag
                                            </button>
                                            <button 
                                                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-1 px-3 rounded text-xs"
                                                onClick={() => handleAlertAction(alert.id, 'dismiss')}
                                            >
                                                Dismiss
                                            </button>
                                        </div>
                                    ) : (
                                        <span className="text-gray-400 text-xs capitalize">{alert.status}</span>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            <div className="mt-4 text-sm text-gray-600">
                Showing {alerts.length} alerts • Sorted by {sortField} ({sortDirection})
            </div>
        </div>
    );
};

ReactDOM.render(<App />, document.getElementById('root'));