// ui/src/App.jsx
const { useState, useEffect } = React;

const App = () => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);

  const handleLogin = async () => {
    try {
      const response = await fetch('http://localhost:5001/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await response.json();
      if (data.token) {
        setToken(data.token);
        localStorage.setItem('token', data.token);
        setError(null);
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (error) {
      setError('Network error: ' + error.message);
    }
  };

  useEffect(() => {
    if (token) {
      fetch('http://localhost:5000/alerts', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch alerts: ' + res.status);
          return res.json();
        })
        .then(data => setAlerts(data.slice(0, 5)))
        .catch(err => setError('Fetch alerts error: ' + err.message));
    }
  }, [token]);

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="p-6 bg-white rounded shadow-md">
          <h2 className="text-2xl font-bold mb-4">SOC Login</h2>
          {error && <p className="text-red-500 mb-2">{error}</p>}
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mb-2 p-2 border rounded w-full"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-2 p-2 border rounded w-full"
          />
          <button
            onClick={handleLogin}
            className="bg-blue-500 text-white p-2 rounded w-full hover:bg-blue-600"
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-bold mb-4">SOC Alert Dashboard</h1>
      {error && <p className="text-red-500 mb-2">{error}</p>}
      <table className="w-full border-collapse border">
        <thead>
          <tr className="bg-gray-200">
            <th className="border p-2">ID</th>
            <th className="border p-2">Timestamp</th>
            <th className="border p-2">User ID</th>
            <th className="border p-2">Action</th>
            <th className="border p-2">Controls</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr key={alert.id}>
              <td className="border p-2">{alert.id}</td>
              <td className="border p-2">{alert.timestamp}</td>
              <td className="border p-2">{alert.user_id}</td>
              <td className="border p-2">{alert.action}</td>
              <td className="border p-2">
                <button
                  onClick={() => console.log(`Dismiss alert ${alert.id}`)}
                  className="bg-red-500 text-white p-1 rounded mr-2 hover:bg-red-600"
                >
                  Dismiss
                </button>
                <button
                  onClick={() => console.log(`Flag alert ${alert.id}`)}
                  className="bg-yellow-500 text-white p-1 rounded hover:bg-yellow-600"
                >
                  Flag
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
