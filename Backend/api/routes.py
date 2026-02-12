from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import shutil
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from Utilities.video_utils import VideoProcessor

from Models.whisper_stt import WhisperSTT
from Models.filler_word_detection import FillerWordDetector
from Models.Question_Generator import QuestionGenerator

router = APIRouter()


whisper_model = None
filler_detector = None
question_generator = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = WhisperSTT()
    return whisper_model

def get_filler_detector():
    global filler_detector
    if filler_detector is None:
        filler_detector = FillerWordDetector()
    return filler_detector

def get_question_generator():
    global question_generator
    if question_generator is None:
        question_generator = QuestionGenerator()
    return question_generator


# Pydantic models for request/response
class TranscriptionResponse(BaseModel):
    success: bool
    transcript: str
    audio_duration: Optional[float] = None
    language: Optional[str] = None

class FillerAnalysisResponse(BaseModel):
    success: bool
    analysis: Dict
    
class QuestionGeneratorRequest(BaseModel):
    """Request model for question generation"""
    job_role: Optional[str] = "Software Engineer"
    degree: Optional[str] = "Computer Science"
    experience_level: Optional[str] = "Entry Level"
    company_type: Optional[str] = "Tech Startup"
    num_questions: Optional[int] = 5

class QuestionGeneratorResponse(BaseModel):
    """Response model for question generation"""
    success: bool
    questions: List[Dict]
    profile: Dict
    message: str


# ============== EXISTING ENDPOINTS ==============

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        temp_dir = "temp_audio"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, audio.filename)
        
        with open(temp_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Transcribe
        model = get_whisper_model()
        result = model.transcribe(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return TranscriptionResponse(
            success=True,
            transcript=result["text"],
            audio_duration=result.get("duration"),
            language=result.get("language")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/analyze/fillers", response_model=FillerAnalysisResponse)
async def analyze_fillers(text: str):
    """
    Analyze text for filler words
    
    Args:
        text: Transcribed text
    
    Returns:
        Filler word analysis
    """
    try:
        detector = get_filler_detector()
        analysis = detector.analyze(text)
        
        return FillerAnalysisResponse(
            success=True,
            analysis=analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filler analysis failed: {str(e)}")


@router.post("/analyze/complete")
async def analyze_complete(audio: UploadFile = File(...)):
    """
    Complete analysis: Transcription + Filler detection
    
    Args:
        audio: Audio file
    
    Returns:
        Complete analysis result
    """
    try:
        # Save uploaded file temporarily
        temp_dir = "temp_audio"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, audio.filename)
        
        with open(temp_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Step 1: Transcribe
        whisper = get_whisper_model()
        transcription = whisper.transcribe(temp_path)
        
        # Step 2: Analyze fillers
        detector = get_filler_detector()
        filler_analysis = detector.analyze(transcription["text"])
        
        # Clean up
        os.remove(temp_path)
        
        return {
            "success": True,
            "transcription": {
                "text": transcription["text"],
                "duration": transcription.get("duration"),
                "language": transcription.get("language")
            },
            "filler_analysis": filler_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete analysis failed: {str(e)}")


@router.post("/generate-questions", response_model=QuestionGeneratorResponse)
async def generate_questions(request: QuestionGeneratorRequest):

    try:
        # Get question generator
        generator = get_question_generator()
        
        # Build profile dictionary
        profile = {
            "job_role": request.job_role,
            "degree": request.degree,
            "experience_level": request.experience_level,
            "company_type": request.company_type
        }
        
        # Generate questions
        questions = generator.generate_questions(
            profile=profile,
            num_questions=request.num_questions
        )
        
        # Determine message based on source
        if generator.client and questions:
            message = f"Generated {len(questions)} questions using GPT-4"
        else:
            message = f"Generated {len(questions)} questions using templates"
        
        return QuestionGeneratorResponse(
            success=True,
            questions=questions,
            profile=profile,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Question generation failed: {str(e)}"
        )


@router.get("/test-questions")
async def test_question_generation():
    try:
        generator = get_question_generator()
        questions = generator.generate_questions()
        
        return {
            "success": True,
            "message": "Question generation test successful",
            "num_questions": len(questions),
            "questions": questions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )

video_processor = None
def get_video_processor():
    global video_processor
    if video_processor is None:
        video_processor = VideoProcessor()
    return video_processor

class VideoInfoResponse(BaseModel):
    """Video information response model"""
    success: bool
    video_info: Dict
    message: str

class FrameExtractionRequest(BaseModel):
    """Frame extraction request model"""
    video_filename: str
    every_n: int = 10
    max_frames: Optional[int] = None
    save_to_disk: bool = True

class FrameExtractionResponse(BaseModel):
    """Frame extraction response model"""
    success: bool
    frames_extracted: int
    output_folder: Optional[str] = None
    message: str


# ============== VIDEO ENDPOINTS ==============

@router.post("/api/video/upload", response_model=VideoInfoResponse)
async def upload_video(video: UploadFile = File(...)):
    try:
        processor = get_video_processor()
        
        # Save uploaded video
        video_path = os.path.join(processor.raw_path, video.filename)
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        # Get video info
        info = processor.get_video_info(video_path)
        
        return VideoInfoResponse(
            success=True,
            video_info=info,
            message=f"Video uploaded successfully: {video.filename}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video upload failed: {str(e)}"
        )


@router.get("/api/video/info/{filename}", response_model=VideoInfoResponse)
async def get_video_info(filename: str):
    try:
        processor = get_video_processor()
        video_path = os.path.join(processor.raw_path, filename)
        
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=404,
                detail=f"Video not found: {filename}"
            )
        
        info = processor.get_video_info(video_path)
        
        return VideoInfoResponse(
            success=True,
            video_info=info,
            message="Video info retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video info: {str(e)}"
        )


@router.post("/api/video/extract-frames", response_model=FrameExtractionResponse)
async def extract_frames(request: FrameExtractionRequest):
    try:
        processor = get_video_processor()
        video_path = os.path.join(processor.raw_path, request.video_filename)
        
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=404,
                detail=f"Video not found: {request.video_filename}"
            )
        
        # Create output folder
        video_name = os.path.splitext(request.video_filename)[0]
        output_folder = os.path.join(processor.frames_path, video_name)
        
        # Extract frames
        frames = processor.extract_frames(
            video_path=video_path,
            output_folder=output_folder if request.save_to_disk else None,
            every_n=request.every_n,
            max_frames=request.max_frames,
            return_arrays=False  # Don't load all into memory for API
        )
        
        return FrameExtractionResponse(
            success=True,
            frames_extracted=len(frames) if frames else 0,
            output_folder=output_folder if request.save_to_disk else None,
            message=f"Extracted frames from {request.video_filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Frame extraction failed: {str(e)}"
        )


@router.get("/api/video/list")
async def list_videos():
    try:
        processor = get_video_processor()
        
        videos = []
        for filename in os.listdir(processor.raw_path):
            if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_path = os.path.join(processor.raw_path, filename)
                info = processor.get_video_info(video_path)
                videos.append({
                    "filename": filename,
                    "duration": info['duration_seconds'],
                    "resolution": info['resolution'],
                    "size_mb": info['file_size_mb']
                })
        
        return {
            "success": True,
            "count": len(videos),
            "videos": videos
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list videos: {str(e)}"
        )


@router.delete("/api/video/{filename}")
async def delete_video(filename: str):
    try:
        processor = get_video_processor()
        video_path = os.path.join(processor.raw_path, filename)
        
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=404,
                detail=f"Video not found: {filename}"
            )
        
        # Delete video file
        os.remove(video_path)
        
        # Delete associated frames if they exist
        video_name = os.path.splitext(filename)[0]
        frames_folder = os.path.join(processor.frames_path, video_name)
        if os.path.exists(frames_folder):
            shutil.rmtree(frames_folder)
        
        return {
            "success": True,
            "message": f"Deleted video: {filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete video: {str(e)}"
        )


@router.post("/api/video/cleanup")
async def cleanup_old_videos(older_than_hours: int = 24):
    try:
        processor = get_video_processor()
        processor.cleanup_temp_files(older_than_hours=older_than_hours)
        
        return {
            "success": True,
            "message": f"Cleaned up files older than {older_than_hours} hours"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )
@router.get("/api/video/test")
async def test_video_processor():
    try:
        processor = get_video_processor()
        
        return {
            "success": True,
            "message": "Video processor is ready",
            "paths": {
                "raw": processor.raw_path,
                "processed": processor.processed_path,
                "frames": processor.frames_path
            },
            "test_results": {
                "folders_exist": all([
                    os.path.exists(processor.raw_path),
                    os.path.exists(processor.processed_path),
                    os.path.exists(processor.frames_path)
                ])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video processor test failed: {str(e)}"
        )  
    