from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import sys
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utilities.video_utils import VideoProcessor

# Create router
router = APIRouter(prefix="/api/video", tags=["Video Processing"])

# Initialize video processor (lazy loading)
video_processor = None

def get_video_processor():
    """Get or create video processor instance"""
    global video_processor
    if video_processor is None:
        video_processor = VideoProcessor()
    return video_processor


# ============== REQUEST/RESPONSE MODELS ==============

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

@router.get("/test")
async def test_video_processor():
    """
    Quick test to verify video processor is working
    
    Returns:
        Video processor status
    """
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


@router.post("/upload", response_model=VideoInfoResponse)
async def upload_video(video: UploadFile = File(...)):
    """
    Upload a video file for processing
    
    Args:
        video: Video file (mp4, avi, mov, etc.)
    
    Returns:
        Video information
    """
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


@router.get("/info/{filename}", response_model=VideoInfoResponse)
async def get_video_info(filename: str):
    """
    Get information about an uploaded video
    
    Args:
        filename: Video filename in Data/Video/Raw/
    
    Returns:
        Video metadata
    """
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


@router.post("/extract-frames", response_model=FrameExtractionResponse)
async def extract_frames(request: FrameExtractionRequest):
    """
    Extract frames from uploaded video for AI analysis
    
    Args:
        request: Frame extraction parameters
    
    Returns:
        Frame extraction results
    """
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
        
        # Count saved frames
        frames_count = 0
        if request.save_to_disk and os.path.exists(output_folder):
            frames_count = len([f for f in os.listdir(output_folder) if f.endswith('.jpg')])
        
        return FrameExtractionResponse(
            success=True,
            frames_extracted=frames_count,
            output_folder=output_folder if request.save_to_disk else None,
            message=f"Extracted {frames_count} frames from {request.video_filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Frame extraction failed: {str(e)}"
        )


@router.get("/list")
async def list_videos():
    """
    List all uploaded videos
    
    Returns:
        List of video filenames with metadata
    """
    try:
        processor = get_video_processor()
        
        videos = []
        for filename in os.listdir(processor.raw_path):
            if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_path = os.path.join(processor.raw_path, filename)
                try:
                    info = processor.get_video_info(video_path)
                    videos.append({
                        "filename": filename,
                        "duration": info['duration_seconds'],
                        "resolution": info['resolution'],
                        "size_mb": info['file_size_mb']
                    })
                except:
                    # Skip files that can't be read
                    continue
        
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


@router.delete("/{filename}")
async def delete_video(filename: str):
    """
    Delete an uploaded video
    
    Args:
        filename: Video filename to delete
    
    Returns:
        Deletion confirmation
    """
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


@router.post("/cleanup")
async def cleanup_old_videos(older_than_hours: int = 24):
    """
    Clean up old video files
    
    Args:
        older_than_hours: Delete files older than this many hours
    
    Returns:
        Cleanup results
    """
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