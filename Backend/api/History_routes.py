"""
Interview History Routes
Stores and retrieves interview summaries
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from datetime import datetime

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

# Storage path
REPORT_DIR = "Data/Report"
INTERVIEWS_FILE = os.path.join(REPORT_DIR, "interviews.json")

# Ensure directory exists
os.makedirs(REPORT_DIR, exist_ok=True)


class InterviewSummary(BaseModel):
    interview_id: str
    username: str
    timestamp: str
    job_role: str
    grade: str
    overall_score: int
    questions_answered:int=0


def load_interviews() -> List[dict]:
    """Load all interviews from JSON file"""
    if not os.path.exists(INTERVIEWS_FILE):
        return []
    
    try:
        with open(INTERVIEWS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_interviews(interviews: List[dict]):
    """Save interviews to JSON file"""
    with open(INTERVIEWS_FILE, 'w') as f:
        json.dump(interviews, f, indent=2)


@router.post("/save")
async def save_interview(summary: InterviewSummary):
    """
    Save interview summary after completion
    
    Called from scorecard after calculating final grade
    """
    try:
        print(f"\n{'='*60}")
        print(f"💾 Saving Interview Summary")
        print(f"   User: {summary.username}")
        print(f"   Job Role: {summary.job_role}")
        print(f"   Grade: {summary.grade}")
        print(f"   Score: {summary.overall_score}")
        print(f"{'='*60}\n")
        
        # Load existing interviews
        interviews = load_interviews()
        
        # Add new interview
        interviews.append({
            "interview_id": summary.interview_id,
            "username": summary.username,
            "timestamp": summary.timestamp,
            "job_role": summary.job_role,
            "grade": summary.grade,
            "overall_score": summary.overall_score,
            "questions_answered":  summary.questions_answered
        })
        
        # Keep only most recent 50 interviews per user
        # Group by username
        by_user = {}
        for interview in interviews:
            user = interview['username']
            if user not in by_user:
                by_user[user] = []
            by_user[user].append(interview)
        
        # Keep only 50 most recent per user
        filtered = []
        for user, user_interviews in by_user.items():
            # Sort by timestamp descending
            user_interviews.sort(key=lambda x: x['timestamp'], reverse=True)
            filtered.extend(user_interviews[:50])
        
        # Save back
        save_interviews(filtered)
        
        print(f"✅ Interview saved successfully")
        
        return {
            "success": True,
            "message": "Interview summary saved"
        }
    
    except Exception as e:
        print(f"❌ Error saving interview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save interview: {str(e)}"
        )


@router.get("/recent")
async def get_recent_interviews(username: str, limit: int = 5):
    try:
        print(f"\n📋 Fetching recent interviews for: {username}")
        interviews = load_interviews()

        user_interviews = [
            interview for interview in interviews 
            if interview['username'].lower() == username.lower()
        ]
        # Sort by timestamp descending (most recent first)
        user_interviews.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Return only requested number
        recent = user_interviews[:limit]
        
        print(f"✅ Found {len(recent)} recent interviews")
        
        return {
            "success": True,
            "count": len(recent),
            "interviews": recent
        }
    
    except Exception as e:
        print(f"❌ Error fetching interviews: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch interviews: {str(e)}"
        )


@router.get("/stats")
async def get_user_stats(username: str):
    """
    Get statistics for a user's interviews
    
    Returns:
        - Total interviews
        - Average score
        - Grade distribution
        - Best/worst scores
    """
    try:
        interviews = load_interviews()
        user_interviews = [
            i for i in interviews 
            if i['username'].lower() == username.lower()
        ]
        
        if not user_interviews:
            return {
                "success": True,
                "total_interviews": 0,
                "average_score": 0,
                "grade_distribution": {},
                "best_score": 0,
                "worst_score": 0
            }
        
        # Calculate stats
        total = len(user_interviews)
        scores = [i['overall_score'] for i in user_interviews]
        avg_score = sum(scores) / len(scores)
        
        # Grade distribution
        grade_dist = {}
        for interview in user_interviews:
            grade = interview['grade']
            grade_dist[grade] = grade_dist.get(grade, 0) + 1
        
        return {
            "success": True,
            "total_interviews": total,
            "average_score": round(avg_score, 1),
            "grade_distribution": grade_dist,
            "best_score": max(scores),
            "worst_score": min(scores)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )


@router.delete("/clear")
async def clear_user_interviews(username: str):
    """
    Clear all interviews for a user (for testing)
    """
    try:
        interviews = load_interviews()
        
        # Filter out user's interviews
        interviews = [
            i for i in interviews 
            if i['username'].lower() != username.lower()
        ]
        
        save_interviews(interviews)
        
        return {
            "success": True,
            "message": f"Cleared all interviews for {username}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear interviews: {str(e)}"
        )


@router.get("/test")
def test_history_api():
    """Test endpoint"""
    return {
        "message": "Interview History API is working!",
        "storage": INTERVIEWS_FILE,
        "endpoints": {
            "save": "POST /api/interviews/save",
            "recent": "GET /api/interviews/recent?username=X&limit=5",
            "stats": "GET /api/interviews/stats?username=X",
            "clear": "DELETE /api/interviews/clear?username=X"
        }
    }