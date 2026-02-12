from Utilities.video_utils import VideoProcessor
p = VideoProcessor()

# Test camera 0
print("Testing camera 0:")
p.test_webcam(0)

# Test camera 1
print("\nTesting camera 1:")
p.test_webcam(1)

print("\nTesting camera 2:")
p.test_webcam(2)

print("\nTesting camera 31:")
p.test_webcam(3)

print("\nTesting camera 4:")
p.test_webcam(4)