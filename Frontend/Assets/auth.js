document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const direction = params.get('dir');
    const card = document.querySelector('.auth-card');

    if (card) {
        if (direction === 'right') {
            card.classList.add('slide-right');
        } else if (direction === 'left') {
            card.classList.add('slide-left');
        } else {
            // Default "drop down" animation if no direction is specified
            card.style.animation = "boxSlideDown 0.6s ease forwards"; 
        }
    }
});

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

    // Get stored users from memory
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
    
    // Store session (in a real app, you'd use secure tokens)
    if (rememberMe) {
        storeSession(user.username);
    }

    // Redirect after 1.5 seconds (you can change this to your dashboard page)
    setTimeout(() => {
        // window.location.href = 'dashboard.html';
        alert('Login successful! (Redirect to dashboard here)');
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

// Storage Functions (using in-memory storage for demo)
// In production, you would use a backend database

let usersData = [];

function getUsers() {
    return usersData;
}

function saveUsers(users) {
    usersData = users;
}

function storeSession(username) {
    // In production, use secure session management
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

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const direction = params.get('dir');
    const card = document.querySelector('.auth-card');

    if (card) {
        if (direction === 'right') {
            // Sliding right into Register
            card.classList.add('slide-in-right');
        } else if (direction === 'left') {
            // Sliding left into Login
            card.classList.add('slide-in-left');
        } else {
            // Default "fade-in" if no direction (e.g., first landing)
            card.style.opacity = "1";
            card.style.transition = "opacity 0.5s ease";
        }
    }
});