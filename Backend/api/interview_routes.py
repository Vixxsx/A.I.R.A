"""
Interview Routes - Fixed for Emotion Detection
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import shutil
import cv2
from datetime import datetime

# Import your models
from Backend.Models.whisper_stt import WhisperSTT
from Backend.Models.filler_word_detection import FillerDetector
from Backend.Models.emotion_detector import EmotionDetector
from Backend.Utilities.video_utils import VideoProcessor
from Backend.Utilities.audio_extract import AudioExtractor

import numpy as np

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

router = APIRouter(prefix="/api/interview", tags=["interview"])

# Initialize models (you may want to do this in main.py instead)
stt = WhisperSTT(model_size="base")
filler_detector = FillerDetector(strictness="medium")
emotion_detector = EmotionDetector()
video_processor = VideoProcessor()
audio_extractor = AudioExtractor()

# Directories
UPLOAD_DIR = "Data/Video/Raw"
FRAMES_DIR = "Data/Video/Frames"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)


@router.post("/analyze-answer")
async def analyze_answer(
    video: UploadFile = File(...),
    question: str = Form(...),
    questionNumber: int = Form(...)
):
    try:
        # Step 1: Save uploaded video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"question_{questionNumber}_{timestamp}.webm"
        video_path = os.path.join(UPLOAD_DIR, video_filename)
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        print(f"\n{'='*60}")
        print(f"🎯 Analyzing Question {questionNumber}")
        print(f"📁 Video saved: {video_path}")
        print(f"❓ Question: {question}")
        print(f"{'='*60}\n")
        
        # Step 2: Extract audio and transcribe
        print("🎤 Step 1: Extracting audio and transcribing...")
        audio_path = audio_extractor.extract_audio(video_path)
        transcript_result = stt.transcribe_audio(audio_path)
        transcript_text = transcript_result["text"]
        stats = stt.get_speaking_stats(transcript_result)

        print(f"✅ Transcription complete: {stats['total_words']} words")
        print(f"   Speaking rate: {stats['words_per_minute']} WPM")
        
        # Step 3: Analyze filler words
        print("\n🔍 Step 2: Analyzing filler words...")
        filler_result = filler_detector.detect_fillers(transcript_text)
        
        print(f"✅ Filler analysis complete:")
        print(f"   Total fillers: {filler_result['total_fillers']}")
        print(f"   Filler density: {filler_result['filler_density_percentage']}%")
        print(f"   Filler score: {filler_result['score']}/100")
        
        # Step 4: Extract frames
        print("\n📸 Step 3: Extracting video frames...")
        frames_output_dir = os.path.join(FRAMES_DIR, f"question_{questionNumber}_{timestamp}")
        os.makedirs(frames_output_dir, exist_ok=True)
        
        frame_paths = video_processor.extract_frames(
            video_path,
            output_folder=frames_output_dir,
            every_nth=30,
            max_frames=30,
            return_arrays=True  
        )
        
        print(f"✅ Extracted {len(frame_paths)} frames")
        
        # Step 5: Analyze emotions
        print("\n😊 Step 4: Analyzing emotions from frames...")
        
        # Load frames for emotion analysis
          # Analyze first 30 frames max
        
        emotion_results = emotion_detector.analyze_frames_list(frame_paths)
        
        print(f"✅ Emotion analysis complete")
        
        # Step 6: Calculate audio quality score
        print("\n📊 Step 5: Calculating overall scores...")
        words_per_minute = stats["words_per_minute"]
        
        if 130 <= words_per_minute <= 160:
            speaking_rate_score = 100
        elif 120 <= words_per_minute < 130 or 160 < words_per_minute <= 170:
            speaking_rate_score = 85
        elif 110 <= words_per_minute < 120 or 170 < words_per_minute <= 180:
            speaking_rate_score = 70
        else:
            speaking_rate_score = 50
        
        # Overall audio score (filler words + speaking rate)
        audio_quality_score = round(
            (filler_result["score"] * 0.6) + (speaking_rate_score * 0.4)
        )
        
        # FIX: Extract dominant emotion from distribution
        emotion_distribution = emotion_results['summary']['emotion_distribution']
        dominant_emotion_overall = max(emotion_distribution, key=emotion_distribution.get)
        dominant_emotion_score = emotion_distribution[dominant_emotion_overall]
        
        # Body language score (based on emotion assessment)
        emotion_summary = emotion_results['summary']
        body_language_score = round(
            (emotion_summary['confidence_score'] * 0.4) +
            (emotion_summary['professionalism_score'] * 0.4) +
            ((100 - emotion_summary['nervousness_score']) * 0.2)
        )
        
        print(f"✅ Scoring complete:")
        print(f"   Audio Quality: {audio_quality_score}/100")
        print(f"   Body Language: {body_language_score}/100")
        print(f"   Dominant Emotion: {dominant_emotion_overall} ({dominant_emotion_score:.1f}%)")
        
        print(f"\n{'='*60}")
        print(f"✅ Question {questionNumber} analysis complete!")
        print(f"{'='*60}\n")
        
        # Return comprehensive results
        result = {
            "success": True,
            "question_number": questionNumber,
            "question": question,
            "video_path": video_path,
            "frames_dir": frames_output_dir,
            "transcript": {
                "text": transcript_text,
                "word_count": stats["total_words"],
                "duration_seconds": stats["duration_seconds"],
                "words_per_minute": round(words_per_minute, 1),
                "speaking_time": stats["speaking_time_seconds"]
            },
            "filler_analysis": {
                "total_fillers": filler_result["total_fillers"],
                "filler_density": filler_result["filler_density_percentage"],
                "filler_frequency": filler_result["filler_frequency"],
                "score": filler_result["score"]
            },
            "audio_quality": {
                "speaking_rate_score": speaking_rate_score,
                "filler_score": filler_result["score"],
                "overall_score": audio_quality_score
            },
            "emotion_analysis": {
                "dominant_emotion": dominant_emotion_overall,
                "dominant_emotion_confidence": round(dominant_emotion_score, 1),
                "emotion_distribution": emotion_distribution,
                "confidence_score": emotion_summary['confidence_score'],
                "enthusiasm_score": emotion_summary['enthusiasm_score'],
                "nervousness_score": emotion_summary['nervousness_score'],
                "professionalism_score": emotion_summary['professionalism_score'],
                "emotional_tone": emotion_summary['emotional_tone'],
                "feedback": emotion_summary['interview_feedback']
            },
            "body_language": {
                "score": body_language_score,
                "appears_confident": emotion_summary['appeared_confident_percentage'] > 50,
                "appears_nervous": emotion_summary['appeared_nervous_percentage'] > 30,
                "appears_enthusiastic": emotion_summary['appeared_enthusiastic_percentage'] > 40
            },
            "overall_assessment": {
                "audio_quality_score": audio_quality_score,
                "body_language_score": body_language_score,
                "emotional_tone": emotion_summary['emotional_tone']
            }
        }
        return convert_numpy_types(result)
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"❌ ANALYSIS FAILED: {str(e)}")
        print(f"{'='*60}")
        print(error_details)
        print(f"{'='*60}\n")
        
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/test")
def test_interview_api():
    """Test endpoint"""
    return {
        "message": "Interview API is working!",
        "endpoints": {
            "analyze_answer": "POST /api/interview/analyze-answer"
        }
    }