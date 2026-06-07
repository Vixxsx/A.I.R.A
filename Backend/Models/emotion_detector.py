import os
import numpy as np
from typing import List, Dict, Optional
from deepface import DeepFace

os.environ["DISPLAY"] = ""
os.environ["MPLBACKEND"] = "Agg"

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ cv2 not available - emotion detection will use fallback")


class EmotionDetector:
    def __init__(self):
        self.basic_emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

        self.interview_emotions = {
            'confident':   ['happy', 'neutral'],
            'enthusiastic':['happy', 'surprise'],
            'nervous':     ['fear', 'sad'],
            'composed':    ['neutral'],
            'engaged':     ['happy', 'surprise', 'neutral']
        }

        self.DOMINANCE_THRESHOLD = 40
        self.NEUTRAL_FALLBACK    = True

        print("✅ Emotion Detector initialized (DeepFace - Interview Mode)")

    def _resolve_dominant(self, emotions: Dict[str, float]) -> str:
        dominant       = max(emotions, key=emotions.get)
        dominant_score = emotions[dominant]

        if self.NEUTRAL_FALLBACK and dominant != 'neutral':
            if dominant_score < self.DOMINANCE_THRESHOLD:
                return 'neutral'
            neutral_score = emotions.get('neutral', 0)
            if dominant_score - neutral_score < 10:
                return 'neutral'

        return dominant

    def analyze_frame(self, frame: np.ndarray) -> Dict:
        try:
            if CV2_AVAILABLE:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_frame = frame

            result = DeepFace.analyze(
                rgb_frame,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend='opencv',
                silent=True
            )

            if isinstance(result, list):
                result = result[0]

            emotions         = result['emotion']
            dominant_emotion = self._resolve_dominant(emotions)
            interview_assessment = self._assess_for_interview(emotions)

            return {
                "face_detected":      True,
                "dominant_emotion":   dominant_emotion,
                "emotions":           emotions,
                "confidence":         round(emotions[dominant_emotion], 2),
                "interview_assessment": interview_assessment
            }

        except Exception as e:
            return {
                "face_detected":    False,
                "dominant_emotion": "unknown",
                "emotions":         {emotion: 0 for emotion in self.basic_emotions},
                "confidence":       0,
                "interview_assessment": {
                    "appears_confident":   False,
                    "appears_enthusiastic":False,
                    "appears_nervous":     False,
                    "overall_impression":  "Unable to detect"
                },
                "error": str(e)
            }

    def _assess_for_interview(self, emotions: Dict[str, float]) -> Dict:
        confidence_score     = emotions.get('happy', 0) * 0.6 + emotions.get('neutral', 0) * 0.4
        enthusiasm_score     = emotions.get('happy', 0) * 0.7 + emotions.get('surprise', 0) * 0.3
        nervousness_score    = emotions.get('fear',  0) * 0.6 + emotions.get('sad', 0) * 0.4
        professionalism_score= emotions.get('neutral', 0)

        appears_confident    = confidence_score    > 35
        appears_enthusiastic = enthusiasm_score    > 30
        appears_nervous      = nervousness_score   > 25
        appears_professional = professionalism_score > 40

        if appears_enthusiastic and appears_confident:
            overall = "Very positive - enthusiastic and confident"
        elif appears_confident and appears_professional:
            overall = "Professional and composed"
        elif appears_enthusiastic:
            overall = "Engaged and positive"
        elif appears_nervous and nervousness_score > 40:
            overall = "Noticeably anxious - may need to relax"
        elif appears_nervous:
            overall = "Slight nervousness detected"
        elif appears_professional:
            overall = "Calm and professional demeanor"
        else:
            overall = "Balanced emotional expression"

        return {
            "confidence_score":      round(confidence_score, 1),
            "enthusiasm_score":      round(enthusiasm_score, 1),
            "nervousness_score":     round(nervousness_score, 1),
            "professionalism_score": round(professionalism_score, 1),
            "appears_confident":     appears_confident,
            "appears_enthusiastic":  appears_enthusiastic,
            "appears_nervous":       appears_nervous,
            "appears_professional":  appears_professional,
            "overall_impression":    overall
        }

    def analyze_video(self, video_path: str, sample_rate: int = 30) -> Dict:
        if not CV2_AVAILABLE:
            raise Exception("cv2 not available for video analysis")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}")

        fps          = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_results  = []
        frame_count    = 0
        analyzed_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % sample_rate == 0:
                    result = self.analyze_frame(frame)
                    result['frame_number'] = frame_count
                    result['timestamp']    = frame_count / fps
                    frame_results.append(result)
                    analyzed_count += 1
                frame_count += 1

            summary = self._calculate_interview_summary(frame_results)
            return {
                "success":          True,
                "video_path":       video_path,
                "total_frames":     total_frames,
                "analyzed_frames":  analyzed_count,
                "fps":              fps,
                "duration_seconds": total_frames / fps,
                "frame_results":    frame_results,
                "summary":          summary
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

        summary = self._calculate_interview_summary(frame_results)
        return {
            "success":         True,
            "analyzed_frames": len(frames),
            "frame_results":   frame_results,
            "summary":         summary
        }

    def _calculate_interview_summary(self, frame_results: List[Dict]) -> Dict:
        if not frame_results:
            return self._empty_summary()

        valid_results = [r for r in frame_results if r['face_detected']]
        if not valid_results:
            return self._empty_summary()

        emotion_totals = {emotion: 0 for emotion in self.basic_emotions}
        for result in valid_results:
            for emotion, value in result['emotions'].items():
                emotion_totals[emotion] += value

        total_valid      = len(valid_results)
        emotion_averages = {e: t / total_valid for e, t in emotion_totals.items()}
        overall_dominant = self._resolve_dominant(emotion_averages)

        avg_confidence      = sum(r['interview_assessment']['confidence_score']     for r in valid_results) / total_valid
        avg_enthusiasm      = sum(r['interview_assessment']['enthusiasm_score']      for r in valid_results) / total_valid
        avg_nervousness     = sum(r['interview_assessment']['nervousness_score']     for r in valid_results) / total_valid
        avg_professionalism = sum(r['interview_assessment']['professionalism_score'] for r in valid_results) / total_valid

        confident_pct    = sum(1 for r in valid_results if r['interview_assessment']['appears_confident'])    / total_valid * 100
        enthusiastic_pct = sum(1 for r in valid_results if r['interview_assessment']['appears_enthusiastic']) / total_valid * 100
        nervous_pct      = sum(1 for r in valid_results if r['interview_assessment']['appears_nervous'])      / total_valid * 100

        overall_tone = self._determine_overall_tone(avg_confidence, avg_enthusiasm, avg_nervousness, avg_professionalism)
        feedback     = self._generate_interview_feedback(confident_pct, enthusiastic_pct, nervous_pct, overall_tone)

        return {
            "dominant_emotion":                 overall_dominant,
            "confidence_score":                 round(avg_confidence, 1),
            "enthusiasm_score":                 round(avg_enthusiasm, 1),
            "nervousness_score":                round(avg_nervousness, 1),
            "professionalism_score":            round(avg_professionalism, 1),
            "appeared_confident_percentage":    round(confident_pct, 1),
            "appeared_enthusiastic_percentage": round(enthusiastic_pct, 1),
            "appeared_nervous_percentage":      round(nervous_pct, 1),
            "emotion_distribution":             {e: round(a, 1) for e, a in emotion_averages.items()},
            "emotional_tone":                   overall_tone,
            "interview_feedback":               feedback,
            "frames_with_face":                 total_valid,
            "total_frames_analyzed":            len(frame_results),
            "face_detection_rate":              round(total_valid / len(frame_results) * 100, 1)
        }

    def _determine_overall_tone(self, confidence, enthusiasm, nervousness, professionalism) -> str:
        if enthusiasm > 40 and confidence > 40:
            return "Highly enthusiastic and confident"
        elif confidence > 40 and professionalism > 50:
            return "Professional and composed"
        elif enthusiasm > 35:
            return "Engaged and positive"
        elif nervousness > 35:
            return "Shows noticeable nervousness"
        elif professionalism > 60:
            return "Very professional demeanor"
        elif confidence > 30:
            return "Generally confident"
        else:
            return "Neutral professional expression"

    def _generate_interview_feedback(self, confident_pct, enthusiastic_pct, nervous_pct, overall_tone) -> str:
        parts = []
        if confident_pct > 70:
            parts.append("You project strong confidence throughout.")
        elif confident_pct < 40:
            parts.append("Try to show more confidence in your expressions.")
        if enthusiastic_pct > 60:
            parts.append("Your enthusiasm comes through clearly!")
        elif enthusiastic_pct < 30:
            parts.append("Consider showing more enthusiasm when discussing your interests.")
        if nervous_pct > 50:
            parts.append("Try to relax - take deep breaths before answering.")
        elif nervous_pct > 30:
            parts.append("Some nervousness detected - remember to stay calm.")
        if not parts:
            parts.append("Good emotional control and professional demeanor.")
        return " ".join(parts)

    def _empty_summary(self) -> Dict:
        return {
            "dominant_emotion":                 "neutral",
            "confidence_score":                 0,
            "enthusiasm_score":                 0,
            "nervousness_score":                0,
            "professionalism_score":            0,
            "appeared_confident_percentage":    0,
            "appeared_enthusiastic_percentage": 0,
            "appeared_nervous_percentage":      0,
            "emotion_distribution":             {e: 0 for e in self.basic_emotions},
            "emotional_tone":                   "Unable to detect emotions",
            "interview_feedback":               "No face detected in video",
            "frames_with_face":                 0,
            "total_frames_analyzed":            0,
            "face_detection_rate":              0
        }


def quick_emotion_analysis(video_path: str) -> Dict:
    return EmotionDetector().analyze_video(video_path)