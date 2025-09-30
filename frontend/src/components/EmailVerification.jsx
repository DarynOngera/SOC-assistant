import React, { useState, useEffect } from 'react';
import { Mail, CheckCircle, AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react';

const EmailVerification = ({ email, onVerified, onBack }) => {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [isVerified, setIsVerified] = useState(false);

  // Auto-focus first input on mount
  useEffect(() => {
    document.getElementById('otp-0')?.focus();
  }, []);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  const handleOtpChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      document.getElementById(`otp-${index + 1}`)?.focus();
    }

    // Auto-submit when all 6 digits are entered
    if (newOtp.every(digit => digit !== '') && index === 5) {
      handleVerify(newOtp.join(''));
    }
  };

  const handleKeyDown = (index, e) => {
    // Handle backspace
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      document.getElementById(`otp-${index - 1}`)?.focus();
    }
    // Handle paste
    if (e.key === 'v' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      navigator.clipboard.readText().then(text => {
        const digits = text.replace(/\D/g, '').slice(0, 6).split('');
        const newOtp = [...otp];
        digits.forEach((digit, i) => {
          if (i < 6) newOtp[i] = digit;
        });
        setOtp(newOtp);
        if (digits.length === 6) {
          handleVerify(newOtp.join(''));
        }
      });
    }
  };

  const handleVerify = async (otpCode = null) => {
    const code = otpCode || otp.join('');
    
    if (code.length !== 6) {
      setError('Please enter all 6 digits');
      return;
    }

    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/auth/email/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          otp: code
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Email verified successfully! 🎉');
        setIsVerified(true);
        setTimeout(() => {
          if (onVerified) onVerified();
        }, 1500);
      } else {
        setError(data.error || 'Invalid verification code');
        // Clear OTP on error
        setOtp(['', '', '', '', '', '']);
        document.getElementById('otp-0')?.focus();
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;

    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/auth/email/resend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Verification code sent! Check your email.');
        setResendCooldown(60); // 60 second cooldown
        setOtp(['', '', '', '', '', '']);
        document.getElementById('otp-0')?.focus();
      } else {
        setError(data.error || 'Failed to resend code');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Back Button */}
        {onBack && !isVerified && (
          <button
            onClick={onBack}
            className="mb-4 flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
            <span>Back</span>
          </button>
        )}

        {/* Main Card */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-8 text-center">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 backdrop-blur-sm">
              {isVerified ? (
                <CheckCircle className="text-white" size={32} />
              ) : (
                <Mail className="text-white" size={32} />
              )}
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">
              {isVerified ? 'Email Verified!' : 'Verify Your Email'}
            </h1>
            <p className="text-green-100 text-sm">
              {isVerified 
                ? 'Your email has been successfully verified'
                : `We sent a verification code to ${email}`
              }
            </p>
          </div>

          {/* Content */}
          <div className="p-8">
            {!isVerified && (
              <>
                {/* Instructions */}
                <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <p className="text-blue-200 text-sm text-center">
                    Enter the 6-digit code from your email
                  </p>
                </div>

                {/* OTP Input */}
                <div className="flex gap-2 justify-center mb-6">
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      id={`otp-${index}`}
                      type="text"
                      maxLength="1"
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(index, e)}
                      disabled={isLoading}
                      className="w-12 h-14 text-center text-2xl font-bold bg-slate-700/50 border-2 border-slate-600 rounded-lg text-white focus:border-green-500 focus:ring-2 focus:ring-green-500/20 focus:outline-none transition-all disabled:opacity-50"
                    />
                  ))}
                </div>

                {/* Error Message */}
                {error && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2">
                    <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={18} />
                    <p className="text-red-200 text-sm">{error}</p>
                  </div>
                )}

                {/* Success Message */}
                {success && (
                  <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg flex items-start gap-2">
                    <CheckCircle className="text-green-400 flex-shrink-0 mt-0.5" size={18} />
                    <p className="text-green-200 text-sm">{success}</p>
                  </div>
                )}

                {/* Verify Button */}
                <button
                  onClick={() => handleVerify()}
                  disabled={isLoading || otp.some(digit => digit === '')}
                  className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-500/20"
                >
                  {isLoading ? 'Verifying...' : 'Verify Email'}
                </button>

                {/* Resend Link */}
                <div className="mt-6 text-center">
                  <p className="text-slate-400 text-sm mb-2">
                    Didn't receive the code?
                  </p>
                  <button
                    onClick={handleResend}
                    disabled={isLoading || resendCooldown > 0}
                    className="inline-flex items-center gap-2 text-green-400 hover:text-green-300 font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw size={16} />
                    {resendCooldown > 0 
                      ? `Resend in ${resendCooldown}s`
                      : 'Resend Code'
                    }
                  </button>
                </div>

                {/* Help Text */}
                <div className="mt-6 p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-xs text-center">
                    💡 <strong>Tip:</strong> Check your spam folder if you don't see the email. The code expires in 10 minutes.
                  </p>
                </div>
              </>
            )}

            {/* Success State */}
            {isVerified && (
              <div className="text-center py-8">
                <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="text-green-400" size={48} />
                </div>
                <p className="text-slate-300 mb-6">
                  You can now access all features of the SOC Dashboard
                </p>
                {onVerified && (
                  <button
                    onClick={onVerified}
                    className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all"
                  >
                    Continue
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer Info */}
        {!isVerified && (
          <div className="mt-6 text-center">
            <p className="text-slate-400 text-xs">
              Having trouble? Contact your system administrator
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailVerification;
