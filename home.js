// Check if user is logged in
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupFormHandler();
});

// Check if user is logged in
function checkLoginStatus() {
    // In a real app, you'd check session/token
    // For now, we'll use a simple check
    const currentUser = getCurrentUser();
    
    if (!currentUser) {
        // User not logged in, redirect to login page
        window.location.href = 'index.html';
        return;
    }
    
    // Display username
    document.getElementById('username').textContent = currentUser;
}

// Get current logged in user (from memory)
function getCurrentUser() {
    // In production, this would check JWT token or session
    // For demo, we'll check if there's a logged in user stored
    return sessionStorage.getItem('currentUser');
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
        
        // Show success and redirect (to interview page - to be created)
        alert(`Interview Setup Complete!
        
Job Role: ${jobRole}
Difficulty: ${difficulty}
Questions: ${numQuestions}
Type: ${interviewType}

Starting your interview...`);
        
        // In production, redirect to interview page
        // window.location.href = 'interview.html';
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
    sessionStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}