document.addEventListener('DOMContentLoaded', function() {
    // Redirect if already authenticated
    if (Utils.isAuthenticated()) {
        window.location.href = 'dashboard.html';
        return;
    }

    // Form elements
    const signupForm = document.getElementById('signupForm');
    const signupBtn = document.getElementById('signupBtn');
    const signupBtnText = document.getElementById('signupBtnText');
    const formStatus = document.getElementById('formStatus');
    
    // Input elements
    const inputs = {
        firstName: document.getElementById('firstName'),
        lastName: document.getElementById('lastName'),
        middleName: document.getElementById('middleName'),
        email: document.getElementById('email'),
        phone: document.getElementById('phone'),
        address: document.getElementById('address'),
        password: document.getElementById('password'),
        confirmPassword: document.getElementById('confirmPassword')
    };

    // Password elements
    const togglePasswordBtn = document.getElementById('togglePassword');
    const toggleConfirmPasswordBtn = document.getElementById('toggleConfirmPassword');
    const passwordStrength = document.getElementById('passwordStrength');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    const requirements = document.getElementById('requirements');
    const passwordMatch = document.getElementById('passwordMatch');
    const passwordMismatch = document.getElementById('passwordMismatch');

    // Validation state
    let validationErrors = {};
    let passwordStrengthScore = 0;
    let passwordRequirements = {
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        special: false
    };

    // Password toggle functionality
    togglePasswordBtn.addEventListener('click', () => togglePassword(inputs.password, togglePasswordBtn));
    toggleConfirmPasswordBtn.addEventListener('click', () => togglePassword(inputs.confirmPassword, toggleConfirmPasswordBtn));

    // Real-time validation
    Object.keys(inputs).forEach(field => {
        inputs[field].addEventListener('input', () => validateField(field, inputs[field].value));
        inputs[field].addEventListener('blur', () => validateField(field, inputs[field].value));
    });

    // Form submission
    signupForm.addEventListener('submit', handleSignup);

    function togglePassword(input, button) {
        const type = input.type === 'password' ? 'text' : 'password';
        input.type = type;
        
        const icon = button.querySelector('i');
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
    }

    function validateField(field, value) {
        const errors = { ...validationErrors };

        switch (field) {
            case 'firstName':
                if (!value.trim()) {
                    errors.firstName = 'First name is required';
                } else if (value.trim().length < 2) {
                    errors.firstName = 'First name must be at least 2 characters';
                } else {
                    delete errors.firstName;
                }
                break;

            case 'lastName':
                if (!value.trim()) {
                    errors.lastName = 'Last name is required';
                } else if (value.trim().length < 2) {
                    errors.lastName = 'Last name must be at least 2 characters';
                } else {
                    delete errors.lastName;
                }
                break;

            case 'email':
                if (!value.trim()) {
                    errors.email = 'Email is required';
                } else if (!Utils.isValidEmail(value)) {
                    errors.email = 'Please enter a valid email address';
                } else {
                    delete errors.email;
                }
                break;

            case 'phone':
                if (value && !Utils.isValidPhone(value)) {
                    errors.phone = 'Please enter a valid phone number';
                } else {
                    delete errors.phone;
                }
                break;

            case 'password':
                validatePassword(value, errors);
                break;

            case 'confirmPassword':
                validateConfirmPassword(value, errors);
                break;

            default:
                if (value.trim()) {
                    delete errors[field];
                }
        }

        validationErrors = errors;
        updateFieldError(field);
        updateFormState();
    }

    function validatePassword(password, errors) {
        if (!password) {
            errors.password = 'Password is required';
            passwordStrength.classList.add('hidden');
            return;
        }

        // Show password strength indicator
        passwordStrength.classList.remove('hidden');

        // Check requirements
        passwordRequirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[^A-Za-z0-9]/.test(password)
        };

        // Calculate strength
        passwordStrengthScore = Object.values(passwordRequirements).filter(Boolean).length * 20;

        // Update UI
        updatePasswordStrengthUI();
        updatePasswordRequirementsUI();

        // Validate password strength
        if (passwordStrengthScore < 100) {
            const missing = [];
            if (!passwordRequirements.length) missing.push('at least 8 characters');
            if (!passwordRequirements.uppercase) missing.push('one uppercase letter');
            if (!passwordRequirements.lowercase) missing.push('one lowercase letter');
            if (!passwordRequirements.number) missing.push('one number');
            if (!passwordRequirements.special) missing.push('one special character');
            
            errors.password = `Password must contain ${missing.join(', ')}`;
        } else {
            delete errors.password;
        }
    }

    function validateConfirmPassword(confirmPassword, errors) {
        if (!confirmPassword) {
            errors.confirmPassword = 'Please confirm your password';
            passwordMatch.classList.add('hidden');
            passwordMismatch.classList.add('hidden');
        } else if (confirmPassword !== inputs.password.value) {
            errors.confirmPassword = 'Passwords do not match';
            passwordMatch.classList.add('hidden');
            passwordMismatch.classList.remove('hidden');
        } else if (passwordStrengthScore < 100) {
            errors.confirmPassword = 'Please create a stronger password first';
            passwordMatch.classList.add('hidden');
            passwordMismatch.classList.add('hidden');
        } else {
            delete errors.confirmPassword;
            passwordMatch.classList.remove('hidden');
            passwordMismatch.classList.add('hidden');
        }
    }

    function updatePasswordStrengthUI() {
        const colors = {
            0: 'bg-red-500',
            20: 'bg-red-500',
            40: 'bg-orange-500',
            60: 'bg-yellow-500',
            80: 'bg-blue-500',
            100: 'bg-green-500'
        };

        const texts = {
            0: 'Very Weak',
            20: 'Very Weak',
            40: 'Weak',
            60: 'Fair',
            80: 'Good',
            100: 'Excellent'
        };

        strengthBar.className = `h-1 rounded-full transition-all duration-300 ${colors[passwordStrengthScore]}`;
        strengthBar.style.width = `${passwordStrengthScore}%`;
        strengthText.textContent = texts[passwordStrengthScore];
        strengthText.className = `text-xs font-medium ${colors[passwordStrengthScore].replace('bg-', 'text-')}`;
    }

    function updatePasswordRequirementsUI() {
        Object.keys(passwordRequirements).forEach(req => {
            const element = document.getElementById(`req-${req}`);
            const icon = element.querySelector('i');
            const text = element.querySelector('span');
            
            if (passwordRequirements[req]) {
                icon.className = 'fas fa-check text-green-400';
                text.classList.remove('text-white/70');
                text.classList.add('text-green-400');
            } else {
                icon.className = 'fas fa-times text-red-400';
                text.classList.remove('text-green-400');
                text.classList.add('text-white/70');
            }
        });
    }

    function updateFieldError(field) {
        const errorElement = document.getElementById(`${field}Error`);
        const inputElement = inputs[field];
        
        if (validationErrors[field]) {
            if (errorElement) {
                errorElement.textContent = validationErrors[field];
                errorElement.classList.remove('hidden');
            }
            if (inputElement) {
                inputElement.classList.add('border-red-400');
            }
        } else {
            if (errorElement) {
                errorElement.classList.add('hidden');
            }
            if (inputElement) {
                inputElement.classList.remove('border-red-400');
                if (field === 'confirmPassword' && inputs.confirmPassword.value && inputs.password.value === inputs.confirmPassword.value) {
                    inputElement.classList.add('border-green-400');
                }
            }
        }
    }

    function updateFormState() {
        const isFormValid = isValidForm();
        
        if (isFormValid) {
            signupBtn.disabled = false;
            signupBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            signupBtnText.textContent = 'Create SafeGuard Account';
            formStatus.classList.add('hidden');
        } else {
            signupBtn.disabled = true;
            signupBtn.classList.add('opacity-50', 'cursor-not-allowed');
            signupBtnText.textContent = 'Complete Required Fields';
            formStatus.classList.remove('hidden');
        }
    }

    function isValidForm() {
        return (
            inputs.firstName.value.trim() &&
            inputs.lastName.value.trim() &&
            inputs.email.value.trim() &&
            inputs.password.value &&
            inputs.confirmPassword.value &&
            inputs.password.value === inputs.confirmPassword.value &&
            passwordStrengthScore === 100 &&
            Object.keys(validationErrors).length === 0
        );
    }

    async function handleSignup(e) {
        e.preventDefault();
        
        if (!isValidForm()) {
            Utils.showToast('Please fix all errors before submitting', 'error');
            return;
        }

        Utils.setLoading(signupBtn, true);
        
        try {
            // Prepare signup data
            const signupData = {
                firstName: inputs.firstName.value.trim(),
                lastName: inputs.lastName.value.trim(),
                middleName: inputs.middleName.value.trim() || undefined,
                email: inputs.email.value.trim(),
                phone: inputs.phone.value.trim() || undefined,
                address: inputs.address.value.trim() || undefined,
                password: inputs.password.value
            };

            // Make API request
            const response = await Utils.apiRequest('/auth/register', {
                method: 'POST',
                body: JSON.stringify(signupData)
            });

            // Save user data
            Utils.saveUserData(response.user);
            
            // Save auth token if provided
            if (response.access_token) {
                localStorage.setItem('authToken', response.access_token);
            }

            // Show success message
            Utils.showToast('🎉 Welcome to SafeGuard!', 'success');
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);

        } catch (error) {
            console.error('Signup error:', error);
            Utils.showToast(error.message || 'Registration failed. Please try again.', 'error');
        } finally {
            Utils.setLoading(signupBtn, false);
        }
    }
});

// Go to login page
function goToLogin() {
    window.location.href = 'index.html';
}
