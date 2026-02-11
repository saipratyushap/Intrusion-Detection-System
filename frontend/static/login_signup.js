/**
 * JWT Authentication Frontend Module
 * Handles login, signup, token management, and API requests with JWT
 */

// JWT Configuration
const JWT_CONFIG = {
    ACCESS_TOKEN_KEY: 'jwt_access_token',
    REFRESH_TOKEN_KEY: 'jwt_refresh_token',
    TOKEN_EXPIRY_KEY: 'jwt_token_expiry',
    USERNAME_KEY: 'jwt_username',
    USER_ROLE_KEY: 'jwt_user_role',
    USER_PERMISSIONS_KEY: 'jwt_user_permissions'
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function () {
    console.log('[JWT Auth] Initializing JWT module...');

    // Initialize JWT module
    initializeJWTModule();

    // Set up form handlers
    initializeForms();

    // Check if user is already logged in
    checkAuthStatus();

    console.log('[JWT Auth] Module initialized successfully');
});

/**
 * Initialize JWT authentication module
 */
function initializeJWTModule() {
    // Clean up old tokens if present
    cleanupOldTokens();

    // Set up token refresh interval
    setInterval(async () => {
        await refreshTokenIfNeeded();
    }, 60000); // Check every minute

    // Set up logout handler for page unload
    window.addEventListener('beforeunload', () => {
        // Don't logout on refresh, just ensure token is valid
    });

    console.log('[JWT Auth] Module initialized');
}

/**
 * Clean up old token formats
 */
function cleanupOldTokens() {
    const oldToken = localStorage.getItem('auth_token');
    if (oldToken && !oldToken.includes('.')) {
        // This is the old token format, remove it
        localStorage.removeItem('auth_token');
        localStorage.removeItem('username');
        console.log('[JWT Auth] Cleaned up old token format');
    }
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    const token = getAccessToken();
    if (!token) {
        console.log('[JWT Auth] No access token found');
        return false;
    }

    // Check if token is expired
    const expiry = localStorage.getItem(JWT_CONFIG.TOKEN_EXPIRY_KEY);
    if (!expiry) {
        console.log('[JWT Auth] No token expiry found');
        return false;
    }

    const isAuth = Date.now() < parseInt(expiry);
    console.log('[JWT Auth] Authentication check:', isAuth ? 'authenticated' : 'expired');
    return isAuth;
}

/**
 * Get access token from storage
 */
function getAccessToken() {
    return localStorage.getItem(JWT_CONFIG.ACCESS_TOKEN_KEY);
}

/**
 * Get refresh token from storage
 */
function getRefreshToken() {
    return localStorage.getItem(JWT_CONFIG.REFRESH_TOKEN_KEY);
}

/**
 * Store tokens securely
 */
function storeTokens(accessToken, refreshToken, expiresIn) {
    const now = Date.now();
    localStorage.setItem(JWT_CONFIG.ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(JWT_CONFIG.REFRESH_TOKEN_KEY, refreshToken || '');
    localStorage.setItem(JWT_CONFIG.TOKEN_EXPIRY_KEY, String(now + (expiresIn * 1000)));
}

/**
 * Store user info
 */
function storeUserInfo(username, role, permissions) {
    localStorage.setItem(JWT_CONFIG.USERNAME_KEY, username);
    localStorage.setItem(JWT_CONFIG.USER_ROLE_KEY, role);
    localStorage.setItem(JWT_CONFIG.USER_PERMISSIONS_KEY, JSON.stringify(permissions));
}

/**
 * Get stored user info
 */
function getUserInfo() {
    return {
        username: localStorage.getItem(JWT_CONFIG.USERNAME_KEY),
        role: localStorage.getItem(JWT_CONFIG.USER_ROLE_KEY),
        permissions: JSON.parse(localStorage.getItem(JWT_CONFIG.USER_PERMISSIONS_KEY) || '[]')
    };
}

/**
 * Clear all auth data
 */
function clearAuthData() {
    localStorage.removeItem(JWT_CONFIG.ACCESS_TOKEN_KEY);
    localStorage.removeItem(JWT_CONFIG.REFRESH_TOKEN_KEY);
    localStorage.removeItem(JWT_CONFIG.TOKEN_EXPIRY_KEY);
    localStorage.removeItem(JWT_CONFIG.USERNAME_KEY);
    localStorage.removeItem(JWT_CONFIG.USER_ROLE_KEY);
    localStorage.removeItem(JWT_CONFIG.USER_PERMISSIONS_KEY);
}

/**
 * Check authentication status and update UI
 */
async function checkAuthStatus() {
    if (isAuthenticated()) {
        // Update UI to show logged in state
        updateUIForAuthenticated();

        // Refresh token if needed (within 5 minutes of expiry)
        const expiry = localStorage.getItem(JWT_CONFIG.TOKEN_EXPIRY_KEY);
        if (expiry && (parseInt(expiry) - Date.now()) < 300000) {
            await refreshTokenIfNeeded();
        }
    } else {
        clearAuthData();
        updateUIForUnauthenticated();
    }
}

/**
 * Update UI for authenticated user
 */
function updateUIForAuthenticated() {
    const userInfo = getUserInfo();
    console.log('User authenticated:', userInfo.username);
}

/**
 * Update UI for unauthenticated user
 */
function updateUIForUnauthenticated() {
    console.log('User not authenticated');
}

/**
 * Refresh token if needed
 */
async function refreshTokenIfNeeded() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            storeTokens(data.access_token, data.refresh_token, data.expires_in);

            const userInfo = getUserInfo();
            storeUserInfo(userInfo.username, userInfo.role, userInfo.permissions);

            return true;
        } else {
            // Refresh failed, user needs to login again
            logout();
            return false;
        }
    } catch (error) {
        console.error('Token refresh error:', error);
        return false;
    }
}

/**
 * Make authenticated API request
 */
async function authenticatedFetch(url, options = {}) {
    // Get current token (try refresh first)
    if (!isAuthenticated()) {
        await refreshTokenIfNeeded();
    }

    const token = getAccessToken();

    // Set default headers
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    // If unauthorized, try refresh once
    if (response.status === 401) {
        const refreshed = await refreshTokenIfNeeded();
        if (refreshed) {
            // Retry with new token
            const newToken = getAccessToken();
            headers['Authorization'] = `Bearer ${newToken}`;
            return fetch(url, {
                ...options,
                headers
            });
        } else {
            // Logout user
            logout();
            throw new Error('Session expired. Please login again.');
        }
    }

    return response;
}

// =============================================================================
// Form Handling
// =============================================================================

function initializeForms() {
    const loginToggle = document.getElementById('loginToggle');
    const signupToggle = document.getElementById('signupToggle');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const toggleIndicator = document.querySelector('.toggle-indicator');

    // Password toggle buttons
    const toggleLoginPassword = document.getElementById('toggleLoginPassword');
    const toggleSignupPassword = document.getElementById('toggleSignupPassword');

    // Password strength elements
    const signupPassword = document.getElementById('signupPassword');
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');

    let isLoginForm = true;

    // Set initial state
    if (loginForm) loginForm.classList.add('active');
    if (loginToggle) loginToggle.classList.add('active');
    if (toggleIndicator) toggleIndicator.classList.add('active');

    // Form switching
    if (loginToggle) {
        loginToggle.addEventListener('click', () => {
            if (!isLoginForm) {
                isLoginForm = true;
                if (loginForm) loginForm.classList.add('active');
                if (signupForm) signupForm.classList.remove('active');
                if (loginToggle) loginToggle.classList.add('active');
                if (signupToggle) signupToggle.classList.remove('active');
                updateToggleIndicator();
            }
        });
    }

    if (signupToggle) {
        signupToggle.addEventListener('click', () => {
            if (isLoginForm) {
                isLoginForm = false;
                if (signupForm) signupForm.classList.add('active');
                if (loginForm) loginForm.classList.remove('active');
                if (signupToggle) signupToggle.classList.add('active');
                if (loginToggle) loginToggle.classList.remove('active');
                updateToggleIndicator();
            }
        });
    }

    function updateToggleIndicator() {
        if (toggleIndicator) {
            toggleIndicator.style.transform = isLoginForm ? 'translateX(0)' : 'translateX(100%)';
        }
    }

    // Password visibility toggle
    function setupPasswordToggle(button, input) {
        if (!button || !input) return;

        button.addEventListener('click', function () {
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);

            const icon = this.querySelector('i');
            if (icon) {
                if (type === 'text') {
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            }
        });
    }

    setupPasswordToggle(toggleLoginPassword, document.getElementById('loginPassword'));
    setupPasswordToggle(toggleSignupPassword, signupPassword);

    // Password strength checker
    if (signupPassword) {
        signupPassword.addEventListener('input', function () {
            const password = this.value;

            if (strengthFill) strengthFill.className = 'strength-fill';
            if (strengthText) strengthText.textContent = 'Password strength';

            if (password.length === 0) return;

            let strength = 0;
            let feedback = [];

            // Length check
            if (password.length >= 8) strength++;
            else feedback.push('at least 8 characters');

            // Uppercase check
            if (/[A-Z]/.test(password)) strength++;
            else feedback.push('uppercase letter');

            // Lowercase check
            if (/[a-z]/.test(password)) strength++;
            else feedback.push('lowercase letter');

            // Number check
            if (/[0-9]/.test(password)) strength++;
            else feedback.push('a number');

            // Special character check
            if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
            else feedback.push('special character');

            if (strengthFill) {
                if (strength <= 2) {
                    strengthFill.classList.add('weak');
                } else if (strength <= 4) {
                    strengthFill.classList.add('medium');
                } else {
                    strengthFill.classList.add('strong');
                }
            }

            if (strengthText) {
                if (strength <= 2) {
                    strengthText.textContent = 'Weak - Add ' + feedback.slice(0, 2).join(' and ');
                } else if (strength <= 4) {
                    strengthText.textContent = 'Medium - Add ' + feedback[0];
                } else {
                    strengthText.textContent = 'Strong password!';
                }
            }
        });
    }

    // Form submissions
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleLogin(e.target);
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleSignup(e.target);
        });
    }

    // Add shake animation style
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Handle login form submission
 */
async function handleLogin(form) {
    const email = document.getElementById('loginEmail');
    const password = document.getElementById('loginPassword');
    const submitBtn = form.querySelector('.submit-btn');

    console.log('[JWT Auth] Login attempt for:', email.value);

    // Validate
    if (!validateEmail(email.value)) {
        showError(email, 'Please enter a valid email address');
        return;
    }

    if (password.value.length < 8) {
        showError(password, 'Password must be at least 8 characters');
        return;
    }

    // Show loading state
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
    submitBtn.disabled = true;

    try {
        // Extract username from email (e.g., user@example.com -> user)
        const username = email.value.split('@')[0];
        console.log('[JWT Auth] Extracted username:', username);

        // Make login request
        console.log('[JWT Auth] Sending login request to /api/auth/login...');
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password.value
            })
        });

        console.log('[JWT Auth] Login response status:', response.status);
        const data = await response.json();
        console.log('[JWT Auth] Login response data:', data);

        if (response.ok && data.access_token) {
            // Store tokens
            console.log('[JWT Auth] Storing tokens...');
            storeTokens(data.access_token, data.refresh_token, data.expires_in);

            // Store user info
            const userInfo = data.username || username;
            storeUserInfo(userInfo, 'user', []);
            console.log('[JWT Auth] User info stored:', userInfo);

            // Show success
            showSuccess('Login successful! Redirecting...');
            console.log('[JWT Auth] Login successful, redirecting to /data...');

            // Redirect after delay
            setTimeout(() => {
                window.location.href = '/data';
            }, 1000);
        } else {
            console.error('[JWT Auth] Login failed:', data.detail || 'Unknown error');
            showError(email, data.detail || 'Login failed');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    } catch (error) {
        console.error('[JWT Auth] Login error:', error);
        showError(email, 'Connection error. Please try again.');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

/**
 * Handle signup form submission
 */
async function handleSignup(form) {
    const name = document.getElementById('signupName');
    const email = document.getElementById('signupEmail');
    const password = document.getElementById('signupPassword');
    const confirmPassword = document.getElementById('signupConfirmPassword');
    const agreeTerms = document.getElementById('agreeTerms');
    const submitBtn = form.querySelector('.submit-btn');

    console.log('[JWT Auth] Signup attempt for:', email.value);

    // Validate
    if (name.value.trim().length < 2) {
        showError(name, 'Please enter your full name');
        return;
    }

    if (!validateEmail(email.value)) {
        showError(email, 'Please enter a valid email address');
        return;
    }

    if (password.value.length < 8) {
        showError(password, 'Password must be at least 8 characters');
        return;
    }

    if (password.value !== confirmPassword.value) {
        showError(confirmPassword, 'Passwords do not match');
        return;
    }

    if (!agreeTerms.checked) {
        agreeTerms.closest('.checkbox-container').style.color = '#e74c3c';
        return;
    }

    // Show loading state
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
    submitBtn.disabled = true;

    try {
        // Make signup request
        console.log('[JWT Auth] Sending signup request to /api/auth/signup...');
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: name.value.trim(),
                password: password.value,
                email: email.value
            })
        });

        console.log('[JWT Auth] Signup response status:', response.status);
        const data = await response.json();
        console.log('[JWT Auth] Signup response data:', data);

        if (response.ok && data.access_token) {
            // Store tokens
            console.log('[JWT Auth] Storing tokens...');
            storeTokens(data.access_token, data.refresh_token, data.expires_in);

            // Store user info
            const userInfo = data.username || name.value.trim();
            storeUserInfo(userInfo, 'user', []);
            console.log('[JWT Auth] User info stored:', userInfo);

            // Show success
            showSuccess('Account created! Redirecting...');
            console.log('[JWT Auth] Signup successful, redirecting to /data...');

            // Redirect after delay
            setTimeout(() => {
                window.location.href = '/data';
            }, 1000);
        } else {
            console.error('[JWT Auth] Signup failed:', data.detail || 'Unknown error');
            showError(name, data.detail || 'Signup failed');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    } catch (error) {
        console.error('[JWT Auth] Signup error:', error);
        showError(name, 'Connection error. Please try again.');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

/**
 * Validate email format
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Show error message
 */
function showError(input, message) {
    const wrapper = input.closest('.input-wrapper');
    if (wrapper) {
        wrapper.classList.add('error');

        let errorMsg = wrapper.querySelector('.error-message');
        if (!errorMsg) {
            errorMsg = document.createElement('span');
            errorMsg.className = 'error-message';
            errorMsg.style.cssText = 'color: #e74c3c; font-size: 12px; position: absolute; bottom: -20px; left: 5px;';
            wrapper.appendChild(errorMsg);
        }
        errorMsg.textContent = message;

        // Shake animation
        input.style.animation = 'none';
        input.offsetHeight;
        input.style.animation = 'shake 0.5s ease';
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    const successMessage = document.getElementById('successMessage');
    const successText = document.querySelector('.success-text');

    if (successMessage) {
        successMessage.classList.add('show');
    }

    if (successText) {
        successText.textContent = message;
    }
}

/**
 * Logout user
 */
async function logout() {
    console.log('[JWT Auth] Logging out...');

    try {
        const token = getAccessToken();
        if (token) {
            console.log('[JWT Auth] Sending logout request to server...');
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
        }
    } catch (error) {
        console.error('[JWT Auth] Logout error:', error);
    } finally {
        clearAuthData();
        console.log('[JWT Auth] Redirecting to /login...');
        window.location.href = '/login';
    }
}

// Export functions for use in other scripts
window.JWTAuth = {
    isAuthenticated,
    getAccessToken,
    getRefreshToken,
    getUserInfo,
    logout,
    authenticatedFetch,
    refreshTokenIfNeeded
};

