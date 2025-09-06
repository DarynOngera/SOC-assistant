import React, { useState } from 'react';
import { Smartphone, Shield, CheckCircle, AlertCircle, Copy, Eye, EyeOff } from 'lucide-react';

const MFASetup = ({ user, onMFAChange }) => {
  const [step, setStep] = useState(1); // 1: Setup, 2: Verify, 3: Complete
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSecret, setShowSecret] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const setupMFA = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/auth/mfa/setup', {
        method: 'POST',
        headers: getAuthHeaders()
      });

      const data = await response.json();

      if (response.ok) {
        setSecret(data.secret);
        setQrCode(data.qr_code);
        setStep(2);
      } else {
        setError(data.error || 'Failed to setup MFA');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const verifyAndEnable = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/auth/mfa/enable', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ token: verificationCode })
      });

      const data = await response.json();

      if (response.ok) {
        setStep(3);
        onMFAChange(true);
      } else {
        setError(data.error || 'Invalid verification code');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const disableMFA = async () => {
    if (!window.confirm('Are you sure you want to disable MFA? This will reduce your account security.')) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/auth/mfa/disable', {
        method: 'POST',
        headers: getAuthHeaders()
      });

      const data = await response.json();

      if (response.ok) {
        onMFAChange(false);
      } else {
        setError(data.error || 'Failed to disable MFA');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const copySecret = () => {
    navigator.clipboard.writeText(secret);
  };

  if (user.mfa_enabled && step === 1) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Shield className="h-6 w-6 text-green-500 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Multi-Factor Authentication</h3>
              <p className="text-sm text-gray-600">MFA is currently enabled for your account</p>
            </div>
          </div>
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-sm font-medium text-green-700">Enabled</span>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <p className="text-sm text-green-800">
                Your account is protected with two-factor authentication using Google Authenticator.
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        <button
          onClick={disableMFA}
          disabled={loading}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
        >
          {loading ? 'Disabling...' : 'Disable MFA'}
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center mb-6">
        <Smartphone className="h-6 w-6 text-indigo-600 mr-3" />
        <div>
          <h3 className="text-lg font-medium text-gray-900">Multi-Factor Authentication Setup</h3>
          <p className="text-sm text-gray-600">Secure your account with Google Authenticator</p>
        </div>
      </div>

      {/* Step 1: Introduction */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <Shield className="h-5 w-5 text-blue-400" />
              <div className="ml-3">
                <h4 className="text-sm font-medium text-blue-800">Why enable MFA?</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Multi-factor authentication adds an extra layer of security to your account by requiring 
                  a time-based code from your mobile device in addition to your password.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Before you start:</h4>
            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
              <li>Install Google Authenticator on your mobile device</li>
              <li>Make sure your device's time is synchronized</li>
              <li>Have your device ready to scan a QR code</li>
            </ul>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={setupMFA}
            disabled={loading}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Setting up...' : 'Start MFA Setup'}
          </button>
        </div>
      )}

      {/* Step 2: QR Code and Verification */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="text-center">
            <h4 className="font-medium text-gray-900 mb-4">Scan QR Code</h4>
            {qrCode && (
              <div className="inline-block p-4 bg-white border-2 border-gray-200 rounded-lg">
                <img 
                  src={`data:image/png;base64,${qrCode}`} 
                  alt="MFA QR Code"
                  className="w-48 h-48"
                />
              </div>
            )}
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
            <h5 className="font-medium text-gray-900 mb-2">Manual Entry</h5>
            <p className="text-sm text-gray-600 mb-3">
              If you can't scan the QR code, enter this secret manually:
            </p>
            <div className="flex items-center space-x-2">
              <code className="flex-1 bg-white px-3 py-2 border border-gray-300 rounded text-sm font-mono">
                {showSecret ? secret : '••••••••••••••••••••••••••••••••'}
              </code>
              <button
                onClick={() => setShowSecret(!showSecret)}
                className="p-2 text-gray-500 hover:text-gray-700"
              >
                {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
              <button
                onClick={copySecret}
                className="p-2 text-gray-500 hover:text-gray-700"
              >
                <Copy className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter verification code from your authenticator app:
            </label>
            <input
              type="text"
              maxLength="6"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
              placeholder="123456"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              onClick={() => setStep(1)}
              className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200"
            >
              Back
            </button>
            <button
              onClick={verifyAndEnable}
              disabled={loading || verificationCode.length !== 6}
              className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Verifying...' : 'Verify & Enable'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Success */}
      {step === 3 && (
        <div className="text-center space-y-4">
          <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h4 className="text-lg font-medium text-gray-900">MFA Successfully Enabled!</h4>
            <p className="text-sm text-gray-600 mt-2">
              Your account is now protected with two-factor authentication. You'll need to enter 
              a code from your authenticator app each time you log in.
            </p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <div className="ml-3 text-left">
                <h5 className="text-sm font-medium text-green-800">Important:</h5>
                <ul className="text-sm text-green-700 mt-1 space-y-1">
                  <li>• Keep your mobile device secure</li>
                  <li>• Don't share your authenticator app with others</li>
                  <li>• Contact your administrator if you lose access to your device</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MFASetup;
