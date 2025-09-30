import React, { useState, useEffect } from 'react';
import { Fingerprint, Plus, Trash2, AlertCircle, CheckCircle, Shield } from 'lucide-react';

const PasskeyManagement = () => {
  const [passkeys, setPasskeys] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);

  useEffect(() => {
    loadPasskeys();
  }, []);

  const loadPasskeys = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/auth/passkey/list', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPasskeys(data.passkeys || []);
      }
    } catch (err) {
      console.error('Failed to load passkeys:', err);
    }
  };

  const registerPasskey = async () => {
    setError('');
    setSuccess('');
    setIsRegistering(true);

    try {
      // Check WebAuthn support
      if (!window.PublicKeyCredential) {
        setError('Passkeys are not supported in this browser. Please use Chrome, Edge, Safari, or Firefox.');
        setIsRegistering(false);
        return;
      }

      const token = localStorage.getItem('access_token');

      // Step 1: Begin registration
      const beginResponse = await fetch('http://localhost:5000/api/auth/passkey/register/begin', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!beginResponse.ok) {
        const data = await beginResponse.json();
        throw new Error(data.error || 'Failed to start passkey registration');
      }

      const { options, state_id } = await beginResponse.json();

      // Step 2: Convert options for WebAuthn API
      const publicKey = {
        ...options.publicKey,
        challenge: Uint8Array.from(atob(options.publicKey.challenge), c => c.charCodeAt(0)),
        user: {
          ...options.publicKey.user,
          id: Uint8Array.from(atob(options.publicKey.user.id), c => c.charCodeAt(0))
        }
      };

      // Step 3: Create credential
      const credential = await navigator.credentials.create({ publicKey });

      // Step 4: Complete registration
      const completeResponse = await fetch('http://localhost:5000/api/auth/passkey/register/complete', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          state_id,
          credential: {
            id: credential.id,
            rawId: btoa(String.fromCharCode(...new Uint8Array(credential.rawId))),
            type: credential.type,
            response: {
              clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(credential.response.clientDataJSON))),
              attestationObject: btoa(String.fromCharCode(...new Uint8Array(credential.response.attestationObject)))
            }
          }
        })
      });

      const data = await completeResponse.json();

      if (completeResponse.ok) {
        setSuccess('Passkey registered successfully!');
        loadPasskeys();
      } else {
        throw new Error(data.error || 'Failed to complete registration');
      }
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Registration cancelled or timed out');
      } else if (err.name === 'InvalidStateError') {
        setError('This authenticator is already registered');
      } else {
        setError(err.message || 'Failed to register passkey');
      }
    } finally {
      setIsRegistering(false);
    }
  };

  const deletePasskey = async (credentialId) => {
    if (!window.confirm('Are you sure you want to delete this passkey?')) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:5000/api/auth/passkey/${credentialId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Passkey deleted successfully');
        loadPasskeys();
      } else {
        setError(data.error || 'Failed to delete passkey');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 px-6 py-8">
          <div className="flex items-center">
            <div className="bg-white/20 backdrop-blur-sm p-3 rounded-full mr-4">
              <Fingerprint className="h-8 w-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Passkey Management</h2>
              <p className="text-blue-100 mt-1">Secure your account with biometric authentication</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Info Box */}
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <Shield className="h-5 w-5 text-blue-500" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">What are Passkeys?</h3>
                <p className="mt-2 text-sm text-blue-700">
                  Passkeys use your device's biometric authentication (fingerprint, face recognition) or security keys 
                  to sign in securely without passwords. They're phishing-resistant and more secure than traditional passwords.
                </p>
              </div>
            </div>
          </div>

          {/* Messages */}
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">{error}</h3>
                </div>
              </div>
            </div>
          )}

          {success && (
            <div className="mb-4 rounded-md bg-green-50 p-4">
              <div className="flex">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">{success}</h3>
                </div>
              </div>
            </div>
          )}

          {/* Register Button */}
          <div className="mb-6">
            <button
              onClick={registerPasskey}
              disabled={isRegistering}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRegistering ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Registering...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Register New Passkey
                </>
              )}
            </button>
          </div>

          {/* Passkeys List */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Your Passkeys</h3>
            
            {passkeys.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-lg">
                <Fingerprint className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No passkeys registered yet</p>
                <p className="text-sm text-gray-400 mt-2">Click "Register New Passkey" to get started</p>
              </div>
            ) : (
              <div className="space-y-3">
                {passkeys.map((passkey) => (
                  <div
                    key={passkey.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-center">
                      <div className="bg-blue-100 p-2 rounded-full mr-3">
                        <Fingerprint className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">{passkey.name}</h4>
                        <p className="text-xs text-gray-500">
                          Added {new Date(passkey.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => deletePasskey(passkey.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete passkey"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Browser Support Info */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Browser Support</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-600">
              <div className="flex items-center">
                <span className="text-green-500 mr-1">✓</span> Chrome 67+
              </div>
              <div className="flex items-center">
                <span className="text-green-500 mr-1">✓</span> Edge 18+
              </div>
              <div className="flex items-center">
                <span className="text-green-500 mr-1">✓</span> Firefox 60+
              </div>
              <div className="flex items-center">
                <span className="text-green-500 mr-1">✓</span> Safari 13+
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Note: HTTPS is required for passkeys to work (except on localhost)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PasskeyManagement;
