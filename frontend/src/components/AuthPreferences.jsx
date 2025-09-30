import React, { useState, useEffect } from 'react';
import { Shield, Mail, Key, Fingerprint, CheckCircle, AlertCircle, Info } from 'lucide-react';

const AuthPreferences = ({ user, onPreferenceChange }) => {
  const [preferences, setPreferences] = useState({
    default_method: 'password',
    email_otp_enabled: false,
    passkey_enabled: false,
    mfa_enabled: user?.mfa_enabled || false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [hasPasskeys, setHasPasskeys] = useState(false);
  const [emailVerified, setEmailVerified] = useState(user?.email_verified || false);

  useEffect(() => {
    fetchPreferences();
    checkPasskeys();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchPreferences = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/auth/preferences', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences({
          default_method: data.default_method || 'password',
          email_otp_enabled: data.email_otp_enabled || false,
          passkey_enabled: data.passkey_enabled || false,
          mfa_enabled: user?.mfa_enabled || false
        });
        setEmailVerified(data.email_verified || false);
      }
    } catch (err) {
      console.error('Error fetching preferences:', err);
    }
  };

  const checkPasskeys = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/auth/passkey/list', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setHasPasskeys(data.passkeys && data.passkeys.length > 0);
      }
    } catch (err) {
      console.error('Error checking passkeys:', err);
    }
  };

  const updatePreference = async (key, value) => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/auth/preferences', {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ [key]: value })
      });

      const data = await response.json();

      if (response.ok) {
        setPreferences(prev => ({ ...prev, [key]: value }));
        setSuccess(data.message || 'Preference updated successfully');
        
        // Notify parent component
        if (onPreferenceChange) {
          onPreferenceChange(key, value);
        }

        // Update local user data
        const userData = JSON.parse(localStorage.getItem('user'));
        userData[key] = value;
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        setError(data.error || 'Failed to update preference');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDefaultMethodChange = (method) => {
    // Validate that the method is available
    if (method === 'email_otp' && !emailVerified) {
      setError('Please verify your email address before setting it as default');
      return;
    }
    if (method === 'passkey' && !hasPasskeys) {
      setError('Please register a passkey before setting it as default');
      return;
    }
    
    updatePreference('default_method', method);
  };

  const toggleEmailOTP = async () => {
    if (!emailVerified && !preferences.email_otp_enabled) {
      setError('Please verify your email address first');
      return;
    }
    
    updatePreference('email_otp_enabled', !preferences.email_otp_enabled);
  };

  const togglePasskey = async () => {
    if (!hasPasskeys && !preferences.passkey_enabled) {
      setError('Please register a passkey first');
      return;
    }
    
    updatePreference('passkey_enabled', !preferences.passkey_enabled);
  };

  const getMethodIcon = (method) => {
    switch (method) {
      case 'password':
        return <Key className="h-5 w-5" />;
      case 'email_otp':
        return <Mail className="h-5 w-5" />;
      case 'passkey':
        return <Fingerprint className="h-5 w-5" />;
      default:
        return <Shield className="h-5 w-5" />;
    }
  };

  const getMethodName = (method) => {
    switch (method) {
      case 'password':
        return 'Password + MFA';
      case 'email_otp':
        return 'Email OTP';
      case 'passkey':
        return 'Passkey';
      default:
        return 'Unknown';
    }
  };

  const getMethodDescription = (method) => {
    switch (method) {
      case 'password':
        return 'Traditional password login with optional multi-factor authentication';
      case 'email_otp':
        return 'Passwordless login using a one-time code sent to your email';
      case 'passkey':
        return 'Biometric authentication using fingerprint, Face ID, or security key';
      default:
        return '';
    }
  };

  const isMethodAvailable = (method) => {
    switch (method) {
      case 'password':
        return true; // Always available
      case 'email_otp':
        return emailVerified;
      case 'passkey':
        return hasPasskeys;
      default:
        return false;
    }
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-lg shadow-sm border border-slate-700/50">
      <div className="flex items-center mb-6">
        <Shield className="h-6 w-6 text-blue-500 mr-3" />
        <div>
          <h3 className="text-lg font-medium text-white">Authentication Preferences</h3>
          <p className="text-sm text-gray-400">Choose your preferred login method and enable additional options</p>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 rounded-md bg-red-900/20 border border-red-500/30 p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
            <div className="ml-3">
              <p className="text-sm text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 rounded-md bg-green-900/20 border border-green-500/30 p-4">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
            <div className="ml-3">
              <p className="text-sm text-green-300">{success}</p>
            </div>
          </div>
        </div>
      )}

      {/* Default Login Method */}
      <div className="mb-8">
        <h4 className="text-sm font-medium text-gray-300 mb-4">Default Login Method</h4>
        <p className="text-xs text-gray-400 mb-4">
          This method will be pre-selected when you visit the login page
        </p>

        <div className="space-y-3">
          {['password', 'email_otp', 'passkey'].map((method) => {
            const available = isMethodAvailable(method);
            const isSelected = preferences.default_method === method;

            return (
              <div
                key={method}
                className={`relative flex items-start p-4 rounded-lg border transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? 'bg-blue-900/20 border-blue-500/50 shadow-lg shadow-blue-500/10'
                    : available
                    ? 'bg-slate-900/30 border-slate-700/50 hover:border-slate-600/50'
                    : 'bg-slate-900/10 border-slate-700/30 opacity-50 cursor-not-allowed'
                }`}
                onClick={() => available && !loading && handleDefaultMethodChange(method)}
              >
                <div className="flex items-center flex-1">
                  <div className={`flex-shrink-0 ${isSelected ? 'text-blue-400' : 'text-gray-400'}`}>
                    {getMethodIcon(method)}
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="flex items-center">
                      <p className={`text-sm font-medium ${isSelected ? 'text-blue-300' : 'text-white'}`}>
                        {getMethodName(method)}
                      </p>
                      {isSelected && (
                        <CheckCircle className="ml-2 h-4 w-4 text-blue-400" />
                      )}
                      {!available && (
                        <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-600/20 text-yellow-400 rounded-full border border-yellow-500/30">
                          Setup Required
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {getMethodDescription(method)}
                    </p>
                    {!available && (
                      <p className="text-xs text-yellow-400 mt-2">
                        {method === 'email_otp' && '→ Verify your email address to enable'}
                        {method === 'passkey' && '→ Register a passkey to enable'}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Additional Options */}
      <div className="pt-6 border-t border-slate-700/50">
        <h4 className="text-sm font-medium text-gray-300 mb-4">Additional Security Options</h4>

        <div className="space-y-4">
          {/* Email OTP Toggle */}
          <div className="flex items-center justify-between p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <div className="flex items-center flex-1">
              <Mail className="h-5 w-5 text-gray-400 flex-shrink-0" />
              <div className="ml-3">
                <p className="text-sm font-medium text-white">Email OTP Login</p>
                <p className="text-xs text-gray-400 mt-1">
                  Allow passwordless login via email verification codes
                </p>
                {!emailVerified && (
                  <p className="text-xs text-yellow-400 mt-1">
                    Email verification required
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={toggleEmailOTP}
              disabled={loading || (!emailVerified && !preferences.email_otp_enabled)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
                preferences.email_otp_enabled ? 'bg-blue-600' : 'bg-gray-600'
              } ${loading || (!emailVerified && !preferences.email_otp_enabled) ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  preferences.email_otp_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Passkey Toggle */}
          <div className="flex items-center justify-between p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <div className="flex items-center flex-1">
              <Fingerprint className="h-5 w-5 text-gray-400 flex-shrink-0" />
              <div className="ml-3">
                <p className="text-sm font-medium text-white">Passkey Authentication</p>
                <p className="text-xs text-gray-400 mt-1">
                  Enable biometric login with fingerprint or Face ID
                </p>
                {!hasPasskeys && (
                  <p className="text-xs text-yellow-400 mt-1">
                    Register a passkey first
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={togglePasskey}
              disabled={loading || (!hasPasskeys && !preferences.passkey_enabled)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
                preferences.passkey_enabled ? 'bg-blue-600' : 'bg-gray-600'
              } ${loading || (!hasPasskeys && !preferences.passkey_enabled) ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  preferences.passkey_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* MFA Status (Read-only, managed in MFASetup component) */}
          <div className="flex items-center justify-between p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <div className="flex items-center flex-1">
              <Shield className="h-5 w-5 text-gray-400 flex-shrink-0" />
              <div className="ml-3">
                <p className="text-sm font-medium text-white">Multi-Factor Authentication</p>
                <p className="text-xs text-gray-400 mt-1">
                  Adds extra security to password login
                </p>
              </div>
            </div>
            <div className="flex items-center">
              {preferences.mfa_enabled ? (
                <span className="px-3 py-1 text-xs bg-green-600/20 text-green-400 rounded-full border border-green-500/30 flex items-center">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Enabled
                </span>
              ) : (
                <span className="px-3 py-1 text-xs bg-gray-600/20 text-gray-400 rounded-full border border-gray-500/30">
                  Disabled
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-6 bg-blue-900/10 border border-blue-500/20 rounded-md p-4">
        <div className="flex">
          <Info className="h-5 w-5 text-blue-400 flex-shrink-0" />
          <div className="ml-3">
            <h5 className="text-sm font-medium text-blue-300">Security Tips</h5>
            <ul className="text-xs text-blue-200/80 mt-2 space-y-1">
              <li>• <strong>Passkeys</strong> are the most secure and convenient option</li>
              <li>• <strong>Email OTP</strong> is great when you don't have access to your device</li>
              <li>• <strong>MFA</strong> adds extra protection to password-based login</li>
              <li>• You can always use any enabled method, regardless of your default</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPreferences;
