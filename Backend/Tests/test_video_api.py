import requests
import os

# API base URL (make sure FastAPI server is running!)
BASE_URL = "http://localhost:8000"

def test_video_processor_status():
    """Test 1: Check if video processor is ready"""
    print("\n" + "="*70)
    print("TEST 1: Video Processor Status")
    print("="*70 + "\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/video/test")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Video processor is ready!")
            print(f"   Raw videos: {data['paths']['raw']}")
            print(f"   Frames: {data['paths']['frames']}")
            print(f"   Folders exist: {data['test_results']['folders_exist']}")
        else:
            print(f"❌ Test failed: Status {response.status_code}")
            print(f"   {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API!")
        print("   Make sure FastAPI server is running:")
        print("   cd Backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_upload_video():
    """Test 2: Upload a video file"""
    print("\n" + "="*70)
    print("TEST 2: Upload Video")
    print("="*70 + "\n")
    
    video_path = "Data/Video/Raw/test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"⚠️  No test video found at: {video_path}")
        print("   Skipping upload test")
        return None
    
    try:
        with open(video_path, 'rb') as f:
            files = {'video': ('test_video.mp4', f, 'video/mp4')}
            response = requests.post(
                f"{BASE_URL}/api/video/upload",
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Video uploaded successfully!")
            print(f"   Filename: {data['video_info']['filename']}")
            print(f"   Duration: {data['video_info']['duration_formatted']}")
            print(f"   Resolution: {data['video_info']['resolution']}")
            print(f"   Size: {data['video_info']['file_size_mb']} MB")
            return data['video_info']['filename']
        else:
            print(f"❌ Upload failed: Status {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


def test_list_videos():
    """Test 3: List all videos"""
    print("\n" + "="*70)
    print("TEST 3: List Videos")
    print("="*70 + "\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/video/list")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} video(s):")
            
            for video in data['videos']:
                print(f"\n   📹 {video['filename']}")
                print(f"      Duration: {video['duration']}s")
                print(f"      Resolution: {video['resolution']}")
                print(f"      Size: {video['size_mb']} MB")
            
            return data['videos']
        else:
            print(f"❌ List failed: Status {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ List failed: {e}")
        return []


def test_get_video_info(filename="test_video.mp4"):
    """Test 4: Get video information"""
    print("\n" + "="*70)
    print(f"TEST 4: Get Video Info - {filename}")
    print("="*70 + "\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/video/info/{filename}")
        
        if response.status_code == 200:
            data = response.json()
            info = data['video_info']
            
            print("✅ Video info retrieved:")
            print(f"   Filename: {info['filename']}")
            print(f"   Duration: {info['duration_formatted']} ({info['duration_seconds']}s)")
            print(f"   Resolution: {info['resolution']}")
            print(f"   FPS: {info['fps']}")
            print(f"   Frame count: {info['frame_count']}")
            print(f"   File size: {info['file_size_mb']} MB")
            
            return info
        elif response.status_code == 404:
            print(f"⚠️  Video not found: {filename}")
            return None
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None


def test_extract_frames(filename="test_video.mp4"):
    """Test 5: Extract frames from video"""
    print("\n" + "="*70)
    print(f"TEST 5: Extract Frames - {filename}")
    print("="*70 + "\n")
    
    try:
        payload = {
            "video_filename": filename,
            "every_n": 10,
            "save_to_disk": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/video/extract-frames",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Frames extracted successfully!")
            print(f"   Frames extracted: {data['frames_extracted']}")
            print(f"   Saved to: {data['output_folder']}")
            
            return data
        elif response.status_code == 404:
            print(f"⚠️  Video not found: {filename}")
            return None
        else:
            print(f"❌ Extraction failed: Status {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None


def test_delete_video(filename="test_upload.mp4"):
    """Test 6: Delete video"""
    print("\n" + "="*70)
    print(f"TEST 6: Delete Video - {filename}")
    print("="*70 + "\n")
    
    try:
        response = requests.delete(f"{BASE_URL}/api/video/{filename}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Video not found: {filename}")
            return False
        else:
            print(f"❌ Delete failed: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        return False


def run_all_tests():
    """Run complete API test suite"""
    print("\n" + "🎬 " + "="*66)
    print("AIRA - Video API Test Suite")
    print("="*70 + "\n")
    
    print("⚠️  Make sure FastAPI server is running:")
    print("   cd Backend && python main.py\n")
    
    input("Press Enter to start tests...")
    
    results = {}
    
    # Test 1: Status check
    results['status'] = test_video_processor_status()
    
    if not results['status']:
        print("\n❌ API not reachable. Stopping tests.")
        return
    
    # Test 2: List videos
    videos = test_list_videos()
    results['list'] = len(videos) >= 0
    
    # Test 3: Get info (if videos exist)
    if videos:
        filename = videos[0]['filename']
        results['info'] = test_get_video_info(filename) is not None
        
        # Test 4: Extract frames
        results['extract'] = test_extract_frames(filename) is not None
    else:
        print("\n⚠️  No videos found. Upload a video first to test info/extract.")
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}\n")
    
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
    print("\n🎬 AIRA Video API Test Menu\n")
    print("1. Run all tests")
    print("2. Test API status")
    print("3. List videos")
    print("4. Get video info")
    print("5. Extract frames")
    print("6. Exit")
    
    choice = input("\nSelect test (1-6): ")
    
    if choice == '1':
        run_all_tests()
    elif choice == '2':
        test_video_processor_status()
    elif choice == '3':
        test_list_videos()
    elif choice == '4':
        filename = input("Enter filename (or press Enter for 'test_video.mp4'): ")
        test_get_video_info(filename or "test_video.mp4")
    elif choice == '5':
        filename = input("Enter filename (or press Enter for 'test_video.mp4'): ")
        test_extract_frames(filename or "test_video.mp4")
    elif choice == '6':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")  