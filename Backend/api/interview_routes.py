from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional, Dict
import os
import shutil
from datetime import datetime

# Import analysis modules
from Backend.Models.whisper_stt import WhisperSTT
from Backend.Models.filler_word_detection import FillerDetector
from Backend.Utilities.video_utils import VideoProcessor
from Backend.Utilities.audio_extract import AudioExtractor
from Backend.Models.eye_tracker import EyeTracker
from Backend.Models.emotion_detector import EmotionDetector

# Create router
router = APIRouter(prefix="/api/interview", tags=["Interview Analysis"])

# Initialize analyzers (lazy loading)
analyzers = {
    "stt": None,
    "filler": None,
    "video": None,
    "audio": None,
    "eye": None,
    "emotion": None
}

def get_analyzer(name: str):
    """Get or create analyzer instance"""
    if analyzers[name] is None:
        if name == "stt":
            print("🎤 Loading Whisper STT...")
            analyzers["stt"] = WhisperSTT(model_size="base")
        elif name == "filler":
            analyzers["filler"] = FillerDetector(strictness="medium")
        elif name == "video":
            analyzers["video"] = VideoProcessor()
        elif name == "audio":
            analyzers["audio"] = AudioExtractor()
        elif name == "eye":
            print("👁️ Loading Eye Tracker...")
            analyzers["eye"] = EyeTracker()
        elif name == "emotion":
            print("😊 Loading Emotion Detector...")
            analyzers["emotion"] = EmotionDetector()
    
    return analyzers[name]


# ========== REQUEST/RESPONSE MODELS ==========

class AnalysisResponse(BaseModel):
    """Complete interview analysis response"""
    success: bool
    answer_id: str
    audio_analysis: Dict
    video_analysis: Dict
    overall_score: int
    feedback: str


# ========== HELPER FUNCTIONS ==========

def calculate_speaking_rate_score(wpm: float) -> int:
    """Calculate score from words per minute"""
    if 130 <= wpm <= 160:
        return 100
    elif 120 <= wpm < 130 or 160 < wpm <= 170:
        return 85
    elif 110 <= wpm < 120 or 170 < wpm <= 180:
        return 70
    else:
        return 50


def calculate_overall_score(
    filler_score: int,
    speaking_rate_score: int,
    eye_contact_percentage: float,
    emotion_tone: str
) -> int:
    """
    Calculate overall interview answer score
    
    Weights:
    - Audio quality (filler + speaking rate): 40%
    - Eye contact: 35%
    - Emotional presentation: 25%
    """
    # Audio score (40%)
    audio_score = (filler_score * 0.6 + speaking_rate_score * 0.4)
    audio_weighted = audio_score * 0.4
    
    # Eye contact score (35%)
    eye_score = min(100, eye_contact_percentage)  # Cap at 100
    eye_weighted = eye_score * 0.35
    
    # Emotion score (25%)
    emotion_scores = {
        "Very positive and enthusiastic": 100,
        "Positive and engaged": 90,
        "Professional and composed": 85,
        "Balanced emotional expression": 75,
        "Shows signs of stress or concern": 60
    }
    emotion_score = emotion_scores.get(emotion_tone, 70)
    emotion_weighted = emotion_score * 0.25
    
    overall = audio_weighted + eye_weighted + emotion_weighted
    
    return round(overall)


def generate_feedback(
    audio_analysis: Dict,
    video_analysis: Dict,
    overall_score: int
) -> str:
    """Generate friendly feedback message"""
    feedback_parts = []
    
    # Overall performance
    if overall_score >= 90:
        feedback_parts.append("🌟 Excellent performance!")
    elif overall_score >= 75:
        feedback_parts.append("👍 Good job!")
    elif overall_score >= 60:
        feedback_parts.append("✅ Decent performance.")
    else:
        feedback_parts.append("📝 Room for improvement.")
    
    # Audio feedback
    wpm = audio_analysis.get('words_per_minute', 0)
    if wpm < 110:
        feedback_parts.append("Try speaking a bit faster.")
    elif wpm > 180:
        feedback_parts.append("Slow down slightly for clarity.")
    
    filler_score = audio_analysis.get('filler_score', 100)
    if filler_score < 70:
        feedback_parts.append("Watch out for filler words like 'um' and 'uh'.")
    
    # Eye contact feedback
    eye_contact = video_analysis.get('eye_contact_percentage', 0)
    if eye_contact < 50:
        feedback_parts.append("Maintain more eye contact with the camera.")
    elif eye_contact > 80:
        feedback_parts.append("Great eye contact!")
    
    # Emotion feedback
    emotion_tone = video_analysis.get('emotional_tone', '')
    if 'stress' in emotion_tone.lower():
        feedback_parts.append("Try to appear more relaxed and confident.")
    elif 'positive' in emotion_tone.lower():
        feedback_parts.append("Your enthusiasm comes through well!")
    
    return " ".join(feedback_parts)


# ========== API ENDPOINTS ==========

@router.post("/analyze-answer")
async def analyze_interview_answer(
    video: UploadFile = File(...),
    question_id: Optional[str] = Form(None),
    question_number: Optional[int] = Form(None)
):
    """
    Complete analysis of interview answer
    
    Processes video file and returns:
    - Audio transcription + filler words + speaking rate
    - Eye contact tracking
    - Emotion detection
    - Overall score + feedback
    
    Args:
        video: Video file from WebRTC recording
        question_id: Optional question identifier
        question_number: Optional question number (1-5)
    
    Returns:
        Complete analysis results
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    answer_id = f"answer_{timestamp}"
    
    # Temp paths
    video_processor = get_analyzer("video")
    temp_video_path = os.path.join(video_processor.raw_path, f"{answer_id}.mp4")
    
    try:
        # Step 1: Save uploaded video
        print(f"\n{'='*70}")
        print(f"📹 ANALYZING INTERVIEW ANSWER: {answer_id}")
        print(f"{'='*70}\n")
        
        print("💾 Step 1: Saving video...")
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        print(f"   ✅ Saved: {temp_video_path}")
        
        # Step 2: Extract audio
        print("\n🎵 Step 2: Extracting audio...")
        audio_extract = get_analyzer("audio")
        audio_path = audio_extract.extract_audio(
            temp_video_path,
            output_filename=f"{answer_id}.wav"
        )
        
        # Step 3: Transcribe audio
        print("\n🎤 Step 3: Transcribing speech...")
        stt = get_analyzer("stt")
        transcription = stt.transcribe_audio(audio_path)
        transcript_text = transcription["text"]
        
        # Step 4: Get speaking stats
        print("\n📊 Step 4: Calculating speaking stats...")
        stats = stt.get_speaking_stats(transcription)
        wpm = stats["words_per_minute"]
        speaking_rate_score = calculate_speaking_rate_score(wpm)
        
        # Step 5: Analyze fillers
        print("\n🔍 Step 5: Detecting filler words...")
        filler_detector = get_analyzer("filler")
        filler_result = filler_detector.detect_fillers(transcript_text)
        
        # Step 6: Extract frames for video analysis
        print("\n🎬 Step 6: Extracting video frames...")
        frames = video_processor.extract_frames(
            video_path=temp_video_path,
            every_nth=30,  # ~1 frame per second at 30fps
            return_arrays=True
        )
        print(f"   ✅ Extracted {len(frames)} frames")
        
        # Step 7: Eye contact tracking
        print("\n👁️ Step 7: Tracking eye contact...")
        eye_tracker = get_analyzer("eye")
        eye_result = eye_tracker.analyze_frames_list(frames)
        eye_contact_percentage = eye_result['summary']['eye_contact_percentage']
        
        # Step 8: Emotion detection
        print("\n😊 Step 8: Detecting emotions...")
        emotion_detector = get_analyzer("emotion")
        emotion_result = emotion_detector.analyze_frames_list(frames)
        emotion_tone = emotion_result['summary']['emotional_tone']
        
        # Step 9: Calculate overall score
        print("\n🎯 Step 9: Calculating overall score...")
        overall_score = calculate_overall_score(
            filler_score=filler_result["score"],
            speaking_rate_score=speaking_rate_score,
            eye_contact_percentage=eye_contact_percentage,
            emotion_tone=emotion_tone
        )
        
        # Step 10: Generate feedback
        audio_analysis = {
            "transcript": transcript_text,
            "word_count": stats["total_words"],
            "words_per_minute": round(wpm, 1),
            "speaking_rate_score": speaking_rate_score,
            "filler_words": filler_result["filler_frequency"],
            "total_fillers": filler_result["total_fillers"],
            "filler_score": filler_result["score"],
            "duration_seconds": stats["duration_seconds"]
        }
        
        video_analysis = {
            "eye_contact_percentage": eye_contact_percentage,
            "dominant_emotion": emotion_result['summary']['dominant_emotion_overall'],
            "emotion_distribution": emotion_result['summary']['emotion_distribution'],
            "emotional_tone": emotion_tone,
            "frames_analyzed": len(frames)
        }
        
        feedback = generate_feedback(audio_analysis, video_analysis, overall_score)
        
        print(f"\n{'='*70}")
        print(f"✅ ANALYSIS COMPLETE!")
        print(f"   Overall Score: {overall_score}/100")
        print(f"   Eye Contact: {eye_contact_percentage}%")
        print(f"   Speaking Rate: {round(wpm, 1)} WPM")
        print(f"   Emotional Tone: {emotion_tone}")
        print(f"{'='*70}\n")
        
        # Return results
        return {
            "success": True,
            "answer_id": answer_id,
            "question_id": question_id,
            "question_number": question_number,
            "audio_analysis": audio_analysis,
            "video_analysis": video_analysis,
            "overall_score": overall_score,
            "feedback": feedback,
            "timestamp": timestamp
        }
    
    except Exception as e:
        print(f"\n❌ ANALYSIS FAILED: {str(e)}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    
    finally:
        # Cleanup temp files (optional - keep for debugging)
        # os.remove(temp_video_path)
        # os.remove(audio_path)
        pass


@router.get("/test")
async def test_interview_analyzer():
    """Test if all analyzers can be loaded"""
    try:
        status = {}
        
        # Test each analyzer
        analyzers_to_test = ["stt", "filler", "video", "audio", "eye", "emotion"]
        
        for name in analyzers_to_test:
            try:
                get_analyzer(name)
                status[name] = "✅ Ready"
            except Exception as e:
                status[name] = f"❌ Error: {str(e)}"
        
        all_ready = all("✅" in s for s in status.values())
        
        return {
            "success": all_ready,
            "message": "All analyzers ready!" if all_ready else "Some analyzers failed to load",
            "analyzers": status
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )