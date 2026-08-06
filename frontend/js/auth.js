// Authentication Logic

const auth = {
    /**
     * Initializes authentication page listeners and UI toggles
     */
    init() {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');

        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }

        if (registerForm) {
            registerForm.addEventListener('submit', this.handleRegister.bind(this));
        }

        this.initPasswordToggles();
    },

    /**
     * Attaches click events to password visibility toggle icons.
     */
    initPasswordToggles() {
        const toggles = document.querySelectorAll('.password-toggle');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                // The toggle icon is a sibling to the input
                const input = e.target.closest('.relative').querySelector('input');
                if (input.type === 'password') {
                    input.type = 'text';
                    e.target.classList.remove('fa-eye');
                    e.target.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    e.target.classList.remove('fa-eye-slash');
                    e.target.classList.add('fa-eye');
                }
            });
        });
    },

    /**
     * Helper to validate email format using standard regex.
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Handles the login form submission
     */
    async handleLogin(event) {
        event.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const submitBtn = document.getElementById('login-btn');

        if (!email || !password) {
            utils.showNotification('Please fill in all fields.', 'error');
            return;
        }

        if (!this.isValidEmail(email)) {
            utils.showNotification('Please enter a valid email address.', 'error');
            return;
        }

        try {
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Logging in...';

            // Call API - mapping email to 'username' field for FastAPI OAuth2 spec
            const credentials = {
                email: email,
                password: password
            };

            const data = await api.login(credentials);
            
            if (data && data.access_token) {
                // 1. Save JWT
                storage.setToken(data.access_token);
                
                // 2. Call getCurrentUser
                const user = await api.getCurrentUser();
                
                // 3. Save user
                storage.setUser(user);
                
                // 4. Redirect to Dashboard (or the originally requested URL)
                router.checkAuth(); 
            } else {
                throw new Error("Invalid response from server.");
            }
        } catch (error) {
            utils.showNotification(error.message || 'Login failed. Please check your credentials.', 'error');
        } finally {
            // Always restore button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Sign In';
        }
    },

    /**
     * Handles the registration form submission
     */
    async handleRegister(event) {
        event.preventDefault();
        
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const submitBtn = document.getElementById('register-btn');

        if (!name || !email || !password || !confirmPassword) {
            utils.showNotification('Please fill in all fields.', 'error');
            return;
        }

        if (!this.isValidEmail(email)) {
            utils.showNotification('Please enter a valid email address.', 'error');
            return;
        }

        if (password.length < 8) {
            utils.showNotification('Password must be at least 8 characters long.', 'error');
            return;
        }

        if (password !== confirmPassword) {
            utils.showNotification('Passwords do not match.', 'error');
            return;
        }

        try {
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account...';

            const userData = {
                full_name: name,
                email: email,
                password: password
            };

            await api.register(userData);
            
            utils.showNotification('Registration successful! Please sign in.', 'success');
            router.navigate(CONSTANTS.ROUTES.LOGIN);
            
        } catch (error) {
            utils.showNotification(error.message || 'Registration failed. Please try again.', 'error');
        } finally {
            // Restore button state in case of error (success redirects)
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Create Account';
        }
    }
};

// Initialize listeners on DOM load
document.addEventListener('DOMContentLoaded', () => {
    auth.init();
});
