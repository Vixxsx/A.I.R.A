// ════════════════════════════════
//  INIT
// ════════════════════════════════
document.addEventListener('DOMContentLoaded', function () {
    checkLoginStatus();
    setupFormHandler();
    loadInterviewHistory();
});

// ════════════════════════════════
//  AUTH
// ════════════════════════════════
function getCurrentUser() {
    return localStorage.getItem('aira_user') || sessionStorage.getItem('aira_user');
}

function checkLoginStatus() {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        window.location.href = 'Login.html';
        return;
    }
    document.getElementById('username').textContent = currentUser + '!';
}

function logout() {
    sessionStorage.removeItem('aira_user');
    localStorage.removeItem('aira_user');
    window.location.href = 'Login.html';
}

// ════════════════════════════════
//  FORM HANDLER
// ════════════════════════════════
function setupFormHandler() {
    const form = document.getElementById('interviewForm');

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const jobRole       = document.getElementById('jobRole').value.trim();
        const difficulty    = document.getElementById('difficulty').value;
        const numQuestions  = document.getElementById('numQuestions').value;
        const interviewType = document.getElementById('interviewType').value;

        if (!jobRole || !difficulty || !numQuestions || !interviewType) {
            showMessage('Please fill in all fields', 'error');
            return;
        }
        if (numQuestions < 1 || numQuestions > 20) {
            showMessage('Number of questions must be between 1 and 20', 'error');
            return;
        }

        // Save preferences — jobRole saved separately so Interview page can pass it to API
        const interviewPreferences = {
            jobRole,
            difficulty,
            numQuestions,
            interviewType,
            timestamp: new Date().toISOString()
        };

        sessionStorage.setItem('interviewPreferences', JSON.stringify(interviewPreferences));
        sessionStorage.setItem('jobRole', jobRole);  // easy access for Interview_routes

        showMessage('✅ Setup complete! Starting interview...', 'success');

        setTimeout(() => {
            window.location.href = 'interview_test.html';
        }, 1500);
    });
}

// ════════════════════════════════
//  INTERVIEW HISTORY
// ════════════════════════════════
async function loadInterviewHistory() {
    const username = getCurrentUser();
    const section = document.getElementById('historySection');
    
    if (!username) {
        section.innerHTML = '<p>Please log in to view history</p>';
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:8000/api/interviews/recent?username=${username}&limit=5`);
        
        if (response.ok) {
            const data = await response.json();
            if (data.interviews && data.interviews.length > 0) {
                section.innerHTML = data.interviews.map(buildHistoryCard).join('');
            } else {
                section.innerHTML = `
                    <div style="text-align:center; padding:40px; color:rgba(255,251,150,0.3);">
                        <div style="font-size:48px; margin-bottom:16px;">🎯</div>
                        <p>No interviews yet</p>
                    </div>`;
            }
        }
    } catch (error) {
        console.error('Error loading history:', error);
        section.innerHTML = '<p>Unable to load history</p>';
    }
}

function buildHistoryCard(interview) {
    const GRADE_COLOURS = {
        S: 'linear-gradient(135deg,#fbe238,#f49829)',
        A: 'linear-gradient(135deg,#05FFA1,#01CDFE)',
        B: 'linear-gradient(135deg,#01CDFE,#B967FF)',
        C: 'linear-gradient(135deg,#FFFB96,#f49829)',
        D: 'linear-gradient(135deg,#f49829,#FF71CE)',
        F: 'linear-gradient(135deg,#FF71CE,#764ba2)',
    };
    
    const date = new Date(interview.timestamp).toLocaleDateString('en-US', { 
        month:'short', day:'numeric', year:'numeric' 
    });
    
    return `
    <div class="history-card">
        <div class="history-grade" style="background: ${GRADE_COLOURS[interview.grade]}">
            ${interview.grade}
        </div>
        <div class="history-info">
            <div class="history-role">${interview.job_role}</div>
            <div class="history-date">
                <span>📅 ${date}</span>
            </div>
        </div>
        <div class="history-score">
            <div class="score-value">${interview.overall_score}</div>
            <div class="score-label">/ 100</div>
        </div>
    </div>`;
}

function getInterviewHistory() {
    // Try to load from localStorage (persists across sessions)
    try {
        const raw = localStorage.getItem('aira_interview_history');
        if (raw) return JSON.parse(raw);
    } catch(e) {}

    // Fallback: check if current session has results and build a single entry
    try {
        const raw = sessionStorage.getItem('interviewResults');
        const prefs = sessionStorage.getItem('interviewPreferences');
        if (raw && prefs) {
            const results  = JSON.parse(raw);
            const p        = JSON.parse(prefs);
            const overall  = calcOverall(results);
            const grade    = scoreToGrade(overall);
            return [{
                jobRole:       p.jobRole,
                difficulty:    p.difficulty,
                interviewType: p.interviewType,
                numQuestions:  p.numQuestions,
                overall,
                grade,
                timestamp:     p.timestamp || new Date().toISOString()
            }];
        }
    } catch(e) {}

    return [];
}

function calcOverall(results) {
    if (!results || !results.length) return 0;
    let tC=0,tA=0,tE=0,tB=0, cC=0,aC=0,eC=0,bC=0;
    results.forEach(r => {
        if (!r.success) return;
        // Content
        if (r.content_relevancy) { tC += r.content_relevancy.score; cC++; }
        else if (r.transcript) {
            const wc = r.transcript.word_count||0, dur = r.transcript.duration_seconds||1;
            let s=70; if(wc>=50&&wc<=250) s+=15; if(dur>=30&&dur<=120) s+=15;
            tC+=s; cC++;
        }
        if (r.audio_quality)  { tA += r.audio_quality.overall_score;  aC++; }
        tE += 70; eC++;
        if (r.body_language)  { tB += r.body_language.score;          bC++; }
    });
    const c=cC>0?tC/cC:70, a=aC>0?tA/aC:75, e=eC>0?tE/eC:70, b=bC>0?tB/bC:75;
    return Math.round(c*0.30 + a*0.25 + e*0.25 + b*0.20);
}

function scoreToGrade(s) {
    if(s>=90) return 'S'; if(s>=80) return 'A';
    if(s>=70) return 'B'; if(s>=60) return 'C';
    if(s>=50) return 'D'; return 'F';
}

// Call this from Scorecard page after interview to persist history
function saveInterviewToHistory(entry) {
    try {
        const raw     = localStorage.getItem('aira_interview_history');
        const history = raw ? JSON.parse(raw) : [];
        history.push(entry);
        // Keep last 20 only
        if (history.length > 20) history.splice(0, history.length - 20);
        localStorage.setItem('aira_interview_history', JSON.stringify(history));
    } catch(e) {
        console.warn('Could not save history:', e);
    }
}

const GRADE_COLOURS = {
    S: 'linear-gradient(135deg,#fbe238,#f49829)',
    A: 'linear-gradient(135deg,#05FFA1,#01CDFE)',
    B: 'linear-gradient(135deg,#01CDFE,#B967FF)',
    C: 'linear-gradient(135deg,#FFFB96,#f49829)',
    D: 'linear-gradient(135deg,#f49829,#FF71CE)',
    F: 'linear-gradient(135deg,#FF71CE,#764ba2)',
};

const GRADE_SHADOWS = {
    S: 'rgba(251,226,56,0.5)',
    A: 'rgba(5,255,161,0.5)',
    B: 'rgba(1,205,254,0.5)',
    C: 'rgba(255,251,150,0.4)',
    D: 'rgba(244,152,41,0.5)',
    F: 'rgba(255,113,206,0.5)',
};

function buildHistoryCard(entry) {
    const grade   = entry.grade  || 'B';
    const score   = entry.overall || 0;
    const role    = entry.jobRole || 'Interview';
    const type    = (entry.interviewType || 'mixed').charAt(0).toUpperCase() + (entry.interviewType||'mixed').slice(1);
    const diff    = (entry.difficulty   || 'intermediate').charAt(0).toUpperCase() + (entry.difficulty||'').slice(1);
    const date    = entry.timestamp
        ? new Date(entry.timestamp).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' })
        : 'Unknown date';
    const numQ    = entry.numQuestions || '?';

    return `
    <div class="history-card">
        <div class="history-grade" style="
            background: ${GRADE_COLOURS[grade] || GRADE_COLOURS['B']};
            box-shadow: 0 4px 20px ${GRADE_SHADOWS[grade] || 'rgba(1,205,254,0.4)'};
        ">${grade}</div>

        <div class="history-info">
            <div class="history-role">${role}</div>
            <div class="history-date">
                <span>📅 ${date}</span>
                <span>🎯 ${type}</span>
                <span>⚡ ${diff}</span>
                <span>❓ ${numQ} questions</span>
            </div>
        </div>

        <div class="history-score">
            <div class="score-value">${score}</div>
            <div class="score-label">/ 100</div>
        </div>
    </div>`;
}

// ════════════════════════════════
//  MODAL
// ════════════════════════════════
function openModal() {
    document.getElementById('aboutModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('aboutModal').style.display = 'none';
}

window.onclick = function (event) {
    const modal = document.getElementById('aboutModal');
    if (event.target === modal) closeModal();
};

// ════════════════════════════════
//  MESSAGE HELPER
// ════════════════════════════════
function showMessage(text, type) {
    const el = document.getElementById('message');
    el.textContent   = text;
    el.className     = 'message ' + type;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}