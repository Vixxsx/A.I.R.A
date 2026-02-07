import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.dirname(current_dir)  
sys.path.insert(0, backend_path)

from Utilities.video_utils import VideoProcessor


def test_webcam():
    """Test 1: Webcam availability"""
    print("\n" + "="*70)
    print("TEST 1: Webcam Check")
    print("="*70 + "\n")
    
    processor = VideoProcessor()
    
    result = processor.test_webcam(camera_index=0)
    
    if result:
        print("\nWebcam test PASSED")
    else:
        print("\nWebcam test FAILED")
        print("   Make sure your camera is connected and not used by another app")
    
    return result


def test_find_cameras():
    """Test 2: Find all available cameras"""
    print("\n" + "="*70)
    print("TEST 2: Find Available Cameras")
    print("="*70 + "\n")
    
    processor = VideoProcessor()
    cameras = processor.get_available_cameras()
    
    if cameras:
        print(f"\nFound {len(cameras)} camera(s): {cameras}")
    else:
        print("\nNo cameras found")
    
    return cameras


def test_video_info():
    """Test 3: Get video information"""
    print("\n" + "="*70)
    print("TEST 3: Video Info (if test video exists)")
    print("="*70 + "\n")
    
    processor = VideoProcessor()
    test_video = "Data/Video/Raw/test_video.mp4"
    
    if os.path.exists(test_video):
        info = processor.video_info(test_video)
        
        print("Video Information:")
        print(f"  Filename: {info['filename']}")
        print(f"  Resolution: {info['resolution']}")
        print(f"  FPS: {info['fps']}")
        print(f"  Duration: {info['duration_formatted']} ({info['duration_seconds']}s)")
        print(f"  Frame Count: {info['frame_count']}")
        print(f"  File Size: {info['file_size_mb']} MB")
        
        print("\nVideo info retrieved successfully")
        return info
    else:
        print(f"No test video found at: {test_video}")
        print("   Run test_capture_video() first to create one")
        return None


def test_capture_video():
    """Test 4: Capture short video"""
    print("\n" + "="*70)
    print("TEST 4: Video Capture (5 seconds)")
    print("="*70 + "\n")
    
    processor = VideoProcessor()
    
    try:
        print("Starting capture in 3 seconds...")
        print("   Look at your camera!")
        import time
        time.sleep(3)
        
        video_path = processor.capture_video(
            duration=5,
            camera_index=1,
            filename="test_video.mp4"
        )
        
        print(f"\nVideo captured: {video_path}")
        
        # Show info
        info = processor.video_info(video_path)
        print(f"\nCaptured video info:")
        print(f"  Duration: {info['duration_seconds']}s")
        print(f"  Resolution: {info['resolution']}")
        print(f"  File size: {info['file_size_mb']} MB")
        
        return video_path
        
    except Exception as e:
        print(f"\n❌ Capture failed: {e}")
        return None


def test_frame_extraction():
    """Test 5: Extract frames from video"""
    print("\n" + "="*70)
    print("TEST 5: Frame Extraction")
    print("="*70 + "\n")
    
    processor = VideoProcessor()
    test_video = "Data/Video/Raw/test_video.mp4"
    
    if not os.path.exists(test_video):
        print(f"⚠️  No test video found: {test_video}")
        print("   Run test_capture_video() first")
        return None
    
    # Create output folder
    output_folder = "Data/Video/Frames/test_extraction"
    
    try:
        # Extract frames (every 10th frame)
        frames = processor.extract_frames(
            video_path=test_video,
            output_folder=output_folder,
            every_nth=10,
            return_arrays=True
        )
        print(f"\n✅ Extracted {len(frames)} frames")
        print(f"   Saved to: {output_folder}")
        print(f"   Frame shape: {frames[0].shape if frames else 'N/A'}")
        
        return frames
        
    except Exception as e:
        print(f"\nFrame extraction failed: {e}")
        return None


def test_save_metadata():
    """Test 6: Save video metadata to JSON"""
    print("\n" + "="*70)
    print("TEST 6: Save Metadata to JSON")
    print("="*70 + "\n")
    
    processor = VideoProcessor()
    test_video = "Data/Video/Raw/test_video.mp4"
    
    if not os.path.exists(test_video):
        print(f"⚠️  No test video found")
        return None
    
    try:
        output_json = "Data/Video/Raw/test_video_info.json"
        processor.save_frame_metadata(test_video, output_json)
        
        print(f"\n✅ Metadata saved to: {output_json}")
        return output_json
        
    except Exception as e:
        print(f"\n❌ Failed to save metadata: {e}")
        return None


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "🎬 " + "="*66)
    print("AIRA - Video Utilities Complete Test Suite")
    print("="*70 + "\n")
    
    results = {}
    
    # Test 1: Webcam
    results['webcam'] = test_webcam()
    
    # Test 2: Find cameras
    results['cameras'] = test_find_cameras()
    
    # Test 3: Video info (if exists)
    results['info'] = test_video_info()
    
    # Test 4: Capture video (optional - requires camera)
    print("\n" + "="*70)
    print("⚠️  TEST 4 will capture 5 seconds of video")
    response = input("Run video capture test? (y/n): ")
    
    if response.lower() == 'y':
        results['capture'] = test_capture_video()
        
        if results['capture']:
            # Test 5: Extract frames
            results['extraction'] = test_frame_extraction()
            
            # Test 6: Save metadata
            results['metadata'] = test_save_metadata()
    else:
        print("⏭️  Skipping capture tests")
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    elif passed > 0:
        print("⚠️  SOME TESTS PASSED")
    else:
        print("❌ ALL TESTS FAILED")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    # Quick menu
    print("\n🎬 AIRA Video Utils Test Menu\n")
    print("1. Run all tests")
    print("2. Test webcam only")
    print("3. Find available cameras")
    print("4. Get video info")
    print("5. Capture video")
    print("6. Extract frames")
    print("7. Exit")
    
    choice = input("\nSelect test (1-7): ")
    
    if choice == '1':
        run_all_tests()
    elif choice == '2':
        test_webcam()
    elif choice == '3':
        test_find_cameras()
    elif choice == '4':
        test_video_info()
    elif choice == '5':
        test_capture_video()
    elif choice == '6':
        test_frame_extraction()
    elif choice == '7':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")