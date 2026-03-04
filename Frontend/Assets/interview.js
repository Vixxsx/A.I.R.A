// ========== CONFIGURATION ==========
const API_BASE_URL = 'http://localhost:8000';
const QUESTION_TIME_LIMIT = 120; // 2 minutes in seconds
const COUNTDOWN_DURATION = 5; // 5 seconds before each question

// ========== STATE ==========
let stream = null;
let mediaRecorder = null;
let recordedChunks = [];
let currentQuestionIndex = 0;
let questions = [];
let timerInterval = null;
let timeRemaining = QUESTION_TIME_LIMIT;
let isRecording = false;
let savedVideos = []; // Store all recorded videos for batch processing

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', async () => {
    // Check if user came from test page
    if (!sessionStorage.getItem('mediaReady')) {
        window.location.href = 'interview_test.html';
        return;
    }

    // Load interview settings
    const settings = JSON.parse(sessionStorage.getItem('interviewPreferences') || '{}');
   
    // Initialize camera
    await initializeCamera();
   
    // Fetch questions from backend
    await fetchQuestions(settings);
   
    // Start first question
    startQuestion();
});

// ========== CAMERA SETUP ==========
async function initializeCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: true
        });

        const videoElement = document.getElementById('videoElement');
        videoElement.srcObject = stream;
       
        console.log('✅ Camera initialized');
    } catch (error) {
        console.error('❌ Camera error:', error);
        alert('Failed to access camera. Please check permissions.');
        window.location.href = 'home.html';
    }
}

// ========== FETCH QUESTIONS ==========
async function fetchQuestions(settings) {
    // FIXED: Show correct loading message for question generation
    showLoading('Generating Interview Questions', 'Please be patient...');
   
    try {
        const response = await fetch(`${API_BASE_URL}/api/questions/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jobRole: settings.jobRole,
                difficulty: settings.difficulty,
                count: settings.numQuestions || 5,
                type: settings.interviewType
            })
        });

        if (response.ok) {
            const data = await response.json();
            questions = data.questions || [];
        }
    } catch (error) {
        console.error('❌ Failed to fetch questions:', error);
    }

    // Fallback demo questions if API fails
    if (questions.length === 0) {
        questions = [
            "Tell me about your experience with the technologies mentioned in your resume.",
            "Describe a challenging project you worked on and how you overcame obstacles.",
            "Where do you see yourself professionally in 5 years?",
            "How do you handle disagreements with team members?",
            "Why are you interested in this role and our company?"
        ];
    }

    hideLoading();
    updateProgress();
}

// ========== QUESTION FLOW ==========
async function startQuestion() {
    if (currentQuestionIndex >= questions.length) {
        // All questions recorded! Now process everything
        await processAllAnswers();
        return;
    }

    // Update UI
    updateProgress();
    displayQuestion();
   
    // Show countdown (NO DIM OVERLAY)
    await showCountdown();
   
    // Start recording
    startRecording();
}

function displayQuestion() {
    const questionNum = currentQuestionIndex + 1;
    const totalQuestions = questions.length;
   
    document.getElementById('questionNumber').textContent = `Question ${questionNum}`;
    document.getElementById('questionProgress').textContent = `Question ${questionNum} of ${totalQuestions}`;
    document.getElementById('questionText').textContent = questions[currentQuestionIndex];
}

function updateProgress() {
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
    document.getElementById('progressBar').style.width = progress + '%';
}

// ========== COUNTDOWN - NEW DESIGN ==========
async function showCountdown() {
    const container = document.getElementById('countdownContainer');
    const numberEl = document.getElementById('countdownNumber');
   
    container.classList.add('active');
   
    for (let i = COUNTDOWN_DURATION; i > 0; i--) {
        numberEl.textContent = i;
       
        // Reset animation
        numberEl.style.animation = 'none';
        const ring = container.querySelector('.countdown-ring');
        if (ring) ring.style.animation = 'none';
       
        // Trigger reflow
        void numberEl.offsetWidth;
       
        // Restart animation
        numberEl.style.animation = 'numberBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
        if (ring) ring.style.animation = 'ringPulse 1s ease-in-out';
       
        await sleep(1000);
    }
   
    container.classList.remove('active');
}

// ========== RECORDING ==========
function startRecording() {
    recordedChunks = [];
   
    // Setup MediaRecorder
    const options = { mimeType: 'video/webm;codecs=vp9,opus' };
    try {
        mediaRecorder = new MediaRecorder(stream, options);
    } catch (e) {
        console.warn('vp9 not supported, trying vp8');
        try {
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8,opus' });
        } catch (e2) {
            mediaRecorder = new MediaRecorder(stream);
        }
    }

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };

    mediaRecorder.onstop = () => {
        console.log('✅ Recording stopped');
        saveVideoLocally();
    };

    // Start recording
    mediaRecorder.start();
    isRecording = true;
   
    // Show recording indicator
    document.getElementById('recordingIndicator').classList.add('active');
   
    // Show stop button
    document.getElementById('stopBtn').classList.add('show');
   
    // Start timer
    startTimer();
   
    console.log('🎥 Recording started');
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        stopTimer();
       
        // Hide recording indicator
        document.getElementById('recordingIndicator').classList.remove('active');
       
        // Hide stop button
        document.getElementById('stopBtn').classList.remove('show');
    }
}

// ========== SAVE VIDEO LOCALLY (BATCH STRATEGY) ==========
function saveVideoLocally() {
    // Create video blob
    const blob = new Blob(recordedChunks, { type: 'video/webm' });
   
    // Store video with question info
    savedVideos.push({
        questionNumber: currentQuestionIndex + 1,
        question: questions[currentQuestionIndex],
        videoBlob: blob,
        timestamp: new Date().toISOString()
    });
   
    console.log(`✅ Video ${currentQuestionIndex + 1} saved locally`);
   
    // Move to next question IMMEDIATELY (no backend call yet!)
    currentQuestionIndex++;
    startQuestion();
}

// ========== BATCH PROCESSING (AT THE END) ==========
async function processAllAnswers() {
    // FIXED: Show "Analyzing Answer" for batch processing
    showLoading('Analyzing Answer', `Processing all ${savedVideos.length} answers...`);
   
    console.log('🔄 Starting batch upload and analysis...');
   
    const results = [];
   
    for (let i = 0; i < savedVideos.length; i++) {
        const video = savedVideos[i];
       
        // FIXED: Keep "Analyzing Answer" title, update subtitle
        showLoading('Analyzing Answer', `Analyzing answer ${i + 1} of ${savedVideos.length}...`);
       
        try {
            // Create form data
            const formData = new FormData();
            formData.append('video', video.videoBlob, `question_${video.questionNumber}.webm`);
            formData.append('question', video.question);
            formData.append('questionNumber', video.questionNumber);
           
            // Upload to backend
            const response = await fetch(`${API_BASE_URL}/api/interview/analyze-answer`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                results.push(result);
                console.log(`✅ Answer ${i + 1} analyzed`);
            } else {
                console.error(`❌ Failed to analyze answer ${i + 1}`);
                results.push({ error: 'Analysis failed', questionNumber: video.questionNumber });
            }
           
        } catch (error) {
            console.error(`❌ Error analyzing answer ${i + 1}:`, error);
            results.push({ error: error.message, questionNumber: video.questionNumber });
        }
    }
   
    // Store all results
    sessionStorage.setItem('interviewResults', JSON.stringify(results));
   
    await finishInterview();
}

// ========== FINISH INTERVIEW ==========
async function finishInterview() {
    showLoading('Analyzing Answer', 'Preparing your scorecard...');
   
    // Stop camera
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
   
    await sleep(1500);
   
    // Redirect to scorecard
    window.location.href = 'scorecard.html';
}

// ========== TIMER ==========
function startTimer() {
    timeRemaining = QUESTION_TIME_LIMIT;
    updateTimerDisplay();
   
    timerInterval = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        updateTimerColor();
       
        if (timeRemaining <= 0) {
            // Time's up!
            stopRecording();
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('timer').textContent = display;
}

function updateTimerColor() {
    const timerEl = document.getElementById('timer');
   
    // Remove all classes
    timerEl.classList.remove('warning', 'danger');
   
    if (timeRemaining <= 10) {
        // Dark red + pulsing (0-10 seconds)
        timerEl.classList.add('danger');
    } else if (timeRemaining <= 30) {
        // Light red (11-30 seconds)
        timerEl.classList.add('warning');
    }
    // else: white (normal)
}

// ========== UI HELPERS ==========
function showLoading(title, subtitle) {
    // Update both title and subtitle
    document.querySelector('.lo-title').textContent = title;
    document.getElementById('loadingText').textContent = subtitle;
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ========== EVENT LISTENERS ==========
document.getElementById('stopBtn').addEventListener('click', () => {
    stopRecording();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    stopTimer();
});

// Prevent accidental page close during interview
window.addEventListener('beforeunload', (e) => {
    if (currentQuestionIndex > 0 && currentQuestionIndex < questions.length) {
        e.preventDefault();
        e.returnValue = 'Interview in progress. Are you sure you want to leave?';
    }
});