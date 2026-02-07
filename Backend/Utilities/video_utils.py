import cv2
import os
import numpy as np
from datetime import datetime
from typing import List,Tuple,Dict,Optional
import json

class VideoProcessor():
    def __init__(self, base_path: str = "Data/Video"):
        self.base_path = base_path
        self.raw_path = os.path.join(base_path, "Raw")
        self.processed_path = os.path.join(base_path, "Processed")
        self.frames_path = os.path.join(base_path, "Frames")

    def test_webcam(self, camera_index: int = 0) -> bool:
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                print(f"❌ Camera {camera_index} not accessible")
                return False
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                print(f" Camera {camera_index} working!")
                print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
                return True
            else:
                print(f"Could not read from camera {camera_index}")
                return False
                
        except Exception as e:
            print(f"Camera test failed: {e}")
            return False
    
    
    def get_available_cameras(self) -> List[int]:
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
                cap.release()
        print(f"Available cameras: {available}")
        return available
    def capture_video(self,duration:int=10,camera_index:int=0,filename:Optional[str]=None,fps:int=30)->str:
        if filename is None:
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            filename=f"video_{timestamp}.mp4"
        output_path=os.path.join(self.raw_path,filename)
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise Exception(f"Camera {camera_index} not accessible")
        width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc=cv2.VideoWriter_fourcc(*'mp4v')
        out=cv2.VideoWriter(output_path,fourcc,fps,(width,height))
        print("Recording started...")
        print("Resolution:",width,"x",height,"FPS:",fps)

        frame_count=0
        total_frames=duration*fps
        try:
            while frame_count<total_frames:
                ret,frame=cap.read()
                if ret:
                    out.write(frame)
                    frame_count+=1
                    if frame_count%(fps*2)==0:
                        elapsed=frame_count//fps
                        print(" Recorded",elapsed,"seconds")
                    else:
                        print("Frame read Failed")
                        break

        finally:
            cap.release()
            out.release()
        print("Video Saved to",output_path)
        return output_path
    def video_info(self,video_path:str)->Dict[str,any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file",video_path, "does not exist")
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

        if not cap.isOpened():
            raise Exception("Could not open video file",video_path)
        try:
            fps=cap.get(cv2.CAP_PROP_FPS)
            frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration=frame_count/fps if fps>0 else 0
            file_size=os.path.getsize(video_path)
            file_size_mb=file_size/(1024*1024)
            info={
                "path":video_path,
                "filename":os.path.basename(video_path),
                "fps":fps,
                "frame_count":frame_count,
                "width":width,
                "height":height,
                "resolution":f"{width}x{height}",
                "duration_seconds":duration,
                "duration_formatted":self._format_duration(duration),
                "file_size_bytes":file_size,
                "file_size_mb":file_size_mb
            }
            return info
        finally:
            cap.release()
    def extract_frames(self,video_path:str,output_folder:Optional[str]=None,every_nth:int=10,max_frames:Optional[int]=None,return_arrays:bool=True)->List[np.ndarray]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file",video_path, "does not exist")
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise Exception("Could not open video file",video_path)
        if output_folder:
            os.makedirs(output_folder,exist_ok=True)
        frames=[]
        frame_index=0
        extracted_count=0
        saved_count=0
        print("Extracting frames from ",os.path.basename(video_path))
        print("Every Nth Frame:",every_nth)
        try:
            while True:
                ret,frame=cap.read()
                if not ret:
                    break
                if frame_index%every_nth==0:
                    if output_folder:
                        frame_filename=f"frame_{frame_index:06d}.jpg"
                        frame_path=os.path.join(output_folder,frame_filename)
                        cv2.imwrite(frame_path,frame)
                    if return_arrays:
                        frames.append(frame)
                    saved_count+=1
                    if max_frames and extracted_count>=max_frames:
                        print("Reached max frames limit:",max_frames)
                        break
                frame_index+=1
            print("Total frames extracted:",extracted_count)
            if output_folder:
                print("Frames saved to:",output_folder)
            return frames
        finally:
            cap.release()

    def extract_frames_by_time(self,video_path:str,timestamps:List[float],output_folder:Optional[str]=None,)->List[np.ndarray]:
        if not os.path.exists(video_path):
            raise FileNotFoundError("Video not found:",video_path)
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        fps=cap.get(cv2.CAP_PROP_FPS)
        if output_folder:
            os.makedirs(output_folder,exist_ok=True)
        frames=[]
        print("Extracting frames at specified timestamps from",os.path.basename(video_path))
        for i,timestamps in enumerate(timestamps):
            frame_number=int(timestamps*fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES,frame_number)
            ret,frame=cap.read()
            if ret:
                frames.append(frame)
                if output_folder:
                    frame_filename=f"frame_at_{int(timestamps*1000)}ms.jpg"
                    frame_path=os.path.join(output_folder,frame_filename)
                    cv2.imwrite(frame_path,frame)
            else:
                print(f"Could not extract frame at ",timestamps," seconds")
        cap.release()
        print("Total frames extracted:",len(frames))
        return frames
    
    def save_frame_metadata(self, video_path: str, output_json: str):
        info = self.get_video_info(video_path)
        with open(output_json, 'w') as f:
            json.dump(info, f, indent=2)
        print(f"Metadata saved: {output_json}")
    
    def _format_duration(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        import time
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        deleted_count = 0
        for folder in [self.raw_path, self.processed_path]:
            for filename in os.listdir(folder):
                if filename == '.gitkeep' or filename == 'readme.md':
                    continue
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"Deleted: {filename}")
        if deleted_count > 0:
            print(f" Cleaned up ",deleted_count," old file(s)")
        else:
            print("No old files to clean up")

def quick_capture(duration: int = 10, output_name: str = "test_video.mp4") -> str:
    processor = VideoProcessor()
    return processor.capture_video(duration=duration, filename=output_name)
def quick_extract_frames(video_path: str, every_n: int = 10) -> List[np.ndarray]:
    processor = VideoProcessor()
    return processor.extract_frames(video_path, every_n=every_n)
        


