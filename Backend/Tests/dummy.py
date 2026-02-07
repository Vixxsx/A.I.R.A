from Backend.Utilities.video_utils import VideoProcessor

processor = VideoProcessor()

# Find DroidCam
cameras = processor.get_available_cameras()
print(f"Available cameras: {cameras}")

# Test each one
for idx in cameras:
    print(f"\nTesting camera {idx}:")
    processor.test_webcam(camera_index=idx)