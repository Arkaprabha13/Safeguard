document.addEventListener('DOMContentLoaded', function() {
    // Redirect if already authenticated
    if (Utils.isAuthenticated()) {
        window.location.href = 'dashboard.html';
        return;
    }

    // Form elements
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('togglePassword');
    const loginBtn = document.getElementById('loginBtn');
    
    // Error elements
    const emailError = document.getElementById('emailError');
    const passwordError = document.getElementById('passwordError');

    // Toggle password visibility
    togglePasswordBtn.addEventListener('click', function() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        
        const icon = this.querySelector('i');
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
    });

    // Real-time validation
    emailInput.addEventListener('blur', validateEmail);
    passwordInput.addEventListener('blur', validatePassword);

    // Social login buttons
    document.querySelectorAll('.social-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const provider = this.dataset.provider;
            Utils.showToast(`${provider} login will be available soon`, 'info');
        });
    });

    // Form submission
    loginForm.addEventListener('submit', handleLogin);

    function validateEmail() {
        const email = emailInput.value.trim();
        
        if (!email) {
            showFieldError(emailError, 'Email is required');
            return false;
        }
        
        if (!Utils.isValidEmail(email)) {
            showFieldError(emailError, 'Please enter a valid email address');
            return false;
        }
        
        hideFieldError(emailError);
        return true;
    }

    function validatePassword() {
        const password = passwordInput.value;
        
        if (!password) {
            showFieldError(passwordError, 'Password is required');
            return false;
        }
        
        hideFieldError(passwordError);
        return true;
    }

    function showFieldError(errorElement, message) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        errorElement.previousElementSibling.classList.add('border-red-400');
    }

    function hideFieldError(errorElement) {
        errorElement.classList.add('hidden');
        errorElement.previousElementSibling.classList.remove('border-red-400');
    }

    async function handleLogin(e) {
        e.preventDefault();
        
        // Validate form
        const isEmailValid = validateEmail();
        const isPasswordValid = validatePassword();
        
        if (!isEmailValid || !isPasswordValid) {
            Utils.showToast('Please fix all errors before submitting', 'error');
            return;
        }

        // Show loading state
        Utils.setLoading(loginBtn, true);
        
        try {
            // Prepare login data
            const loginData = {
                email: emailInput.value.trim(),
                password: passwordInput.value
            };

            // Make API request
            const response = await Utils.apiRequest('/auth/login', {
                method: 'POST',
                body: JSON.stringify(loginData)
            });

            // Save user data
            Utils.saveUserData(response.user);
            
            // Save auth token if provided
            if (response.access_token) {
                localStorage.setItem('authToken', response.access_token);
            }

            // Show success message
            Utils.showToast('🎉 Welcome back!', 'success');
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);

        } catch (error) {
            console.error('Login error:', error);
            Utils.showToast(error.message || 'Login failed. Please try again.', 'error');
        } finally {
            Utils.setLoading(loginBtn, false);
        }
    }
});
