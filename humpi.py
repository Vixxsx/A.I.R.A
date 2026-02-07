import cv2

cap = cv2.VideoCapture("video=DroidCam Source 3", cv2.CAP_DSHOW)

if not cap.isOpened():
    print("DroidCam not opened")
else:
    ret, frame = cap.read()
    print("Opened DroidCam:", frame.shape if ret else "No frame")
