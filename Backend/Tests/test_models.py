import cv2
import os
import sys
import time
import warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Add Backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ========== TEST 1: EMOTION DETECTOR ==========

def test_emotion_detector():
    print("\n" + "="*70)
    print("TEST 1: EMOTION DETECTOR (DeepFace)")
    print("="*70 + "\n")

    try:
        from Models.emotion_detector import EmotionDetector
        
        # Initialize
        print("Loading EmotionDetector...")
        detector = EmotionDetector()
        print("✅ EmotionDetector loaded!\n")

        # Capture test frame from webcam
        print("📷 Capturing test frame from webcam...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open webcam!")
            return False
        
        # Warm up camera
        for _ in range(5):
            cap.read()
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("❌ Cannot read from webcam!")
            return False
        
        print(f"✅ Frame captured: {frame.shape[1]}x{frame.shape[0]}")
        
        # Analyze frame
        print("\n🔍 Analyzing emotions...")
        result = detector.analyze_frame(frame)
        
        if result['face_detected']:
            print(f"\n✅ FACE DETECTED!")
            print(f"   Dominant Emotion: {result['dominant_emotion']}")
            print(f"\n   Interview Assessment:")
            assessment = result['interview_assessment']
            print(f"   Confidence Score:    {assessment['confidence_score']}")
            print(f"   Enthusiasm Score:    {assessment['enthusiasm_score']}")
            print(f"   Nervousness Score:   {assessment['nervousness_score']}")
            print(f"   Professionalism:     {assessment['professionalism_score']}")
            print(f"   Overall Impression:  {assessment['overall_impression']}")
            print(f"\n   Raw Emotions:")
            for emotion, value in result['emotions'].items():
                bar = "█" * int(value / 5) 
                print(f"   {emotion:10}: {value:5.1f}% {bar}")
            return True
        else:
            print("⚠️  No face detected!")
            print("   Make sure:")
            print("   - Camera is on")
            print("   - Face is visible")
            print("   - Room has good lighting")
            return False
    
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Install DeepFace: pip install deepface --break-system-packages")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ========== TEST 2: EYE TRACKER ==========

def test_eye_tracker():
    print("\n" + "="*70)
    print("TEST 2: EYE TRACKER (MediaPipe)")
    print("="*70 + "\n")

    try:
        from Models.eye_tracker import EyeTracker
        
        # Initialize
        print("Loading EyeTracker...")
        tracker = EyeTracker()
        print("✅ EyeTracker loaded!\n")

        # Capture test frame from webcam
        print("📷 Capturing test frame from webcam...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open webcam!")
            return False
        
        # Warm up camera
        for _ in range(5):
            cap.read()
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("❌ Cannot read from webcam!")
            return False
        
        print(f"✅ Frame captured: {frame.shape[1]}x{frame.shape[0]}")
        
        # Analyze frame
        print("\n👁️ Analyzing eye contact...")
        result = tracker.analyze_frame(frame)
        
        if result['face_detected']:
            print(f"\n✅ FACE DETECTED!")
            print(f"   Eye Contact Score: {result.get('eye_contact_score', 'N/A')}")
            print(f"   Looking at Camera: {result['looking_at_camera']}")
            print(f"   Gaze Direction:    {result['gaze_direction']}")
            return True
        else:
            print("⚠️  No face detected!")
            print("   Make sure:")
            print("   - Camera is on")
            print("   - Face is clearly visible")
            print("   - Good lighting")
            return False
    
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Fix MediaPipe:")
        print("   pip uninstall mediapipe -y")
        print("   pip install mediapipe==0.10.9 --break-system-packages")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ========== TEST 3: LIVE WEBCAM TEST ==========

def test_live_webcam(duration: int = 10):
    """
    Live test - shows real-time emotion + eye tracking
    for 10 seconds on your webcam
    """
    print("\n" + "="*70)
    print(f"TEST 3: LIVE WEBCAM TEST ({duration} seconds)")
    print("="*70 + "\n")

    try:
        from Models.emotion_detector import EmotionDetector
        
        has_eye_tracker = False
        try:
            from Models.eye_tracker import EyeTracker
            tracker = EyeTracker()
            has_eye_tracker = True
            print("✅ Eye Tracker loaded")
        except Exception as e:
            print(f"⚠️  Eye tracker unavailable: {e}")
        
        detector = EmotionDetector()
        print("✅ Emotion Detector loaded")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open webcam!")
            return False
        
        print(f"\n📷 Live analysis for {duration} seconds...")
        print("   Look at camera!")
        print("   Press Q to stop early\n")
        
        start_time = time.time()
        frame_count = 0
        results_log = []
        
        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze every 15 frames (~0.5s)
            if frame_count % 15 == 0:
                # Get emotion
                emotion_result = detector.analyze_frame(frame)
                
                # Get eye contact
                eye_result = None
                if has_eye_tracker:
                    eye_result = tracker.analyze_frame(frame)
                
                # Log results
                if emotion_result['face_detected']:
                    log_entry = {
                        "time": round(elapsed, 1),
                        "emotion": emotion_result['dominant_emotion'],
                        "confidence": emotion_result['interview_assessment']['confidence_score'],
                        "nervousness": emotion_result['interview_assessment']['nervousness_score'],
                        "eye_contact": eye_result['looking_at_camera'] if eye_result else "N/A"
                    }
                    results_log.append(log_entry)
                    
                    # Print live update
                    print(f"   [{elapsed:4.1f}s] "
                          f"Emotion: {emotion_result['dominant_emotion']:10} | "
                          f"Confidence: {log_entry['confidence']:4.1f} | "
                          f"Nervous: {log_entry['nervousness']:4.1f} | "
                          f"Eye Contact: {log_entry['eye_contact']}")
            
            frame_count += 1
            
            # Check for Q key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Print summary
        if results_log:
            print(f"\n✅ LIVE TEST COMPLETE!")
            print(f"   Frames analyzed: {len(results_log)}")
            
            avg_confidence = sum(r['confidence'] for r in results_log) / len(results_log)
            avg_nervousness = sum(r['nervousness'] for r in results_log) / len(results_log)
            
            print(f"\n📊 SUMMARY:")
            print(f"   Average Confidence:  {avg_confidence:.1f}")
            print(f"   Average Nervousness: {avg_nervousness:.1f}")
            
            if has_eye_tracker:
                eye_yes = sum(1 for r in results_log if r['eye_contact'] == True)
                eye_pct = (eye_yes / len(results_log)) * 100
                print(f"   Eye Contact %:       {eye_pct:.1f}%")
            
            emotions = [r['emotion'] for r in results_log]
            most_common = max(set(emotions), key=emotions.count)
            print(f"   Most Common Emotion: {most_common}")
        
        return True
    
    except Exception as e:
        print(f"❌ Live test failed: {e}")
        return False


# ========== MAIN MENU ==========

def run_all_tests():
    print("\n🤖 " + "="*66)
    print("AIRA - AI Models Test Suite")
    print("="*70 + "\n")
    
    results = {}
    
    results['Emotion'] = test_emotion_detector()
    results['Eye'] = test_eye_tracker()
    
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70 + "\n")
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - READY FOR DEMO!")
    else:
        print("⚠️  SOME TESTS FAILED - SEE ERRORS ABOVE")
    print("="*70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    print("\n🤖 AIRA AI Models Test Menu\n")
    print("1. Run all tests")
    print("2. Test emotion detector only")
    print("3. Test eye tracker only")
    print("4. Live webcam test (10 seconds)")
    print("5. Exit")
    
    choice = input("\nSelect test (1-5): ")
    
    if choice == '1':
        run_all_tests()
    elif choice == '2':
        test_emotion_detector()
    elif choice == '3':
        test_eye_tracker()
    elif choice == '4':
        duration = input("Duration in seconds (default 10): ")
        test_live_webcam(int(duration) if duration else 10)
    elif choice == '5':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")