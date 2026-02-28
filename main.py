from py_compile import main
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
import os
import warnings

import shutil
from datetime import datetime

# Import routes
from Backend.api.video_routes import router as video_router
from Backend.api.Question_routes import router as question_router
from Backend.api.interview_routes import router as interview_router
from Backend.api.feedback_routes import router as feedback_router

# Import models
from Backend.Models.whisper_stt import WhisperSTT
from Backend.Models.filler_word_detection import FillerDetector
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore') 

UPLOAD_DIR = "Data/Video/Raw"

# Then the makedirs line will work
os.makedirs(UPLOAD_DIR, exist_ok=True)
# ========== CREATE FASTAPI APP ==========

app = FastAPI(
    title="AIRA - AI Interview Analyzer",
    description="Backend API for AI-Powered Interview Feedback Analyzer",
    version="1.0.0"
)

# ========== CORS MIDDLEWARE ==========

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== LOAD AI MODELS ==========

print("🎤 Loading Whisper model...")
stt = WhisperSTT(model_size="base")
print("✅ Whisper loaded!")

print("🔍 Loading Filler Detector...")
filler_detector = FillerDetector(strictness="medium")
print("✅ Filler Detector loaded!")

# ========== CREATE DIRECTORIES ==========

TRANSCRIPT_DIR = "Data/Transcript"
AUDIO_TEST_DIR = "Data/Audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(AUDIO_TEST_DIR, exist_ok=True)

# ========== INCLUDE ROUTERS ==========

# Video routes
app.include_router(video_router)

# Interview routes
app.include_router(interview_router)
print("✅ Interview routes loaded")
app.include_router(question_router)
print("✅ Question routes loaded")
app.include_router(feedback_router)
# Auth routes - IMPORT AND INCLUDE
try:
    from Backend.api.Auth_routes import router as auth_router
    app.include_router(auth_router)
    print("✅ Auth routes loaded from Backend/api/")
except ImportError:
    try:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from Backend.api.Auth_routes import router as auth_router
        app.include_router(auth_router)
        print("✅ Auth routes loaded (development mode)")
    except ImportError:
        print("⚠️  Auth routes not found - authentication endpoints not available")


# ========== SERVE FRONTEND STATIC FILES ==========

# Mount static files (CSS, JS, images, audio)
app.mount("/Assets", StaticFiles(directory="Frontend/Assets"), name="assets")
app.mount("/Components", StaticFiles(directory="Frontend/Components"), name="components")

# Mount pages directory
app.mount("/Pages", StaticFiles(directory="Frontend/Pages", html=True), name="pages")

print("✅ Frontend static files mounted")
print("   - Assets: /Assets/*")
print("   - Components: /Components/*")
print("   - Pages: /Pages/*")


# ========== RESPONSE MODELS ==========

class TranscriptResponse(BaseModel):
    success: bool
    transcript: str
    word_count: int
    duration: float
    speaking_time: float
    words_per_minute: float
    language: str
    timestamp: str
    saved_path: str

class FillerAnalysisResponse(BaseModel):
    success: bool
    total_fillers: int
    filler_density: float
    filler_score: int
    filler_frequency: dict
    categories: dict


# ========== HELPER FUNCTIONS ==========

def get_speaking_rate_feedback(wpm: float) -> str:
    """Generate feedback for speaking rate"""
    if wpm < 110:
        return "Speaking too slowly. Try to increase pace slightly."
    elif 110 <= wpm < 130:
        return "Speaking a bit slow. Slightly faster would be better."
    elif 130 <= wpm <= 160:
        return "Excellent speaking pace - clear and natural."
    elif 160 < wpm <= 180:
        return "Speaking a bit fast. Slow down slightly for clarity."
    else:
        return "Speaking too fast. Take your time and breathe."


def calculate_overall_audio_score(filler_score: int, speaking_rate_score: int) -> int:
    """
    Calculate overall audio quality score
    
    Weighted average:
    - Filler words: 60% (more important)
    - Speaking rate: 40%
    """
    overall = (filler_score * 0.6) + (speaking_rate_score * 0.4)
    return round(overall)


# ========== BASIC ENDPOINTS ==========

@app.get("/")
async def root():
    """Redirect to login page"""
    return RedirectResponse(url="/Pages/start.html")


@app.get("/api")
async def api_root():
    """API welcome endpoint"""
    return {
        "message": "Welcome to AIRA - AI Interview Analyzer Backend!",
        "status": "running",
        "version": "1.0.0",
        "docs": "Visit /docs for API documentation",
        "features": {
            "authentication": "✅ Enabled",
            "audio_analysis": "✅ Enabled",
            "video_processing": "✅ Enabled",
            "interview_analysis": "✅ Enabled"
        }
    }

@app.get("/api/test")
def api_test():
    return {
        "message": "API is working!",
        "status": "success"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "api": "Operational",
        "Models": {
            "whisper": "loaded",
            "filler_detector": "loaded"
        }
    }

@app.get("/status")
def status():
    return {
        "api_name": "AIRA - AI Interview Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "status": "/status",
            "test": "/api/test",
            "auth": {
                "register": "/api/auth/register",
                "login": "/api/auth/login",
                "test": "/api/auth/test"
            },
            "audio": {
                "transcribe": "/api/transcribe",
                "analyze_fillers": "/api/analyze/fillers",
                "complete_analysis": "/api/analyze/complete"
            },
            "interview": {
                "analyze_answer": "/api/interview/analyze-answer",
                "test": "/api/interview/test"
            }
        }
    }


# ========== AUDIO ANALYSIS ENDPOINTS ==========

@app.post("/api/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[1]
        temp_file_path = os.path.join(UPLOAD_DIR, f"audio_{timestamp}{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        print(f"📁 Saved audio to: {temp_file_path}")
        
        # Transcribe with Whisper
        print("🎤 Transcribing...")
        transcript_data = stt.transcribe_audio(temp_file_path)
        
        # Get speaking statistics
        stats = stt.get_speaking_stats(transcript_data)
        
        # Save transcript to file
        output_filename = f"transcript_{timestamp}.json"
        saved_path = stt.save_transcript(transcript_data, filename=output_filename)
        
        # Clean up temp audio file
        os.remove(temp_file_path)
        print("✅ Transcription complete!")
        
        return TranscriptResponse(
            success=True,
            transcript=transcript_data["text"],
            word_count=stats["total_words"],
            duration=stats["duration_seconds"],
            speaking_time=stats["speaking_time_seconds"],
            words_per_minute=stats["words_per_minute"],
            language=transcript_data["language"],
            timestamp=transcript_data["timestamp"],
            saved_path=saved_path
        )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/api/analyze/fillers", response_model=FillerAnalysisResponse)
async def analyze_fillers(text: str):
    """
    Analyze text for filler words
    """
    try:
        print("🔍 Analyzing fillers...")
        result = filler_detector.detect_fillers(text)
        
        return FillerAnalysisResponse(
            success=True,
            total_fillers=result["total_fillers"],
            filler_density=result["filler_density_percentage"],
            filler_score=result["score"],
            filler_frequency=result["filler_frequency"],
            categories=result["categories"]
        )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Filler analysis failed: {str(e)}")


@app.post("/api/analyze/complete")
async def analyze_complete(audio: UploadFile = File(...)):
    """
    Complete audio analysis
    
    Combines:
    - Whisper transcription
    - Filler word detection
    - Audio metrics (WPM, pauses)
    - Overall scoring
    """
    try:
        # Save uploaded file temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[1]
        temp_path = os.path.join(UPLOAD_DIR, f"audio_{timestamp}{file_extension}")
        
        with open(temp_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        print(f"📁 Audio saved: {temp_path}")
        
        # Step 1: Transcribe with Whisper
        print("🎤 Step 1: Transcribing...")
        transcription_result = stt.transcribe_audio(temp_path)
        
        transcript_text = transcription_result["text"]
        audio_duration = transcription_result.get("duration", 0)
        language = transcription_result.get("language", "unknown")
        
        # Step 2: Get speaking stats
        print("📊 Step 2: Calculating speaking stats...")
        stats = stt.get_speaking_stats(transcription_result)
        
        # Step 3: Analyze fillers
        print("🔍 Step 3: Analyzing fillers...")
        filler_result = filler_detector.detect_fillers(transcript_text)
        
        # Step 4: Calculate speaking rate score
        words_per_minute = stats["words_per_minute"]
        
        if 130 <= words_per_minute <= 160:
            speaking_rate_score = 100
        elif 120 <= words_per_minute < 130 or 160 < words_per_minute <= 170:
            speaking_rate_score = 85
        elif 110 <= words_per_minute < 120 or 170 < words_per_minute <= 180:
            speaking_rate_score = 70
        else:
            speaking_rate_score = 50
        
        # Step 5: Save transcript
        print("💾 Step 4: Saving transcript...")
        transcript_filename = f"transcript_{timestamp}.json"
        saved_path = stt.save_transcript(transcription_result, filename=transcript_filename)
        
        # Clean up temp file
        os.remove(temp_path)
        
        print("✅ Complete analysis done!")
        
        # Return combined analysis
        return {
            "success": True,
            "audio_file": audio.filename,
            "transcription": {
                "text": transcript_text,
                "word_count": stats["total_words"],
                "duration_seconds": stats["duration_seconds"],
                "language": language,
                "saved_to": saved_path
            },
            "filler_analysis": {
                "filler_words": filler_result["filler_frequency"],
                "total_fillers": filler_result["total_fillers"],
                "filler_percentage": filler_result["filler_density_percentage"],
                "score": filler_result["score"],
                "feedback": f"Filler word score: {filler_result['score']}/100"
            },
            "audio_metrics": {
                "words_per_minute": round(words_per_minute, 1),
                "speaking_time": stats["speaking_time_seconds"],
                "pause_time": stats["pause_time_seconds"],
                "number_of_pauses": stats["number_of_pauses"],
                "speaking_rate_score": speaking_rate_score,
                "speaking_rate_feedback": get_speaking_rate_feedback(words_per_minute)
            },
            "overall_audio_score": calculate_overall_audio_score(
                filler_result["score"],
                speaking_rate_score
            )
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Complete analysis failed: {str(e)}")


# ========== RUN SERVER ==========

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting AIRA Backend Server...")
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000/")
    print("   - Login: http://localhost:8000/Pages/Login.html")
    print("   - Dashboard: http://localhost:8000/Pages/Dashboard.html")
    print("\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)