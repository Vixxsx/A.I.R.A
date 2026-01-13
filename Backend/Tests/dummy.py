import os
import sys


current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.dirname(current_dir)  # Up one level to Backend/

print(f"Adding to path: {backend_path}")
sys.path.insert(0, backend_path)

from Utilities.video_utils import VideoProcessor

print("✅ Import successful!")
