// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    
    // Check which page we're on
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // Login Form Handler
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Register Form Handler
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

// Handle Login
function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;

    // Get stored users
    const users = getUsers();

    // Find user
    const user = users.find(u => u.username === username);

    if (!user) {
        showMessage('User not found. Please check your username or sign up.', 'error');
        return;
    }

    if (user.password !== password) {
        showMessage('Incorrect password. Please try again.', 'error');
        return;
    }

    // Successful login
    showMessage('Login successful! Redirecting...', 'success');
    
    // Store session
    sessionStorage.setItem('currentUser', user.username);
    
    if (rememberMe) {
        localStorage.setItem('rememberUser', user.username);
    }

    // Redirect to home page after 1.5 seconds
    setTimeout(() => {
        window.location.href = 'home.html';
    }, 1500);
}

// Handle Registration
function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const dob = document.getElementById('dob').value;
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // Validation
    if (password !== confirmPassword) {
        showMessage('Passwords do not match!', 'error');
        return;
    }

    // Check if username already exists
    const users = getUsers();
    if (users.find(u => u.username === username)) {
        showMessage('Username already exists. Please choose another.', 'error');
        return;
    }

    // Check if email already exists
    if (users.find(u => u.email === email)) {
        showMessage('Email already registered. Please use another email.', 'error');
        return;
    }

    // Validate phone number (10 digits)
    if (!/^\d{10}$/.test(phone)) {
        showMessage('Please enter a valid 10-digit phone number.', 'error');
        return;
    }

    // Validate age (must be at least 13 years old)
    const birthDate = new Date(dob);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    if (age < 13) {
        showMessage('You must be at least 13 years old to register.', 'error');
        return;
    }

    // Create new user
    const newUser = {
        username,
        email,
        phone,
        dob,
        password,
        createdAt: new Date().toISOString()
    };

    // Save user
    users.push(newUser);
    saveUsers(users);

    showMessage('Registration successful! Redirecting to login...', 'success');

    // Redirect to login page after 2 seconds
    setTimeout(() => {
        window.location.href = 'index.html';
    }, 2000);
}

// Storage Functions - Using sessionStorage for persistence

function getUsers() {
    const usersData = sessionStorage.getItem('registeredUsers');
    return usersData ? JSON.parse(usersData) : [];
}

function saveUsers(users) {
    sessionStorage.setItem('registeredUsers', JSON.stringify(users));
}

function storeSession(username) {
    // Store session info
    sessionStorage.setItem('currentUser', username);
    console.log('Session stored for:', username);
}

// Show Message Helper
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = 'message ' + type;
    messageDiv.style.display = 'block';

    // Hide message after 5 seconds
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// Optional: Add real-time password strength indicator
document.addEventListener('DOMContentLoaded', function() {
    const regPassword = document.getElementById('reg-password');
    if (regPassword) {
        regPassword.addEventListener('input', function() {
            // You can add password strength indicator here
            const strength = calculatePasswordStrength(this.value);
            // Display strength feedback to user
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