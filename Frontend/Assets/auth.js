// ========== CONFIGURATION ==========
const API_BASE_URL = 'http://localhost:8000';  // Change to your backend URL

// ========== ANIMATION HANDLING ==========
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const direction = params.get('dir');
    const card = document.querySelector('.auth-card');

    if (card) {
        if (direction === 'right') {
            card.classList.add('slide-in-right');
        } else if (direction === 'left') {
            card.classList.add('slide-in-left');
        } else {
            card.style.opacity = "1";
            card.style.transition = "opacity 0.5s ease";
        }
    }
});

// ========== FORM HANDLERS ==========
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

// ========== LOGIN HANDLER ==========
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;

    // Disable submit button
    const submitBtn = e.target.querySelector('.submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'LOGGING IN...';

    try {
        // Call FastAPI login endpoint
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Success!
            showMessage(data.message, 'success');
            
            // Store session
            if (rememberMe) {
                localStorage.setItem('aira_user', username);
            } else {
                sessionStorage.setItem('aira_user', username);
            }

            // Redirect after 1.5 seconds
            setTimeout(() => {
                window.location.href = 'Start.html';
            }, 1500);
        } else {
            // Error from backend
            showMessage(data.detail || 'Login failed', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'LOGIN';
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Connection error. Please check if backend is running.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'LOGIN';
    }
}

// ========== REGISTER HANDLER ==========
async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const dob = document.getElementById('dob').value;
    const password = document.getElementById('reg-password').value;
    const termsAccepted = document.getElementById('terms').checked;

    // Frontend validation
    if (!termsAccepted) {
        showMessage('You must agree to Terms & Conditions', 'error');
        return;
    }

    if (password.length < 6) {
        showMessage('Password must be at least 6 characters', 'error');
        return;
    }

    if (!/^\d{10}$/.test(phone)) {
        showMessage('Please enter a valid 10-digit phone number.', 'error');
        return;
    }

    // Validate age (must be at least 13)
    const birthDate = new Date(dob);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    if (age < 13) {
        showMessage('You must be at least 13 years old to register.', 'error');
        return;
    }

    // Disable submit button
    const submitBtn = e.target.querySelector('.submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'CREATING ACCOUNT...';

    try {
        // Call FastAPI register endpoint
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                email: email,
                phone: phone,
                dob: dob,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Success!
            showMessage(data.message, 'success');

            // Redirect to login page after 2 seconds
            setTimeout(() => {
                window.location.href = 'Login.html';
            }, 2000);
        } else {
            // Error from backend
            showMessage(data.detail || 'Registration failed', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'CREATE ACCOUNT';
        }
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('Connection error. Please check if backend is running on port 8000.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'CREATE ACCOUNT';
    }
}

// ========== MESSAGE DISPLAY ==========
function showMessage(text, type) {
    // Check if message div exists
    let messageDiv = document.getElementById('message');
    
    if (!messageDiv) {
        // Create message div if it doesn't exist
        messageDiv = document.createElement('div');
        messageDiv.id = 'message';
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 15px 30px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 9999;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        document.body.appendChild(messageDiv);
    }

    messageDiv.textContent = text;
    
    // Style based on type
    if (type === 'success') {
        messageDiv.style.background = '#10b981';
        messageDiv.style.color = 'white';
    } else {
        messageDiv.style.background = '#ef4444';
        messageDiv.style.color = 'white';
    }

    messageDiv.style.display = 'block';

    // Hide after 5 seconds
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// ========== SESSION CHECK (Optional) ==========
function checkSession() {
    const user = localStorage.getItem('aira_user') || sessionStorage.getItem('aira_user');
    return user;
}

// ========== PASSWORD STRENGTH INDICATOR (Optional) ==========
document.addEventListener('DOMContentLoaded', function() {
    const regPassword = document.getElementById('reg-password');
    if (regPassword) {
        regPassword.addEventListener('input', function() {
            const strength = calculatePasswordStrength(this.value);
            // You can add visual feedback here
            console.log('Password strength:', strength);
        });
    }
});

function calculatePasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    return strength;
}

// ========== UTILITY: Test Backend Connection ==========
async function testBackendConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/test`);
        const data = await response.json();
        console.log('✅ Backend connection successful:', data);
        return true;
    } catch (error) {
        console.error('❌ Backend connection failed:', error);
        console.log('Make sure FastAPI is running on http://localhost:8000');
        return false;
    }
}

// Auto-test connection on page load (for debugging)
document.addEventListener('DOMContentLoaded', () => {
    testBackendConnection();
});