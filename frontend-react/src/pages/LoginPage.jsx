import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import './LoginPage.css';

// Validation helpers
function validateUsername(username) {
    const trimmed = username.trim();
    if (!trimmed) return 'Username is required';
    if (trimmed.length < 3) return 'Username must be at least 3 characters';
    if (trimmed.length > 30) return 'Username must be 30 characters or less';
    if (!/^[a-zA-Z0-9._-]+$/.test(trimmed)) return 'Username can only contain letters, numbers, dots, underscores, and hyphens';
    if (/^[._-]/.test(trimmed)) return 'Username cannot start with a special character';
    return null;
}

function validatePassword(password) {
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (password.length > 64) return 'Password must be 64 characters or less';
    if (!/[A-Z]/.test(password)) return 'Password must contain at least one uppercase letter (A-Z)';
    if (!/[a-z]/.test(password)) return 'Password must contain at least one lowercase letter (a-z)';
    if (!/[0-9]/.test(password)) return 'Password must contain at least one number (0-9)';
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) return 'Password must contain at least one special character (!@#$%^&*...)';
    if (/\s/.test(password)) return 'Password cannot contain spaces';
    return null;
}

function validateEmail(email) {
    const trimmed = email.trim();
    if (!trimmed) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) return 'Please enter a valid email address';
    return null;
}

export default function LoginPage() {
    const { login } = useAuth();
    const [view, setView] = useState('login');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    // Login state
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    // Signup state
    const [signupEmail, setSignupEmail] = useState('');
    const [otpCode, setOtpCode] = useState('');
    const [newUsername, setNewUsername] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    // Password strength indicator
    const getPasswordStrength = (pw) => {
        if (!pw) return { level: 0, label: '', color: '' };
        let score = 0;
        if (pw.length >= 8) score++;
        if (pw.length >= 12) score++;
        if (/[A-Z]/.test(pw)) score++;
        if (/[a-z]/.test(pw)) score++;
        if (/[0-9]/.test(pw)) score++;
        if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pw)) score++;
        if (score <= 2) return { level: 1, label: 'Weak', color: '#ef4444' };
        if (score <= 4) return { level: 2, label: 'Medium', color: '#f59e0b' };
        if (score <= 5) return { level: 3, label: 'Strong', color: '#22c55e' };
        return { level: 4, label: 'Very Strong', color: '#709138' };
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        const trimUser = username.trim();
        const trimPass = password.trim();
        if (!trimUser) { setError('Please enter your username'); return; }
        if (!trimPass) { setError('Please enter your password'); return; }
        setLoading(true);
        try {
            const res = await axios.post(`/api/auth/login`, { username: trimUser, password: trimPass });
            if (res.data.success) {
                login(res.data.username || trimUser);
            } else {
                setError(res.data.message || 'Invalid credentials');
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Login failed. Is the backend running on port 8000?';
            setError(msg);
        }
        setLoading(false);
    };

    const handleSendOTP = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        const emailErr = validateEmail(signupEmail);
        if (emailErr) { setError(emailErr); return; }
        setLoading(true);
        try {
            const res = await axios.post(`/api/auth/send-otp`, { email: signupEmail.trim() });
            if (res.data.success) {
                setView('signup-otp');
                setSuccess(res.data.message);
            } else {
                setError(res.data.message || 'Failed to send OTP');
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Failed to send OTP. Is the backend running?';
            setError(msg);
        }
        setLoading(false);
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        const trimCode = otpCode.trim();
        if (!trimCode) { setError('Please enter the verification code'); return; }
        if (trimCode.length !== 6) { setError('Code must be exactly 6 digits'); return; }
        if (!/^\d{6}$/.test(trimCode)) { setError('Code must contain only numbers'); return; }
        setLoading(true);
        try {
            const res = await axios.post(`/api/auth/verify-otp`, { email: signupEmail.trim(), code: trimCode });
            if (res.data.success) {
                setSuccess('Email Verified!');
                setView('signup-create');
            } else {
                setError(res.data.message || 'Invalid code');
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Verification failed';
            setError(msg);
        }
        setLoading(false);
    };

    const handleChangeEmail = () => {
        setView('signup-email');
        setSignupEmail('');
        setOtpCode('');
        setError('');
        setSuccess('');
    };

    const handleCreateAccount = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        // Validate username
        const userErr = validateUsername(newUsername);
        if (userErr) { setError(userErr); return; }
        // Validate password
        const passErr = validatePassword(newPassword);
        if (passErr) { setError(passErr); return; }
        // Confirm match
        if (newPassword !== confirmPassword) { setError('Passwords do not match'); return; }
        setLoading(true);
        try {
            const res = await axios.post(`/api/auth/register`, { username: newUsername.trim(), password: newPassword, email: signupEmail.trim() });
            if (res.data.success) {
                setSuccess('Registration Complete! Please login.');
                setView('login');
                setUsername(newUsername.trim());
            } else {
                setError(res.data.message || 'Registration failed');
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Registration failed';
            setError(msg);
        }
        setLoading(false);
    };

    const strength = getPasswordStrength(newPassword);

    return (
        <div className="auth-page">
            {/* Header */}
            <div className="auth-header">
                <img src="/logo.png" alt="ThirdEye" className="auth-logo" />
                <h1 className="auth-title">Intrusion Detection</h1>
                <p className="auth-subtitle">Next-generation surveillance & monitoring</p>
            </div>

            {/* LOGIN */}
            {view === 'login' && (
                <>
                    <div className="auth-card">
                        <div className="auth-card-title">🔐 Welcome Back</div>
                        {error && <div className="auth-error">{error}</div>}
                        {success && <div className="auth-success">{success}</div>}
                        <form onSubmit={handleLogin} autoComplete="off">
                            <div className="form-group">
                                <label>Username</label>
                                <input type="text" value={username} onChange={e => setUsername(e.target.value)} autoComplete="off" spellCheck="false" />
                            </div>
                            <div className="form-group">
                                <label>Password</label>
                                <div className="password-wrapper">
                                    <input type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" />
                                    <button type="button" className="eye-btn" onClick={() => setShowPassword(!showPassword)}>
                                        {showPassword ? '🙈' : '👁'}
                                    </button>
                                </div>
                            </div>
                            <button type="submit" className="auth-btn" disabled={loading}>{loading ? 'Signing in...' : 'Sign In Securely'}</button>
                        </form>
                    </div>
                    <div className="auth-footer">
                        <p className="auth-footer-text">New to the system?</p>
                        <button className="auth-btn auth-btn-secondary" onClick={() => { setView('signup-email'); setError(''); setSuccess(''); }}>
                            Create Management Account
                        </button>
                    </div>
                </>
            )}

            {/* SIGNUP STEP 1: Email */}
            {view === 'signup-email' && (
                <>
                    <div className="auth-card">
                        <div className="auth-card-title">🔐 Verify Email</div>
                        {error && <div className="auth-error">{error}</div>}
                        {success && <div className="auth-success">{success}</div>}
                        <form onSubmit={handleSendOTP} autoComplete="off">
                            <div className="form-group">
                                <label className="label-green">Email Address</label>
                                <input type="email" value={signupEmail} onChange={e => setSignupEmail(e.target.value)} placeholder="your.name@example.com" autoComplete="off" />
                            </div>
                            <button type="submit" className="auth-btn" disabled={loading}>{loading ? 'Sending...' : 'Send Verification Code'}</button>
                        </form>
                    </div>
                    <div className="auth-footer">
                        <p className="auth-footer-text">Already registered?</p>
                        <button className="auth-btn auth-btn-secondary" onClick={() => { setView('login'); setError(''); setSuccess(''); }}>
                            Return to Secure Login
                        </button>
                    </div>
                </>
            )}

            {/* SIGNUP STEP 2: OTP */}
            {view === 'signup-otp' && (
                <>
                    <div className="auth-card">
                        <div className="auth-card-title">🔢 Verify Code</div>
                        <p className="otp-sent-text">Code sent to: <a href={`mailto:${signupEmail}`}>{signupEmail}</a></p>
                        {error && <div className="auth-error">{error}</div>}
                        {success && <div className="auth-success">{success}</div>}
                        <form onSubmit={handleVerifyOTP} autoComplete="off">
                            <div className="form-group">
                                <label>Enter 6-Digit Code</label>
                                <input type="text" value={otpCode} onChange={e => setOtpCode(e.target.value.replace(/\D/g, ''))} maxLength={6} placeholder="••••••" autoComplete="one-time-code" inputMode="numeric" />
                            </div>
                            <div className="btn-row">
                                <button type="submit" className="auth-btn" disabled={loading}>{loading ? 'Verifying...' : 'Verify Email'}</button>
                                <button type="button" className="auth-btn" onClick={handleChangeEmail}>Change Email</button>
                            </div>
                        </form>
                    </div>
                    <div className="auth-footer">
                        <p className="auth-footer-text">Already registered?</p>
                        <button className="auth-btn auth-btn-secondary" onClick={() => { setView('login'); setError(''); setSuccess(''); }}>
                            Return to Secure Login
                        </button>
                    </div>
                </>
            )}

            {/* SIGNUP STEP 3: Account Details */}
            {view === 'signup-create' && (
                <>
                    <div className="auth-card">
                        <div className="auth-card-title">📝 Account Details</div>
                        <div className="verified-email-info">✅ Verified Email: {signupEmail}</div>
                        {error && <div className="auth-error">{error}</div>}
                        {success && <div className="auth-success">{success}</div>}
                        <form onSubmit={handleCreateAccount} autoComplete="off">
                            <div className="form-group">
                                <label>Choose Username</label>
                                <input type="text" value={newUsername} onChange={e => setNewUsername(e.target.value)} placeholder="e.g. jdoe (min 3 chars, letters/numbers only)" autoComplete="off" spellCheck="false" />
                                <small className="field-hint">3-30 characters. Letters, numbers, dots, underscores, hyphens only.</small>
                            </div>
                            <div className="form-group">
                                <label>Choose Password</label>
                                <div className="password-wrapper">
                                    <input type={showNewPassword ? 'text' : 'password'} value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Min 8 chars, upper+lower+number+special" autoComplete="new-password" />
                                    <button type="button" className="eye-btn" onClick={() => setShowNewPassword(!showNewPassword)}>
                                        {showNewPassword ? '🙈' : '👁'}
                                    </button>
                                </div>
                                {newPassword && (
                                    <div className="password-strength">
                                        <div className="strength-bar">
                                            <div className="strength-fill" style={{ width: `${strength.level * 25}%`, background: strength.color }}></div>
                                        </div>
                                        <small style={{ color: strength.color, fontWeight: 600 }}>{strength.label}</small>
                                    </div>
                                )}
                                <small className="field-hint">Min 8 chars: 1 uppercase, 1 lowercase, 1 number, 1 special character</small>
                            </div>
                            <div className="form-group">
                                <label>Confirm Password</label>
                                <div className="password-wrapper">
                                    <input type={showConfirmPassword ? 'text' : 'password'} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Repeat password" autoComplete="new-password" />
                                    <button type="button" className="eye-btn" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                                        {showConfirmPassword ? '🙈' : '👁'}
                                    </button>
                                </div>
                                {confirmPassword && newPassword && confirmPassword !== newPassword && (
                                    <small className="field-error">Passwords do not match</small>
                                )}
                                {confirmPassword && newPassword && confirmPassword === newPassword && (
                                    <small className="field-match">✅ Passwords match</small>
                                )}
                            </div>
                            <button type="submit" className="auth-btn" disabled={loading}>{loading ? 'Creating...' : 'Complete Registration'}</button>
                        </form>
                    </div>
                    <div className="auth-footer">
                        <p className="auth-footer-text">Already registered?</p>
                        <button className="auth-btn auth-btn-secondary" onClick={() => { setView('login'); setError(''); setSuccess(''); }}>
                            Return to Secure Login
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
