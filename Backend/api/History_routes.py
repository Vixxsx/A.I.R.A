"""
Interview History Routes
Stores and retrieves interview summaries via MySQL
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from Backend.Utilities.database import db

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


class InterviewSummary(BaseModel):
    interview_id: str
    username: str
    timestamp: str
    job_role: str
    grade: str
    overall_score: int
    questions_answered: int = 0


@router.post("/save")
async def save_interview(summary: InterviewSummary):
    """Save interview summary to MySQL"""
    try:
        print(f"\n{'='*60}")
        print(f"💾 Saving Interview Summary")
        print(f"   User:     {summary.username}")
        print(f"   Job Role: {summary.job_role}")
        print(f"   Grade:    {summary.grade}")
        print(f"   Score:    {summary.overall_score}")
        print(f"{'='*60}\n")

        success = db.save_interview(summary.dict())

        if success:
            return {"success": True, "message": "Interview summary saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save interview")

    except Exception as e:
        print(f"❌ Error saving interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save interview: {str(e)}")


@router.get("/recent")
async def get_recent_interviews(username: str, limit: int = 5):
    """Get recent interviews for a user from MySQL"""
    try:
        print(f"\n📋 Fetching recent interviews for: {username}")
        interviews = db.get_recent_interviews(username, limit)
        print(f"✅ Found {len(interviews)} interviews")

        return {
            "success": True,
            "count": len(interviews),
            "interviews": interviews
        }

    except Exception as e:
        print(f"❌ Error fetching interviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch interviews: {str(e)}")


@router.get("/stats")
async def get_user_stats(username: str):
    """Get statistics for a user"""
    try:
        stats = db.get_user_stats(username)

        return {
            "success": True,
            **stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.delete("/clear")
async def clear_user_interviews(username: str):
    """Clear all interviews for a user"""
    try:
        success = db.clear_user_interviews(username)

        if success:
            return {"success": True, "message": f"Cleared all interviews for {username}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear interviews")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear interviews: {str(e)}")


@router.get("/test")
def test_history_api():
    """Test endpoint"""
    return {
        "message": "Interview History API is working!",
        "storage": "MySQL Database",
        "endpoints": {
            "save":   "POST /api/interviews/save",
            "recent": "GET  /api/interviews/recent?username=X&limit=5",
            "stats":  "GET  /api/interviews/stats?username=X",
            "clear":  "DELETE /api/interviews/clear?username=X"
        }
    }