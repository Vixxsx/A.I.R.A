import os
import cv2
import numpy as np
import urllib.request
from typing import List, Dict

class EyeTracker:
    def __init__(self):
        self.model_path = "Backend/Models/face_landmarker.task"
        
        if not os.path.exists(self.model_path):
            self._download_model()
        
        # New API imports
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        base_options = mp.tasks.BaseOptions(
            model_asset_path=self.model_path
        )
        
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        
        # Iris indices (MediaPipe 478 landmarks)
        self.LEFT_IRIS  = 468
        self.RIGHT_IRIS = 473
        self.LEFT_EYE   = [33, 133, 160, 159, 158, 157, 173, 144]
        self.RIGHT_EYE  = [362, 263, 385, 386, 387, 388, 398, 373]
        
        print("✅ Eye Tracker initialized (MediaPipe 0.10.32)")
    
    
    def _download_model(self):
        print("📥 Downloading face landmarker model (~30MB)...")
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        try:
            urllib.request.urlretrieve(url, self.model_path)
            print("✅ Model downloaded!")
        except Exception as e:
            raise Exception(
                f"Failed to download model: {e}\n"
                f"Download manually from:\n{url}\n"
                f"Save to: {self.model_path}"
            )
    
    
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        try:
            import mediapipe as mp
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self.landmarker.detect(mp_image)
            
            if not result.face_landmarks:
                return self._no_face_result()
            
            landmarks = result.face_landmarks[0]
            h, w = frame.shape[:2]
            
            score = self._eye_contact_score(landmarks, w, h)
            
            return {
                "face_detected": True,
                "eye_contact_score": round(score, 3),
                "looking_at_camera": score > 0.6,
                "gaze_direction": self._gaze_direction(score)
            }
        
        except Exception as e:
            return self._no_face_result(str(e))
    
    
    def _eye_contact_score(self, landmarks, w, h) -> float:
        """Calculate how centered iris is within eye = eye contact score"""
        
        def center(indices):
            pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in indices]
            return (
                sum(p[0] for p in pts) / len(pts),
                sum(p[1] for p in pts) / len(pts)
            )
        
        left_eye_center  = center(self.LEFT_EYE)
        right_eye_center = center(self.RIGHT_EYE)
        
        left_iris  = (landmarks[self.LEFT_IRIS].x * w,  landmarks[self.LEFT_IRIS].y * h)
        right_iris = (landmarks[self.RIGHT_IRIS].x * w, landmarks[self.RIGHT_IRIS].y * h)
        
        left_offset  = np.linalg.norm(np.array(left_iris)  - np.array(left_eye_center))
        right_offset = np.linalg.norm(np.array(right_iris) - np.array(right_eye_center))
        
        avg_offset = (left_offset + right_offset) / 2
        
        # Offset 0-20px → score 1.0-0.0
        score = max(0.0, 1.0 - (avg_offset / 20.0))
        return score
    
    
    def _gaze_direction(self, score: float) -> str:
        if score > 0.7:   return "Looking at camera"
        elif score > 0.5: return "Slightly off-center"
        elif score > 0.3: return "Looking away"
        else:             return "Not looking at camera"
    
    
    def analyze_frames_list(self, frames: List[np.ndarray]) -> Dict:
        """Analyze list of frames and return summary"""
        print(f"👁️ Analyzing eye contact in {len(frames)} frames...")
        
        results = []
        for i, frame in enumerate(frames):
            result = self.analyze_frame(frame)
            results.append(result)
        
        valid = [r for r in results if r['face_detected']]
        
        if not valid:
            return {
                "success": False,
                "summary": {
                    "eye_contact_percentage": 65.0,  # Default
                    "avg_score": 0.65,
                    "frames_with_face": 0
                }
            }
        
        eye_contact_pct = (
            sum(1 for r in valid if r['looking_at_camera']) / len(valid)
        ) * 100
        
        avg_score = sum(r['eye_contact_score'] for r in valid) / len(valid)
        
        print(f"✅ Eye contact: {eye_contact_pct:.1f}%")
        
        return {
            "success": True,
            "summary": {
                "eye_contact_percentage": round(eye_contact_pct, 1),
                "avg_score": round(avg_score, 3),
                "frames_with_face": len(valid),
                "total_frames": len(results)
            }
        }
    
    
    def _no_face_result(self, error: str = None) -> Dict:
        result = {
            "face_detected": False,
            "eye_contact_score": 0.0,
            "looking_at_camera": False,
            "gaze_direction": "unknown"
        }
        if error:
            result["error"] = error
        return result