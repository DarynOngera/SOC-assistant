import React, { useState, useEffect } from 'react';
import { Fingerprint, Shield, CheckCircle, AlertCircle, Trash2, Plus } from 'lucide-react';

const PasskeySetup = ({ user }) => {
  const [passkeys, setPasskeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);

  useEffect(() => {
    fetchPasskeys();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchPasskeys = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/auth/passkey/list', {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setPasskeys(data.passkeys || []);
      }
    } catch (err) {
      console.error('Error fetching passkeys:', err);
    }
  };

  const registerPasskey = async () => {
    setError('');
    setSuccess('');
    setIsRegistering(true);

    try {
      // Check if WebAuthn is supported
      if (!window.PublicKeyCredential) {
        setError('Passkeys are not supported in this browser. Please use Chrome, Edge, Safari, or Firefox.');
        setIsRegistering(false);
        return;
      }

      // Step 1: Begin registration
      const beginResponse = await fetch('http://localhost:5000/api/auth/passkey/register/begin', {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (!beginResponse.ok) {
        const data = await beginResponse.json();
        setError(data.error || 'Failed to start passkey registration');
        setIsRegistering(false);
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
        user: {
          ...options.publicKey.user,
          id: base64urlToUint8Array(options.publicKey.user.id)
        }
      };

      // Step 3: Create credential
      const credential = await navigator.credentials.create({ publicKey });

      // Step 4: Complete registration
      // Note: credential.id is base64url, rawId needs to be converted to match
      // But for backend compatibility, we send rawId as base64 and let backend handle it
      const completeResponse = await fetch('http://localhost:5000/api/auth/passkey/register/complete', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          state_id,
          credential: {
            id: credential.id,  // Keep as base64url (from browser)
            rawId: credential.id,  // Use same value as id
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
        fetchPasskeys();
      } else {
        setError(data.error || 'Failed to register passkey');
      }
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Registration cancelled or timed out');
      } else if (err.name === 'InvalidStateError') {
        setError('This device already has a passkey registered');
      } else {
        setError('Passkey registration failed: ' + err.message);
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
      // URL encode the credential ID to handle special characters like / and =
      const encodedId = encodeURIComponent(credentialId);
      const response = await fetch(`http://localhost:5000/api/auth/passkey/${encodedId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Passkey deleted successfully');
        fetchPasskeys();
      } else {
        setError(data.error || 'Failed to delete passkey');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-lg shadow-sm border border-slate-700/50">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Fingerprint className="h-6 w-6 text-blue-500 mr-3" />
          <div>
            <h3 className="text-lg font-medium text-white">Passkey Authentication</h3>
            <p className="text-sm text-gray-400">Secure, passwordless login with biometrics</p>
          </div>
        </div>
        <button
          onClick={registerPasskey}
          disabled={isRegistering || loading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          {isRegistering ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Registering...
            </>
          ) : (
            <>
              <Plus className="h-4 w-4 mr-2" />
              Add Passkey
            </>
          )}
        </button>
      </div>

      {/* Info Box */}
      <div className="bg-blue-900/20 border border-blue-500/30 rounded-md p-4 mb-6">
        <div className="flex">
          <Shield className="h-5 w-5 text-blue-400 flex-shrink-0" />
          <div className="ml-3">
            <h4 className="text-sm font-medium text-blue-300">What are Passkeys?</h4>
            <p className="text-sm text-blue-200/80 mt-1">
              Passkeys use your device's biometric authentication (fingerprint, face recognition, or PIN) 
              to securely log you in without a password. They're more secure and convenient than traditional passwords.
            </p>
            <ul className="text-sm text-blue-200/80 mt-2 space-y-1 ml-4">
              <li>• Works with fingerprint, Face ID, Windows Hello, or security keys</li>
              <li>• No passwords to remember or type</li>
              <li>• Protected against phishing and data breaches</li>
              <li>• Syncs across your devices (depending on your platform)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 rounded-md bg-red-900/20 border border-red-500/30 p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 rounded-md bg-green-900/20 border border-green-500/30 p-4">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <p className="text-sm text-green-300">{success}</p>
            </div>
          </div>
        </div>
      )}

      {/* Passkeys List */}
      <div>
        <h4 className="text-sm font-medium text-gray-300 mb-3">
          Registered Passkeys ({passkeys.length})
        </h4>
        
        {passkeys.length === 0 ? (
          <div className="text-center py-8 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <Fingerprint className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">No passkeys registered yet</p>
            <p className="text-gray-500 text-xs mt-1">Click "Add Passkey" to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {passkeys.map((passkey) => (
              <div
                key={passkey.credential_id}
                className="flex items-center justify-between p-4 bg-slate-900/30 rounded-lg border border-slate-700/50 hover:border-slate-600/50 transition-all duration-200"
              >
                <div className="flex items-center flex-1">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-blue-600/20 rounded-full flex items-center justify-center">
                      <Fingerprint className="h-5 w-5 text-blue-400" />
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-white">
                        {passkey.device_name || 'Unnamed Device'}
                      </p>
                      {passkey.last_used && (
                        <span className="ml-2 px-2 py-0.5 text-xs bg-green-600/20 text-green-400 rounded-full border border-green-500/30">
                          Recently Used
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex items-center text-xs text-gray-400 space-x-4">
                      <span>Created: {formatDate(passkey.created_at)}</span>
                      {passkey.last_used && (
                        <span>Last used: {formatDate(passkey.last_used)}</span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => deletePasskey(passkey.credential_id)}
                  className="ml-4 p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-md transition-all duration-200"
                  title="Delete passkey"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Browser Compatibility Note */}
      <div className="mt-6 pt-6 border-t border-slate-700/50">
        <p className="text-xs text-gray-500">
          <strong>Browser Support:</strong> Passkeys work best in Chrome 109+, Edge 109+, Safari 16+, and Firefox 119+. 
          Make sure your browser and operating system are up to date for the best experience.
        </p>
      </div>
    </div>
  );
};

export default PasskeySetup;
