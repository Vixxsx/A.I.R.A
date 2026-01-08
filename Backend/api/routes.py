from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os

# Import models
from models.whisper_stt import WhisperSTT
from models.filler_word_detection import FillerWordDetector
from models.Question_Generator import QuestionGenerator

# Initialize router
router = APIRouter()

# Initialize models (lazy loading for better performance)
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