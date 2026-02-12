import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import mediapipe as mp

class EyeTracker:
    def __init__(self):
        """Initialize MediaPipe Face Mesh"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Key landmark indices for eyes
        # Left eye: 33, 133, 160, 159, 158, 157, 173, 144
        # Right eye: 362, 263, 385, 386, 387, 388, 398, 373
        self.LEFT_EYE_INDICES = [33, 133, 160, 159, 158, 157, 173, 144]
        self.RIGHT_EYE_INDICES = [362, 263, 385, 386, 387, 388, 398, 373]
        
        # Iris landmarks (added in refine_landmarks=True)
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]
        
        print("✅ Eye Tracker initialized (MediaPipe Face Mesh)")
    
    
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """
        Analyze single frame for eye contact
        
        Args:
            frame: Video frame (BGR format)
        
        Returns:
            Dictionary with eye tracking results
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return {
                "face_detected": False,
                "eye_contact": False,
                "looking_at_camera": False,
                "gaze_direction": "unknown"
            }
        
        # Get face landmarks
        face_landmarks = results.multi_face_landmarks[0]
        
        # Calculate eye contact
        eye_contact_score = self._calculate_eye_contact(face_landmarks, frame.shape)
        
        # Determine gaze direction
        gaze_direction = self._get_gaze_direction(eye_contact_score)
        
        return {
            "face_detected": True,
            "eye_contact": eye_contact_score > 0.6,  # Threshold for "looking at camera"
            "eye_contact_score": round(eye_contact_score, 3),
            "gaze_direction": gaze_direction,
            "looking_at_camera": eye_contact_score > 0.6
        }
    
    
    def analyze_video(
        self,
        video_path: str,
        sample_rate: int = 30
    ) -> Dict:
        """
        Analyze entire video for eye contact patterns
        
        Args:
            video_path: Path to video file
            sample_rate: Analyze every Nth frame (default: 30 = ~1 per second at 30fps)
        
        Returns:
            Complete eye tracking analysis
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_results = []
        frame_count = 0
        analyzed_count = 0
        
        print(f"📹 Analyzing video: {video_path}")
        print(f"   FPS: {fps}, Total frames: {total_frames}")
        print(f"   Sampling every {sample_rate} frames")
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Analyze every Nth frame
                if frame_count % sample_rate == 0:
                    result = self.analyze_frame(frame)
                    result['frame_number'] = frame_count
                    result['timestamp'] = frame_count / fps
                    frame_results.append(result)
                    analyzed_count += 1
                    
                    # Progress update
                    if analyzed_count % 10 == 0:
                        progress = (frame_count / total_frames) * 100
                        print(f"   Progress: {progress:.1f}%")
                
                frame_count += 1
            
            print(f"✅ Analyzed {analyzed_count} frames")
            
            # Calculate summary statistics
            summary = self._calculate_summary(frame_results, fps, total_frames)
            
            return {
                "success": True,
                "video_path": video_path,
                "total_frames": total_frames,
                "analyzed_frames": analyzed_count,
                "fps": fps,
                "duration_seconds": total_frames / fps,
                "frame_results": frame_results,
                "summary": summary
            }
        
        finally:
            cap.release()
    
    
    def analyze_frames_list(self, frames: List[np.ndarray]) -> Dict:
        """
        Analyze a list of frames (already extracted)
        
        Args:
            frames: List of video frames
        
        Returns:
            Eye tracking analysis
        """
        print(f"📹 Analyzing {len(frames)} frames...")
        
        frame_results = []
        
        for i, frame in enumerate(frames):
            result = self.analyze_frame(frame)
            result['frame_number'] = i
            frame_results.append(result)
            
            if (i + 1) % 10 == 0:
                print(f"   Processed {i + 1}/{len(frames)} frames")
        
        print(f"✅ Analysis complete")
        
        # Calculate summary
        summary = self._calculate_summary(frame_results, fps=30, total_frames=len(frames))
        
        return {
            "success": True,
            "analyzed_frames": len(frames),
            "frame_results": frame_results,
            "summary": summary
        }
    
    
    def _calculate_eye_contact(
        self,
        face_landmarks,
        frame_shape: Tuple[int, int, int]
    ) -> float:
        """
        Calculate eye contact score (0-1)
        
        Higher score = more likely looking at camera
        """
        height, width = frame_shape[:2]
        
        # Get iris centers
        left_iris_center = self._get_landmark_point(
            face_landmarks.landmark[468],
            width,
            height
        )
        right_iris_center = self._get_landmark_point(
            face_landmarks.landmark[473],
            width,
            height
        )
        
        # Get eye centers
        left_eye_center = self._get_eye_center(
            face_landmarks,
            self.LEFT_EYE_INDICES,
            width,
            height
        )
        right_eye_center = self._get_eye_center(
            face_landmarks,
            self.RIGHT_EYE_INDICES,
            width,
            height
        )
        
        # Calculate iris offset from eye center
        left_offset = np.linalg.norm(
            np.array(left_iris_center) - np.array(left_eye_center)
        )
        right_offset = np.linalg.norm(
            np.array(right_iris_center) - np.array(right_eye_center)
        )
        
        # Average offset
        avg_offset = (left_offset + right_offset) / 2
        
        # Convert to score (smaller offset = better eye contact)
        # Normalize: offset of 0-20 pixels mapped to score 1.0-0.0
        score = max(0, 1.0 - (avg_offset / 20.0))
        
        return score
    
    
    def _get_eye_center(
        self,
        face_landmarks,
        eye_indices: List[int],
        width: int,
        height: int
    ) -> Tuple[float, float]:
        """Get center point of eye"""
        points = [
            self._get_landmark_point(face_landmarks.landmark[i], width, height)
            for i in eye_indices
        ]
        
        center_x = sum(p[0] for p in points) / len(points)
        center_y = sum(p[1] for p in points) / len(points)
        
        return (center_x, center_y)
    
    
    def _get_landmark_point(
        self,
        landmark,
        width: int,
        height: int
    ) -> Tuple[float, float]:
        """Convert normalized landmark to pixel coordinates"""
        return (landmark.x * width, landmark.y * height)
    
    
    def _get_gaze_direction(self, eye_contact_score: float) -> str:
        """Determine gaze direction from score"""
        if eye_contact_score > 0.7:
            return "center"
        elif eye_contact_score > 0.5:
            return "mostly_center"
        elif eye_contact_score > 0.3:
            return "off_center"
        else:
            return "away"
    
    
    def _calculate_summary(
        self,
        frame_results: List[Dict],
        fps: float,
        total_frames: int
    ) -> Dict:
        """Calculate summary statistics"""
        if not frame_results:
            return {
                "eye_contact_percentage": 0,
                "average_score": 0,
                "frames_with_face": 0,
                "frames_looking_at_camera": 0
            }
        
        frames_with_face = sum(1 for r in frame_results if r['face_detected'])
        frames_looking = sum(1 for r in frame_results if r.get('looking_at_camera', False))
        
        scores = [r.get('eye_contact_score', 0) for r in frame_results if r['face_detected']]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Calculate percentage based on frames with detected face
        eye_contact_percentage = (frames_looking / frames_with_face * 100) if frames_with_face > 0 else 0
        
        return {
            "eye_contact_percentage": round(eye_contact_percentage, 1),
            "average_eye_contact_score": round(avg_score, 3),
            "frames_with_face_detected": frames_with_face,
            "frames_looking_at_camera": frames_looking,
            "total_analyzed_frames": len(frame_results),
            "face_detection_rate": round(frames_with_face / len(frame_results) * 100, 1) if frame_results else 0
        }
    
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()


# ========== CONVENIENCE FUNCTION ==========

def quick_eye_analysis(video_path: str) -> Dict:
    """Quick eye tracking analysis"""
    tracker = EyeTracker()
    return tracker.analyze_video(video_path)