import React, { useState } from 'react';
import { Shield, Eye, EyeOff, AlertCircle, Smartphone } from 'lucide-react';

const Login = ({ onLogin, loading }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    mfaToken: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [checkingMfa, setCheckingMfa] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password,
          mfa_token: formData.mfaToken || undefined
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Store tokens
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        onLogin(data.user);
      } else {
        if (data.mfa_required) {
          setMfaRequired(true);
          setError('Please enter your MFA code from Google Authenticator');
        } else {
          setError(data.error || 'Login failed');
        }
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const checkMfaRequirement = async (username) => {
    if (!username.trim()) {
      setMfaRequired(false);
      return;
    }

    setCheckingMfa(true);
    try {
      const response = await fetch('http://localhost:5000/api/auth/check-mfa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username.trim() }),
      });

      if (response.ok) {
        const data = await response.json();
        setMfaRequired(data.mfa_required);
        if (data.mfa_required) {
          setError(''); // Clear any previous errors when MFA is required
        }
      }
    } catch (err) {
      // Silently fail - don't show error for MFA check
      console.log('MFA check failed:', err);
    } finally {
      setCheckingMfa(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });

    // Check MFA requirement when username changes
    if (name === 'username') {
      // Debounce the MFA check
      clearTimeout(window.mfaCheckTimeout);
      window.mfaCheckTimeout = setTimeout(() => {
        checkMfaRequirement(value);
      }, 500);
    }
  };

  const handleUsernameBlur = () => {
    // Immediate check when user leaves username field
    clearTimeout(window.mfaCheckTimeout);
    checkMfaRequirement(formData.username);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-indigo-600">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            SOC Dashboard
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to your account
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username" className="sr-only">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Username"
                value={formData.username}
                onChange={handleChange}
                onBlur={handleUsernameBlur}
                disabled={isLoading}
              />
            </div>
            <div className="relative">
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 ${
                  mfaRequired ? '' : 'rounded-b-md'
                } focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm`}
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                disabled={isLoading}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-gray-400" />
                ) : (
                  <Eye className="h-4 w-4 text-gray-400" />
                )}
              </button>
            </div>
            
            {mfaRequired && (
              <div className="relative">
                <label htmlFor="mfaToken" className="sr-only">
                  MFA Code
                </label>
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Smartphone className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  id="mfaToken"
                  name="mfaToken"
                  type="text"
                  maxLength="6"
                  pattern="[0-9]{6}"
                  className="appearance-none rounded-none relative block w-full pl-10 px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="6-digit MFA code"
                  value={formData.mfaToken}
                  onChange={handleChange}
                  disabled={isLoading}
                  autoFocus
                />
              </div>
            )}
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    {error}
                  </h3>
                </div>
              </div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading || loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading || loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Signing in...
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          {mfaRequired && (
            <div className="text-center">
              <p className="text-xs text-gray-600">
                <Smartphone className="inline h-3 w-3 mr-1" />
                Enter the 6-digit code from your Google Authenticator app
              </p>
            </div>
          )}

          {checkingMfa && (
            <div className="text-center">
              <div className="text-xs text-blue-600 flex items-center justify-center">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-2"></div>
                Checking MFA requirement...
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default Login;
