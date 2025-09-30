import React, { useState } from 'react';
import { Shield, Eye, EyeOff, AlertCircle, Smartphone, Mail, Key, Fingerprint, ArrowLeft } from 'lucide-react';

const EnhancedLogin = ({ onLogin, loading }) => {
  const [authMode, setAuthMode] = useState('password'); // 'password', 'email-otp', 'passkey'
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    mfaToken: '',
    email: '',
    otp: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [checkingMfa, setCheckingMfa] = useState(false);

  // Password Login
  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
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

  // Email OTP - Request
  const handleRequestOTP = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/auth/passwordless/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setOtpSent(true);
        setSuccess('Login code sent to your email. Please check your inbox.');
      } else {
        setError(data.error || 'Failed to send OTP');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Email OTP - Verify
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/auth/passwordless/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          otp: formData.otp
        }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        onLogin(data.user);
      } else {
        setError(data.error || 'Invalid OTP');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Passkey Authentication
  const handlePasskeyLogin = async () => {
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      // Check if WebAuthn is supported
      if (!window.PublicKeyCredential) {
        setError('Passkeys are not supported in this browser. Please use Chrome, Edge, Safari, or Firefox.');
        setIsLoading(false);
        return;
      }

      if (!formData.username) {
        setError('Please enter your username');
        setIsLoading(false);
        return;
      }

      // Step 1: Begin authentication
      const beginResponse = await fetch('http://localhost:5000/api/auth/passkey/authenticate/begin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username
        }),
      });

      if (!beginResponse.ok) {
        const data = await beginResponse.json().catch(() => ({}));
        setError(data.error || data.message || 'Failed to start passkey authentication');
        setIsLoading(false);
        return;
      }

      const { options, state_id } = await beginResponse.json();

      // Helper function to decode base64url to Uint8Array
      const base64urlToUint8Array = (base64url) => {
        // Convert base64url to base64
        const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
        // Add padding if needed
        const padding = '='.repeat((4 - base64.length % 4) % 4);
        const base64Padded = base64 + padding;
        // Decode
        const binary = atob(base64Padded);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }
        return bytes;
      };

      // Step 2: Convert options for WebAuthn API
      const publicKey = {
        ...options.publicKey,
        challenge: base64urlToUint8Array(options.publicKey.challenge),
        allowCredentials: options.publicKey.allowCredentials.map(cred => ({
          ...cred,
          id: base64urlToUint8Array(cred.id)
        }))
      };

      // Step 3: Get assertion from authenticator
      const assertion = await navigator.credentials.get({ publicKey });

      // Step 4: Complete authentication
      const completeResponse = await fetch('http://localhost:5000/api/auth/passkey/authenticate/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          state_id,
          credential: {
            id: assertion.id,  // Keep as base64url (from browser)
            rawId: assertion.id,  // Use same value as id
            type: assertion.type,
            response: {
              clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(assertion.response.clientDataJSON))),
              authenticatorData: btoa(String.fromCharCode(...new Uint8Array(assertion.response.authenticatorData))),
              signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature))),
              userHandle: assertion.response.userHandle ? 
                btoa(String.fromCharCode(...new Uint8Array(assertion.response.userHandle))) : null
            }
          }
        }),
      });

      const data = await completeResponse.json().catch(() => ({}));

      if (completeResponse.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        onLogin(data.user);
      } else {
        setError(data.error || data.message || 'Passkey authentication failed');
      }
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Authentication cancelled or timed out');
      } else if (err.name === 'InvalidStateError') {
        setError('No passkey found for this account');
      } else {
        setError('Passkey authentication failed: ' + err.message);
      }
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
      }
    } catch (err) {
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

    if (name === 'username' && authMode === 'password') {
      clearTimeout(window.mfaCheckTimeout);
      window.mfaCheckTimeout = setTimeout(() => {
        checkMfaRequirement(value);
      }, 500);
    }
  };

  const switchAuthMode = (mode) => {
    setAuthMode(mode);
    setError('');
    setSuccess('');
    setMfaRequired(false);
    setOtpSent(false);
    setFormData({
      username: '',
      password: '',
      mfaToken: '',
      email: '',
      otp: ''
    });
  };

  const renderPasswordLogin = () => (
    <form className="mt-8 space-y-6" onSubmit={handlePasswordLogin}>
      <div className="rounded-md shadow-sm -space-y-px">
        <div>
          <label htmlFor="username" className="sr-only">Username</label>
          <input
            id="username"
            name="username"
            type="text"
            required
            className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
            placeholder="Username"
            value={formData.username}
            onChange={handleChange}
            disabled={isLoading}
          />
        </div>
        <div className="relative">
          <label htmlFor="password" className="sr-only">Password</label>
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            required
            className={`appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 ${
              mfaRequired ? '' : 'rounded-b-md'
            } focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
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
            <label htmlFor="mfaToken" className="sr-only">MFA Code</label>
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Smartphone className="h-4 w-4 text-gray-400" />
            </div>
            <input
              id="mfaToken"
              name="mfaToken"
              type="text"
              maxLength="6"
              pattern="[0-9]{6}"
              className="appearance-none rounded-none relative block w-full pl-10 px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="6-digit MFA code"
              value={formData.mfaToken}
              onChange={handleChange}
              disabled={isLoading}
              autoFocus
            />
          </div>
        )}
      </div>

      <div>
        <button
          type="submit"
          disabled={isLoading || loading}
          className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading || loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Signing in...
            </div>
          ) : (
            'Sign in with Password'
          )}
        </button>
      </div>
    </form>
  );

  const renderEmailOTPLogin = () => (
    <form className="mt-8 space-y-6" onSubmit={otpSent ? handleVerifyOTP : handleRequestOTP}>
      <div className="rounded-md shadow-sm space-y-3">
        <div>
          <label htmlFor="email" className="sr-only">Email</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="email"
              name="email"
              type="email"
              required
              className="appearance-none relative block w-full pl-10 px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Email address"
              value={formData.email}
              onChange={handleChange}
              disabled={isLoading || otpSent}
            />
          </div>
        </div>

        {otpSent && (
          <div>
            <label htmlFor="otp" className="sr-only">Verification Code</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Key className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="otp"
                name="otp"
                type="text"
                maxLength="6"
                pattern="[0-9]{6}"
                required
                className="appearance-none relative block w-full pl-10 px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm tracking-widest text-center text-lg font-mono"
                placeholder="000000"
                value={formData.otp}
                onChange={handleChange}
                disabled={isLoading}
                autoFocus
              />
            </div>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <button
          type="submit"
          disabled={isLoading || loading}
          className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading || loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {otpSent ? 'Verifying...' : 'Sending code...'}
            </div>
          ) : (
            otpSent ? 'Verify Code' : 'Send Login Code'
          )}
        </button>

        {otpSent && (
          <button
            type="button"
            onClick={() => setOtpSent(false)}
            className="w-full flex items-center justify-center text-sm text-blue-600 hover:text-blue-500"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Use different email
          </button>
        )}
      </div>
    </form>
  );

  const renderPasskeyLogin = () => (
    <div className="mt-8 space-y-6">
      <div className="rounded-md shadow-sm">
        <div>
          <label htmlFor="username-passkey" className="sr-only">Username</label>
          <input
            id="username-passkey"
            name="username"
            type="text"
            required
            className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
            placeholder="Username"
            value={formData.username}
            onChange={handleChange}
            disabled={isLoading}
          />
        </div>
      </div>

      <div>
        <button
          type="button"
          onClick={handlePasskeyLogin}
          disabled={isLoading || loading || !formData.username}
          className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading || loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Authenticating...
            </div>
          ) : (
            <div className="flex items-center">
              <Fingerprint className="h-5 w-5 mr-2" />
              Sign in with Passkey
            </div>
          )}
        </button>
      </div>

      <div className="text-center text-xs text-gray-600">
        <p>Use your fingerprint, face, or security key to sign in</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/50">
            <Shield className="h-10 w-10 text-white" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            SOC Dashboard
          </h2>
          <p className="mt-2 text-center text-sm text-gray-300">
            Secure Authentication Portal
          </p>
        </div>

        {/* Auth Mode Tabs */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-1 flex space-x-1">
          <button
            onClick={() => switchAuthMode('password')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all ${
              authMode === 'password'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-gray-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <div className="flex items-center justify-center">
              <Key className="h-4 w-4 mr-1" />
              Password
            </div>
          </button>
          <button
            onClick={() => switchAuthMode('email-otp')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all ${
              authMode === 'email-otp'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-gray-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <div className="flex items-center justify-center">
              <Mail className="h-4 w-4 mr-1" />
              Email OTP
            </div>
          </button>
          <button
            onClick={() => switchAuthMode('passkey')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all ${
              authMode === 'passkey'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-gray-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <div className="flex items-center justify-center">
              <Fingerprint className="h-4 w-4 mr-1" />
              Passkey
            </div>
          </button>
        </div>

        {/* Login Form Container */}
        <div className="bg-white rounded-lg shadow-2xl p-8">
          {authMode === 'password' && renderPasswordLogin()}
          {authMode === 'email-otp' && renderEmailOTPLogin()}
          {authMode === 'passkey' && renderPasskeyLogin()}

          {/* Error/Success Messages */}
          {error && typeof error === 'string' && error.length > 0 && (
            <div className="mt-4 rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">{error}</h3>
                </div>
              </div>
            </div>
          )}

          {success && typeof success === 'string' && success.length > 0 && (
            <div className="mt-4 rounded-md bg-green-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <Mail className="h-5 w-5 text-green-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">{success}</h3>
                </div>
              </div>
            </div>
          )}

          {checkingMfa && (
            <div className="mt-4 text-center">
              <div className="text-xs text-blue-600 flex items-center justify-center">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-2"></div>
                Checking MFA requirement...
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-400">
          <p>Protected by enterprise-grade security</p>
        </div>
      </div>
    </div>
  );
};

export default EnhancedLogin;
