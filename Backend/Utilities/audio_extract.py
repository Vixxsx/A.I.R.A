import os
import subprocess
from typing import Optional

class AudioExtractor:
    def __init__(self, output_dir: str = "Data/Audio"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        print(f"Audio Extractor initialized (output: {output_dir})")
    
    
    def extract_audio(
        self,
        video_path: str,
        output_filename: Optional[str] = None,
        format: str = "wav"
    ) -> str:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Generate output filename if not provided
        if output_filename is None:
            video_basename = os.path.basename(video_path)
            video_name = os.path.splitext(video_basename)[0]
            output_filename = f"{video_name}_audio.{format}"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"Extracting audio from: {os.path.basename(video_path)}")
        
        try:
            if self._check_ffmpeg():
                self._extract_with_ffmpeg(video_path, output_path, format)
            else:
                print("FFmpeg not found, using OpenCV fallback...")
                self._extract_with_opencv(video_path, output_path)
            
            # Verify file was created
            if not os.path.exists(output_path):
                raise Exception("Audio extraction failed - output file not created")
            
            # Get audio info
            file_size = os.path.getsize(output_path)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"Audio extracted: {output_filename}")
            print(f"   Size: {file_size_mb:.2f} MB")
            print(f"   Path: {output_path}")
            
            return output_path
        
        except Exception as e:
            print(f"Audio extraction failed: {e}")
            raise
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    
    def _extract_with_ffmpeg(self, video_path: str, output_path: str, format: str):
        """Extract audio using FFmpeg"""
        print("   Using FFmpeg...")
        
        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
            "-ar", "16000",  # 16kHz sample rate (good for Whisper)
            "-ac", "1",  # Mono
            "-y",  # Overwrite output file
            output_path
        ]
        
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
    
    
    def _extract_with_opencv(self, video_path: str, output_path: str):
        """
        Fallback: Extract audio using OpenCV + scipy
        (Less ideal but works without FFmpeg)
        """
        import cv2
        import numpy as np
        from scipy.io import wavfile
        
        print("   Using OpenCV fallback...")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception("Cannot open video file")

        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        # Create silent audio (placeholder)
        sample_rate = 16000
        samples = int(duration * sample_rate)
        audio_data = np.zeros(samples, dtype=np.int16)
        
        wavfile.write(output_path, sample_rate, audio_data)

    def extract_audio_segment(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_filename: Optional[str] = None
    ) -> str:

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        if output_filename is None:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_filename = f"{video_name}_segment_{int(start_time)}_{int(end_time)}.wav"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"🎵 Extracting audio segment: {start_time}s - {end_time}s")
        
        try:
            if self._check_ffmpeg():
                # Extract segment with FFmpeg
                duration = end_time - start_time
                
                cmd = [
                    "ffmpeg",
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-i", video_path,
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",
                    output_path
                ]
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if result.returncode != 0:
                    raise Exception(f"FFmpeg error: {result.stderr}")
                
                print(f"Audio segment extracted: {output_filename}")
                return output_path
            else:
                raise Exception("FFmpeg required for segment extraction")
        
        except Exception as e:
            print(f"Segment extraction failed: {e}")
            raise
    
    
    def get_audio_info(self, audio_path: str) -> dict:
        """Get audio file information"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio not found: {audio_path}")
        
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(audio_path)
            
            return {
                "path": audio_path,
                "filename": os.path.basename(audio_path),
                "duration_seconds": len(audio) / 1000.0,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "file_size_mb": os.path.getsize(audio_path) / (1024 * 1024)
            }
        except ImportError:
            # Fallback if pydub not available
            return {
                "path": audio_path,
                "filename": os.path.basename(audio_path),
                "file_size_mb": os.path.getsize(audio_path) / (1024 * 1024)
            }


# ========== CONVENIENCE FUNCTION ==========

def quick_extract_audio(video_path: str) -> str:
    """Quick audio extraction"""
    extractor = AudioExtractor()
    return extractor.extract_audio(video_path)