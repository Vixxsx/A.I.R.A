import warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
import whisper
import json
import os
from datetime import datetime

class WhisperSTT:
    
    def __init__(self, model_size="base"):
        print(f"🎤 Loading Whisper '{model_size}' model...")
        self.model = whisper.load_model(model_size)
        self.model_size = model_size
        print(f"✅ Whisper model '{model_size}' loaded successfully!")
    def transcribe_audio(self, audio_path, language="en"):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        print(f"\n🎤 Transcribing: {audio_path}")
        
        result = self.model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            verbose=False,
            word_timestamps=True,  # Get word-level detail
            condition_on_previous_text=False,  # Don't clean up based on context
            compression_ratio_threshold=2.4,  # More lenient, preserves more words
            no_speech_threshold=0.6  # Lower threshold = catches more speech
        )
        raw_transcript = ""
        if "segments" in result:
            for segment in result["segments"]:
                if "words" in segment:
                    # Get each word exactly as spoken
                    for word_data in segment["words"]:
                        raw_transcript += word_data["word"] + " "
                else:
                    raw_transcript += segment["text"] + " "
        if not raw_transcript.strip():
            raw_transcript = result["text"]
        
        raw_transcript = raw_transcript.strip()
        
        transcript_data = {
            "text": raw_transcript, 
            "language": result["language"],
            "segments": self._process_segments(result["segments"]),
            "duration": result["segments"][-1]["end"] if result["segments"] else 0,
            "word_count": len(raw_transcript.split()),
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model_size,
            "audio_file": os.path.basename(audio_path)
        }
        print(f"✅ Transcription complete!")
        print(f"📝 Transcript: {transcript_data['text'][:100]}...")
        print(f"📊 Word count: {transcript_data['word_count']}")
        return transcript_data
    
    def _process_segments(self, segments):
        processed = []
        for seg in segments:
            processed.append({
                "id": seg["id"],
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip(),
                "duration": round(seg["end"] - seg["start"], 2)
            })
        return processed
    
    def get_speaking_stats(self, transcript_data):
        segments = transcript_data["segments"]
        total_duration = transcript_data["duration"]
        total_words = transcript_data["word_count"]
        speaking_time = sum(seg["duration"] for seg in segments)
        pauses = []
        for i in range(len(segments) - 1):
            pause_duration = segments[i + 1]["start"] - segments[i]["end"]
            if pause_duration > 0.5:  # Only count pauses > 0.5 seconds
                pauses.append({
                    "after_segment": i,
                    "duration": round(pause_duration, 2)
                })
        
        stats = {
            "total_words": total_words,
            "duration_seconds": round(total_duration, 2),
            "speaking_time_seconds": round(speaking_time, 2),
            "words_per_minute": round((total_words / speaking_time) * 60, 2) if speaking_time > 0 else 0,
            "pause_time_seconds": round(total_duration - speaking_time, 2),
            "number_of_pauses": len(pauses),
            "average_pause_duration": round(sum(p["duration"] for p in pauses) / len(pauses), 2) if pauses else 0,
            "longest_pause": max((p["duration"] for p in pauses), default=0)
        }
        
        return stats
    
    def save_transcript(self, transcript_data, filename=None, output_dir="Data/Transcript"):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcript_{timestamp}.json"
        
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        output_path = os.path.join(output_dir, filename)
        
        # Save to JSON file (save entire transcript_data)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Transcript saved: {output_path}")
        return output_path
    
    def load_transcript(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Transcript not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Transcript loaded: {filepath}")
        return data
    
    def transcribe_and_save(self, audio_path, save_transcript=True):
        result = self.model.transcribe(
            audio_path,
            language="en",           # Force English — stops it guessing wrong language mid-sentence
            initial_prompt=(
                "This is a professional job interview. "
                "The candidate is discussing work experience, deadlines, teamwork, "
                "group projects, technical skills, and career goals."
            ),
            temperature=0.0,         # Greedy decoding — more deterministic, less hallucination
            best_of=1,               # No sampling
            beam_size=5,             # Better beam search
            condition_on_previous_text=True,
        )
        saved_path = None
        if save_transcript:
            audio_name = os.path.splitext(os.path.basename(audio_path))[0]
            transcript_filename = f"{audio_name}_transcript.json"
            saved_path = self.save_transcript(result, filename=transcript_filename)
        
        return {
            "transcription": result,
            "saved_to": saved_path
        }


# ========== TESTING==========

def test_whisper():
    """Test Whisper with sample audio"""
    print("="*70)
    print("🧪 WHISPER TESTING")
    print("="*70)
    
    # Initialize Whisper
    stt = WhisperSTT(model_size="medium")
    
    # Test audio file path
    test_audio = "Data/Audio/test_audio.wav"
    
    if not os.path.exists(test_audio):
        print(f"\n⚠️ Test audio file not found: {test_audio}")
        return
    print("\n" + "="*70)
    transcript = stt.transcribe_audio(test_audio)
    stats = stt.get_speaking_stats(transcript)
    print("\n" + "="*70)
    print("📊 TRANSCRIPTION RESULTS")
    print("="*70)
    print(f"\n📝 Full Transcript:\n{transcript['text']}\n")
    print("="*70)
    print("⏱️ SPEAKING STATISTICS:")
    print("="*70)
    for key, value in stats.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    print("\n" + "="*70)
    output_path = stt.save_transcript(transcript)
    
    print("\n" + "="*70)
    print("✅ TRANSCRIPTION COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    test_whisper()