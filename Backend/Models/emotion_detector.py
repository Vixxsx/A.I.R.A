import cv2
import numpy as np
from typing import List, Dict, Optional
from deepface import DeepFace

class EmotionDetector:
    def __init__(self):
        self.emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        print("✅ Emotion Detector initialized (DeepFace)")
    
    
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        try:
            # DeepFace expects RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Analyze emotions
            result = DeepFace.analyze(
                rgb_frame,
                actions=['emotion'],
                enforce_detection=False,  # Don't fail if face not detected
                detector_backend='opencv',  # Faster than default
                silent=True
            )
            
            # Handle both single face and multiple faces
            if isinstance(result, list):
                result = result[0]  # Take first face
            
            emotions = result['emotion']
            dominant_emotion = result['dominant_emotion']
            
            return {
                "face_detected": True,
                "dominant_emotion": dominant_emotion,
                "emotions": emotions,
                "confidence": round(emotions[dominant_emotion], 2)
            }
        
        except Exception as e:
            # No face detected or other error
            return {
                "face_detected": False,
                "dominant_emotion": "unknown",
                "emotions": {emotion: 0 for emotion in self.emotions},
                "confidence": 0,
                "error": str(e)
            }
    
    
    def analyze_video(
        self,
        video_path: str,
        sample_rate: int = 30
    ) -> Dict:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_results = []
        frame_count = 0
        analyzed_count = 0
        
        print(f"😊 Analyzing emotions: {video_path}")
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
                    if analyzed_count % 5 == 0:
                        progress = (frame_count / total_frames) * 100
                        print(f"   Progress: {progress:.1f}% - Detected: {result['dominant_emotion']}")
                
                frame_count += 1
            
            print(f"✅ Analyzed {analyzed_count} frames")
            
            # Calculate summary
            summary = self._calculate_summary(frame_results)
            
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
        print(f"😊 Analyzing emotions in {len(frames)} frames...")
        
        frame_results = []
        
        for i, frame in enumerate(frames):
            result = self.analyze_frame(frame)
            result['frame_number'] = i
            frame_results.append(result)
            
            if (i + 1) % 5 == 0:
                print(f"   Processed {i + 1}/{len(frames)} frames")
        
        print(f"✅ Analysis complete")
        
        # Calculate summary
        summary = self._calculate_summary(frame_results)
        
        return {
            "success": True,
            "analyzed_frames": len(frames),
            "frame_results": frame_results,
            "summary": summary
        }
    
    
    def _calculate_summary(self, frame_results: List[Dict]) -> Dict:
        """Calculate emotion statistics"""
        if not frame_results:
            return {
                "dominant_emotion_overall": "unknown",
                "emotion_distribution": {},
                "average_confidence": 0,
                "frames_with_face": 0
            }
        
        # Filter frames with detected faces
        valid_results = [r for r in frame_results if r['face_detected']]
        
        if not valid_results:
            return {
                "dominant_emotion_overall": "unknown",
                "emotion_distribution": {emotion: 0 for emotion in self.emotions},
                "average_confidence": 0,
                "frames_with_face": 0,
                "face_detection_rate": 0
            }
        
        # Count emotion occurrences
        emotion_counts = {}
        for result in valid_results:
            emotion = result['dominant_emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Calculate percentages
        total_valid = len(valid_results)
        emotion_distribution = {
            emotion: round((count / total_valid) * 100, 1)
            for emotion, count in emotion_counts.items()
        }
        
        # Find most common emotion
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        # Average confidence
        avg_confidence = sum(r['confidence'] for r in valid_results) / total_valid
        
        # Emotional tone assessment
        emotional_tone = self._assess_emotional_tone(emotion_distribution)
        
        return {
            "dominant_emotion_overall": dominant_emotion,
            "emotion_distribution": emotion_distribution,
            "emotional_tone": emotional_tone,
            "average_confidence": round(avg_confidence, 2),
            "frames_with_face": len(valid_results),
            "total_frames_analyzed": len(frame_results),
            "face_detection_rate": round(len(valid_results) / len(frame_results) * 100, 1)
        }
    
    
    def _assess_emotional_tone(self, distribution: Dict[str, float]) -> str:
        """
        Assess overall emotional tone for interview
        
        Returns friendly feedback about emotional presentation
        """
        positive_emotions = distribution.get('happy', 0) + distribution.get('surprise', 0)
        neutral_emotion = distribution.get('neutral', 0)
        negative_emotions = (
            distribution.get('sad', 0) + 
            distribution.get('angry', 0) + 
            distribution.get('fear', 0)
        )
        
        if positive_emotions > 50:
            return "Very positive and enthusiastic"
        elif positive_emotions > 30:
            return "Positive and engaged"
        elif neutral_emotion > 60:
            return "Professional and composed"
        elif negative_emotions > 40:
            return "Shows signs of stress or concern"
        else:
            return "Balanced emotional expression"


# ========== CONVENIENCE FUNCTION ==========

def quick_emotion_analysis(video_path: str) -> Dict:
    """Quick emotion analysis"""
    detector = EmotionDetector()
    return detector.analyze_video(video_path)