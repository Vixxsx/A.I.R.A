"""
Question Generation Routes
Uses the Question_Generator model to generate interview questions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Import your existing Question Generator
from Backend.Models.Question_Generator import QuestionGenerator

router = APIRouter(prefix="/api/questions", tags=["questions"])

# Initialize the generator
question_generator = QuestionGenerator()

class QuestionRequest(BaseModel):
    jobRole: str
    difficulty: str
    count: int
    type: str  # behavioral, technical, or mixed

@router.post("/generate")
async def generate_questions(request: QuestionRequest):
    """
    Generate interview questions based on job role and preferences
    
    Args:
        jobRole: The job position (e.g., "Software Engineer")
        difficulty: beginner, intermediate, or advanced
        count: Number of questions to generate (1-10)
        type: behavioral, technical, or mixed
    
    Returns:
        List of interview questions
    """
    
    try:
        print(f"\n{'='*60}")
        print(f"📝 Generating Questions")
        print(f"   Job Role: {request.jobRole}")
        print(f"   Difficulty: {request.difficulty}")
        print(f"   Count: {request.count}")
        print(f"   Type: {request.type}")
        print(f"{'='*60}\n")
        
        # Generate questions using your model
        profile={
            "job_role": request.jobRole,
            "difficulty": request.difficulty,
            "degree": 'Computer Science',
            "company_type": 'Tech Company',
        }
        result=question_generator.generate_questions(
            profile=profile,
            num_questions=request.count
        )
        questions=[q['question'] for q in result]
        
        print(f"✅ Generated {len(questions)} questions")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "questions": questions,
            "metadata": {
                "job_role": request.jobRole,
                "difficulty": request.difficulty,
                "count": len(questions),
                "type": request.type
            }
        }
    
    except Exception as e:
        print(f"❌ Question generation failed: {str(e)}")
        
        # Fallback to basic questions if generation fails
        fallback_questions = {
            "behavioral": [
                "Tell me about a time when you faced a significant challenge at work. How did you handle it?",
                "Describe a situation where you had to work with a difficult team member.",
                "Give me an example of a goal you set and how you achieved it.",
                "Tell me about a time you failed. What did you learn from it?",
                "Describe a time when you had to adapt to a major change at work."
            ],
            "technical": [
                f"Explain your experience with the main technologies used in a {request.jobRole} role.",
                "Walk me through how you would approach a complex technical problem.",
                "What's the most challenging technical project you've worked on?",
                "How do you stay updated with the latest developments in your field?",
                "Describe your development process from requirements to deployment."
            ],
            "mixed": [
                f"Tell me about your experience as a {request.jobRole}.",
                "Describe a challenging project you worked on and how you overcame obstacles.",
                "Where do you see yourself professionally in 5 years?",
                "How do you handle disagreements with team members?",
                f"Why are you interested in working as a {request.jobRole}?"
            ]
        }
        
        question_type = request.type if request.type in fallback_questions else "mixed"
        fallback = fallback_questions[question_type][:request.count]
        
        return {
            "success": True,
            "questions": fallback,
            "fallback": True,
            "metadata": {
                "job_role": request.jobRole,
                "difficulty": request.difficulty,
                "count": len(fallback),
                "type": request.type
            }
        }


@router.get("/test")
def test_questions_api():
    """Test endpoint"""
    return {
        "message": "Questions API is working!",
        "endpoints": {
            "generate": "POST /api/questions/generate"
        }
    }