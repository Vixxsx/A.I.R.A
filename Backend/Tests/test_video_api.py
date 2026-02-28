"""
AIRA - Complete Video API Test Suite
Tests all video processing, emotion detection, and eye tracking
Run from project root: python Backend/Tests/test_video_api.py
"""

import requests
import os
import sys
import cv2
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_VIDEO_PATH = "Data/Video/Raw/test_video.mp4"

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def test_server_running():
    """Test 1: Check if server is running"""
    print_header("TEST 1: Server Status")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not running!")
        print("   Start server: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_video_processor():
    """Test 2: Video processor endpoint"""
    print_header("TEST 2: Video Processor")
    try:
        response = requests.get(f"{BASE_URL}/api/video/test")
        if response.status_code == 200:
            data = response.json()
            print("✅ Video processor ready")
            print(f"   Paths configured: {data.get('paths', {})}")
            return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_emotion_detector():
    """Test 3: Emotion detector (via interview endpoint)"""
    print_header("TEST 3: Emotion Detector")
    try:
        response = requests.get(f"{BASE_URL}/api/interview/test")
        if response.status_code == 200:
            data = response.json()
            emotion_status = data.get('analyzers', {}).get('emotion', '')
            
            if '✅' in emotion_status:
                print("✅ Emotion detector loaded")
                print(f"   Status: {emotion_status}")
                return True
            else:
                print(f"⚠️  Emotion detector issue: {emotion_status}")
                return False
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_eye_tracker():
    """Test 4: Eye tracker (via interview endpoint)"""
    print_header("TEST 4: Eye Tracker")
    try:
        response = requests.get(f"{BASE_URL}/api/interview/test")
        if response.status_code == 200:
            data = response.json()
            eye_status = data.get('analyzers', {}).get('eye', '')
            
            if '✅' in eye_status:
                print("✅ Eye tracker loaded")
                print(f"   Status: {eye_status}")
                print("   Note: Accuracy depends on webcam quality")
                return True
            else:
                print(f"⚠️  Eye tracker issue: {eye_status}")
                print("   Note: Will use default 65% eye contact value")
                return False
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_video_upload():
    """Test 5: Video upload"""
    print_header("TEST 5: Video Upload")
    
    # Check if test video exists
    if not os.path.exists(TEST_VIDEO_PATH):
        print(f"⚠️  Test video not found: {TEST_VIDEO_PATH}")
        print("   Creating test video from webcam...")
        
        if not create_test_video():
            print("❌ Could not create test video")
            return False
    
    try:
        with open(TEST_VIDEO_PATH, 'rb') as f:
            files = {'video': ('test_video.mp4', f, 'video/mp4')}
            response = requests.post(
                f"{BASE_URL}/api/video/upload",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Video uploaded successfully")
            print(f"   File: {data.get('video_info', {}).get('filename')}")
            print(f"   Size: {data.get('video_info', {}).get('file_size_mb')} MB")
            print(f"   Duration: {data.get('video_info', {}).get('duration_seconds')} seconds")
            return True
        else:
            print(f"❌ Upload failed: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_interview_analysis():
    """Test 6: Complete interview analysis"""
    print_header("TEST 6: Interview Analysis (Full Pipeline)")
    
    if not os.path.exists(TEST_VIDEO_PATH):
        print(f"⚠️  Test video not found: {TEST_VIDEO_PATH}")
        print("   Skipping analysis test")
        return False
    
    print("📤 Uploading video for analysis...")
    print("   (This may take 30-60 seconds)")
    
    try:
        with open(TEST_VIDEO_PATH, 'rb') as f:
            files = {'video': ('test_video.mp4', f, 'video/mp4')}
            data = {
                'question_id': 1,
                'question_text': 'Test question'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/interview/analyze-answer",
                files=files,
                data=data,
                timeout=120
            )
            elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis complete in {elapsed:.1f} seconds")
            print("\n📊 Results:")
            print(f"   Overall Score: {result.get('overall_score')}/100")
            
            audio = result.get('audio_analysis', {})
            print(f"\n   Audio Analysis:")
            print(f"   - Transcript: {audio.get('transcript', '')[:100]}...")
            print(f"   - Filler Score: {audio.get('filler_score')}/100")
            print(f"   - Speaking Rate: {audio.get('speaking_rate')} WPM")
            
            video = result.get('video_analysis', {})
            print(f"\n   Video Analysis:")
            print(f"   - Emotion: {video.get('dominant_emotion')}")
            print(f"   - Confidence: {video.get('confidence_score')}")
            print(f"   - Eye Contact: {video.get('eye_contact_percentage')}%")
            
            print(f"\n   Feedback: {result.get('feedback')}")
            return True
        else:
            print(f"❌ Analysis failed: Status {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out (analysis taking too long)")
        print("   Try with shorter video or check server logs")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_test_video():
    """Create a 5-second test video from webcam"""
    try:
        print("📷 Opening webcam...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open webcam")
            return False
        
        # Video properties
        fps = 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create output directory
        os.makedirs(os.path.dirname(TEST_VIDEO_PATH), exist_ok=True)
        
        # Video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(TEST_VIDEO_PATH, fourcc, fps, (width, height))
        
        print(f"🎥 Recording 5 seconds ({width}x{height} @ {fps}fps)...")
        
        frames_to_record = fps * 5  # 5 seconds
        for i in range(frames_to_record):
            ret, frame = cap.read()
            if ret:
                out.write(frame)
                if (i + 1) % fps == 0:
                    print(f"   Recorded {(i+1)//fps} seconds...")
            else:
                break
        
        cap.release()
        out.release()
        
        if os.path.exists(TEST_VIDEO_PATH):
            size_mb = os.path.getsize(TEST_VIDEO_PATH) / (1024 * 1024)
            print(f"✅ Test video created: {TEST_VIDEO_PATH}")
            print(f"   Size: {size_mb:.2f} MB")
            return True
        else:
            print("❌ Failed to create test video")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test video: {e}")
        return False

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("  🧪 AIRA VIDEO API COMPLETE TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Run tests
    results['server'] = test_server_running()
    
    if not results['server']:
        print("\n❌ Server not running - cannot proceed with other tests")
        print("   Start server: python main.py")
        return False
    
    results['video_processor'] = test_video_processor()
    results['emotion'] = test_emotion_detector()
    results['eye_tracker'] = test_eye_tracker()
    results['upload'] = test_video_upload()
    results['analysis'] = test_interview_analysis()
    
    # Summary
    print_header("TEST SUMMARY")
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test:20}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    percentage = (passed / total) * 100
    
    print(f"\n  Tests Passed: {passed}/{total} ({percentage:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SYSTEM READY FOR DEMO!")
    elif passed >= total * 0.8:
        print("\n⚠️  MOST TESTS PASSED - Minor issues to fix")
    else:
        print("\n❌ MULTIPLE FAILURES - Check server logs")
    
    print("="*70 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)