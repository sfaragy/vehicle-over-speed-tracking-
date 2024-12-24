# import cv2

import time

# cap = cv2.VideoCapture(0)
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#     # Save or process the frame instead of displaying
#     cv2.imwrite(f"TrafficRecord/frame_{time.time()}.jpg", frame)
# cap.release()
#
#
#
# print("Hello, Docker is working correctly!")
# while True:
#     time.sleep(1)  # Keeps the script running







# PACKAGES
import cv2
import datetime
import numpy as np
from mainTracker import EuclideanDistTracker

# TRACKER OBJECT
tracker = EuclideanDistTracker()

# CAPTURE INPUT VIDEO STREAM
# cap = cv2.VideoCapture("resources/traffic.mp4")
cap = cv2.VideoCapture(0)

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_count = 0

# KERNELS
kernel_op = np.ones((3, 3), np.uint8)
kernel_cl = np.ones((11, 11), np.uint8)
kernel_er = np.ones((5, 5), np.uint8)
fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

# FLAGS
ids_list = []
spd_list = []
end_flag = False

while True:
    # OBJECT DETECTION
    ret, frame = cap.read()

    if not ret:
        print("Video stream ended or failed to read.")
        break

    frame_count += 1
    frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
    height, width, _ = frame.shape

    # EXTRACT REGION OF INTEREST (ROI)
    # roi = frame[50:540, 200:960]
    roi = frame[50:frame.shape[0] - 50, 100:frame.shape[1] - 100]


    # MASKING
    fgmask = fgbg.apply(roi)
    _, bin_img = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
    opening = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel_op)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel_cl)
    er_img = cv2.erode(closing, kernel_er)

    # CONTOURS & BOUNDING BOX
    contours, _ = cv2.findContours(er_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    detections = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 1000:  # THRESHOLD
            x, y, w, h = cv2.boundingRect(cnt)
            detections.append([x, y, w, h])

    # OBJECT TRACKING
    boxes_ids = tracker.update(detections)
    for box_id in boxes_ids:
        x, y, w, h, obj_id = box_id
        speed = tracker.getsp(obj_id)
        color = (0, 0, 255) if speed >= tracker.limit() else (0, 255, 0)

        # Draw bounding box and speed
        cv2.rectangle(roi, (x, y), (x + w, y + h), color, 3)
        cv2.putText(roi, f"ID: {obj_id} Speed: {speed}", (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 2)

        # Capture data if conditions are met
        if tracker.f[obj_id] == 1 and speed != 0:
            tracker.capture(roi, x, y, h, w, speed, obj_id)

    # DRAW LINES
    cv2.line(roi, (0, 410), (960, 410), (255, 0, 0), 2)  # Start Line
    cv2.putText(roi, 'START', (2, 425), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    cv2.line(roi, (0, 430), (960, 430), (255, 0, 0), 2)

    cv2.line(roi, (0, 235), (960, 235), (255, 0, 0), 2)  # End Line
    cv2.putText(roi, 'END', (2, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    cv2.line(roi, (0, 255), (960, 255), (255, 0, 0), 2)

    # DISPLAY DATE, TIME, FPS & FRAME INFO
    d = datetime.datetime.now().strftime("%d-%m-%y")
    t = datetime.datetime.now().strftime("%H-%M-%S")
    cv2.putText(roi, f'DATE: {d} | TIME: {t}', (25, 20), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 2)
    cv2.putText(roi, f'FPS: {fps:.2f} | FRAME: {frame_count}/{total_frames}', (400, 20), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 2)

    # DATA ALLOCATION
    ids_list, spd_list = tracker.dataset()

    # DISPLAY OUTPUT
    # cv2.imshow("OUTPUT", roi)
    cv2.imwrite(f"TrafficRecord/output_frame_{frame_count}.jpg", roi)

    # Break on 'Enter' key
    if cv2.waitKey(1) == 13:  # Enter key
        tracker.end()
        tracker.datavis(ids_list, spd_list)
        end_flag = True
        break

if not end_flag:
    tracker.end()

cap.release()
cv2.destroyAllWindows()
