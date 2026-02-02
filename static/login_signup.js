document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const loginToggle = document.getElementById('loginToggle');
    const signupToggle = document.getElementById('signupToggle');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const toggleIndicator = document.querySelector('.toggle-indicator');
    const switchToSignup = document.getElementById('switchToSignup');
    const switchText = document.getElementById('switchText');
    const successMessage = document.getElementById('successMessage');
    
    // Password toggle buttons
    const toggleLoginPassword = document.getElementById('toggleLoginPassword');
    const toggleSignupPassword = document.getElementById('toggleSignupPassword');
    
    // Password strength elements
    const signupPassword = document.getElementById('signupPassword');
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');
    
    // Form states
    let isLoginForm = true;
    
    // Initialize
    initializeForms();
    
    function initializeForms() {
        // Set initial state
        loginForm.classList.add('active');
        loginToggle.classList.add('active');
        toggleIndicator.classList.add('active');
        updateToggleIndicator();
        
        // Set up event listeners
        loginToggle.addEventListener('click', () => switchToForm('login'));
        signupToggle.addEventListener('click', () => switchToForm('signup'));
        switchToSignup.addEventListener('click', (e) => {
            e.preventDefault();
            switchToForm('signup');
        });
        
        // Password toggle
        setupPasswordToggle(toggleLoginPassword, document.getElementById('loginPassword'));
        setupPasswordToggle(toggleSignupPassword, signupPassword);
        
        // Password strength
        signupPassword.addEventListener('input', checkPasswordStrength);
        
        // Form submissions
        loginForm.addEventListener('submit', handleLogin);
        signupForm.addEventListener('submit', handleSignup);
    }
    
    function switchToForm(formType) {
        if (formType === 'login' && isLoginForm) return;
        
        isLoginForm = formType === 'login';
        
        // Update toggle buttons
        if (isLoginForm) {
            loginToggle.classList.add('active');
            signupToggle.classList.remove('active');
            loginForm.classList.add('active');
            signupForm.classList.remove('active');
            switchText.innerHTML = 'Don\'t have an account? <a href="#" id="switchToSignup">Sign Up</a>';
        } else {
            signupToggle.classList.add('active');
            loginToggle.classList.remove('active');
            signupForm.classList.add('active');
            loginForm.classList.remove('active');
            switchText.innerHTML = 'Already have an account? <a href="#" id="switchToLogin">Login</a>';
        }
        
        // Update indicator position
        updateToggleIndicator();
        
        // Update switch link event
        const newSwitchLink = document.getElementById(isLoginForm ? 'switchToSignup' : 'switchToLogin');
        if (newSwitchLink) {
            newSwitchLink.addEventListener('click', (e) => {
                e.preventDefault();
                switchToForm(isLoginForm ? 'signup' : 'login');
            });
        }
        
        // Add fade animation
        const activeForm = document.querySelector('.form.active');
        activeForm.style.animation = 'none';
        activeForm.offsetHeight; // Trigger reflow
        activeForm.style.animation = 'fadeIn 0.4s ease';
    }
    
    function updateToggleIndicator() {
        if (isLoginForm) {
            toggleIndicator.style.transform = 'translateX(0)';
        } else {
            toggleIndicator.style.transform = 'translateX(100%)';
        }
    }
    
    function setupPasswordToggle(button, input) {
        if (!button || !input) return;
        
        button.addEventListener('click', function() {
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            
            const icon = this.querySelector('i');
            if (type === 'text') {
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    }
    
    function checkPasswordStrength() {
        const password = signupPassword.value;
        
        if (password.length === 0) {
            strengthFill.className = 'strength-fill';
            strengthText.textContent = 'Password strength';
            return;
        }
        
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
        
        // Update UI
        strengthFill.className = 'strength-fill';
        
        if (strength <= 2) {
            strengthFill.classList.add('weak');
            strengthText.textContent = 'Weak - Add ' + feedback.slice(0, 2).join(' and ');
        } else if (strength <= 4) {
            strengthFill.classList.add('medium');
            strengthText.textContent = 'Medium - Add ' + feedback[0];
        } else {
            strengthFill.classList.add('strong');
            strengthText.textContent = 'Strong password!';
        }
    }
    
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    function validatePassword(password) {
        return password.length >= 8;
    }
    
    function showError(input, message) {
        const wrapper = input.closest('.input-wrapper');
        if (wrapper) {
            wrapper.classList.add('error');
            
            // Add error message if not exists
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
    
    function clearError(input) {
        const wrapper = input.closest('.input-wrapper');
        if (wrapper) {
            wrapper.classList.remove('error');
            const errorMsg = wrapper.querySelector('.error-message');
            if (errorMsg) {
                errorMsg.remove();
            }
        }
    }
    
    async function handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail');
        const password = document.getElementById('loginPassword');
        let isValid = true;
        
        // Clear previous errors
        clearError(email);
        clearError(password);
        
        // Validate email
        if (!validateEmail(email.value)) {
            showError(email, 'Please enter a valid email address');
            isValid = false;
        }
        
        // Validate password
        if (!validatePassword(password.value)) {
            showError(password, 'Password must be at least 8 characters');
            isValid = false;
        }
        
        if (!isValid) return;
        
        const submitBtn = loginForm.querySelector('.submit-btn');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
        submitBtn.disabled = true;
        
        try {
            // Call the real login API
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: email.value.split('@')[0],  // Use part before @ as username
                    password: password.value
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Store token and username in localStorage
                localStorage.setItem('auth_token', data.token);
                // Store the username exactly as provided by the server
                localStorage.setItem('username', data.username);
                
                // Show success message
                showSuccess();
            } else {
                // Show error
                showError(email, data.detail || 'Login failed');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        } catch (error) {
            console.error('Login error:', error);
            showError(email, 'Connection error. Please try again.');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    async function handleSignup(e) {
        e.preventDefault();
        
        const name = document.getElementById('signupName');
        const email = document.getElementById('signupEmail');
        const password = document.getElementById('signupPassword');
        const confirmPassword = document.getElementById('signupConfirmPassword');
        const agreeTerms = document.getElementById('agreeTerms');
        let isValid = true;
        
        // Clear previous errors
        [name, email, password, confirmPassword].forEach(input => clearError(input));
        
        // Validate name
        if (name.value.trim().length < 2) {
            showError(name, 'Please enter your full name');
            isValid = false;
        }
        
        // Validate email
        if (!validateEmail(email.value)) {
            showError(email, 'Please enter a valid email address');
            isValid = false;
        }
        
        // Validate password
        if (!validatePassword(password.value)) {
            showError(password, 'Password must be at least 8 characters');
            isValid = false;
        }
        
        // Validate confirm password
        if (password.value !== confirmPassword.value) {
            showError(confirmPassword, 'Passwords do not match');
            isValid = false;
        }
        
        // Validate terms
        if (!agreeTerms.checked) {
            agreeTerms.closest('.checkbox-container').style.color = '#e74c3c';
            isValid = false;
        }
        
        if (!isValid) return;
        
        // Simulate signup - in production, this would call your API
        const submitBtn = signupForm.querySelector('.submit-btn');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
        submitBtn.disabled = true;
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Show success message
        showSuccess();
        
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
    
    function showSuccess() {
        successMessage.classList.add('show');
        
        // Redirect after 2 seconds
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }
    
    // Add shake animation style dynamically
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        .input-wrapper.error .input-icon {
            color: #e74c3c;
        }
        
        .input-wrapper.error input {
            border-color: #e74c3c;
        }
        
        .input-wrapper.error .input-border {
            background: #e74c3c;
        }
    `;
    document.head.appendChild(style);
});

