// Check if user is logged in
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupFormHandler();
});

function checkLoginStatus() {
    const currentUser = getCurrentUser();
    
    if (!currentUser) {
        // User not logged in, redirect to login page
        window.location.href = 'Login.html';
        return;
    }
    
    // Display username
    document.getElementById('username').textContent = currentUser+ '!';
}
function getCurrentUser() {
    return localStorage.getItem('aira_user') || sessionStorage.getItem('aira_user');
}

// Setup form submission handler
function setupFormHandler() {
    const form = document.getElementById('interviewForm');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const jobRole = document.getElementById('jobRole').value;
        const difficulty = document.getElementById('difficulty').value;
        const numQuestions = document.getElementById('numQuestions').value;
        const interviewType = document.getElementById('interviewType').value;
        
        // Validation
        if (!jobRole || !difficulty || !numQuestions || !interviewType) {
            showMessage('Please fill in all fields', 'error');
            return;
        }
        
        if (numQuestions < 1 || numQuestions > 20) {
            showMessage('Number of questions must be between 1 and 20', 'error');
            return;

        }
        console.log('🚀 About to redirect to interview_test.html');

        setTimeout(() => {
            console.log('🎯 Redirecting NOW!');
            window.location.href = 'interview_test.html';
        }, 1500);
        // Store interview preferences
        const interviewPreferences = {
            jobRole,
            difficulty,
            numQuestions,
            interviewType,
            timestamp: new Date().toISOString()
        };
        
        // Save preferences
        sessionStorage.setItem('interviewPreferences', JSON.stringify(interviewPreferences));
        
        showMessage('✅ Setup complete! Starting interview...', 'success');

        setTimeout(() => {
            window.location.href = 'interview_test.html';
        }, 1500);
            });
}

// Modal functions
function openModal() {
    document.getElementById('aboutModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('aboutModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('aboutModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Show message helper
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = 'message ' + type;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// Logout function (optional - you can add a logout button)
function logout() {
    sessionStorage.removeItem('aira_user');
    window.location.href = 'Login.html';
}