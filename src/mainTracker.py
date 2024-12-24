import cv2
import math
import time
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
plt.rcParams.update({'font.size': 10})

# SPEED LIMIT (in px/s)
LIMIT = 150

# DIRECTORY SETUP
BASE_DIR = os.getenv("TRAFFIC_RECORD_DIR", "/app/TrafficRecord")
EXCEEDED_DIR = os.path.join(BASE_DIR, "exceeded")
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(EXCEEDED_DIR, exist_ok=True)

# SPEED RECORD FILE
record_file_path = os.path.join(BASE_DIR, "SpeedRecord.txt")
with open(record_file_path, "w") as file:
    file.write("------------------------------\n")
    file.write("            REPORT            \n")
    file.write("------------------------------\n")
    file.write("ID  |   SPEED\n")
    file.write("------------------------------\n")


class EuclideanDistTracker:
    def __init__(self):
        self.center_points = {}  # Tracks object centers
        self.id_count = 0  # ID counter
        self.s1 = np.zeros((1, 1000))
        self.s2 = np.zeros((1, 1000))
        self.s = np.zeros((1, 1000))
        self.f = np.zeros(1000)  # Flags
        self.capf = np.zeros(1000)  # Capture flags
        self.count = 0  # Total vehicle count
        self.exceeded = 0  # Exceeded speed limit count
        self.ids_DATA = []  # IDs for visualization
        self.spd_DATA = []  # Speeds for visualization

    def update(self, objects_rect):
        objects_bbs_ids = []

        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            same_object_detected = False

            for obj_id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if dist < 70:
                    self.center_points[obj_id] = (cx, cy)
                    objects_bbs_ids.append([x, y, w, h, obj_id])
                    same_object_detected = True

                    # Start timer
                    if 410 <= y <= 430:
                        self.s1[0, obj_id] = time.time()

                    # Stop timer and calculate speed
                    if 235 <= y <= 255:
                        self.s2[0, obj_id] = time.time()
                        self.s[0, obj_id] = self.s2[0, obj_id] - self.s1[0, obj_id]

                    # Set capture flag
                    if y < 235:
                        self.f[obj_id] = 1

            if not same_object_detected:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                self.id_count += 1

        # Update center points
        self.center_points = {obj_id: self.center_points[obj_id] for _, _, _, _, obj_id in objects_bbs_ids}
        return objects_bbs_ids

    def getsp(self, obj_id):
        if self.s[0, obj_id] != 0:
            sp = 200 / self.s[0, obj_id]
        else:
            sp = 0
        return int(sp)

    def capture(self, img, x, y, h, w, sp, obj_id):
        if self.capf[obj_id] == 0:
            self.capf[obj_id] = 1
            self.f[obj_id] = 0
            crop_img = img[max(0, y - 5):y + h + 5, max(0, x - 5):x + w + 5]
            file_name = f"vehicle_id_{obj_id}_speed_{sp}.jpg"
            file_path = os.path.join(BASE_DIR, file_name)

            cv2.imwrite(file_path, crop_img)
            self.count += 1

            # Record speed
            with open(record_file_path, "a") as record_file:
                if sp > LIMIT:
                    exceeded_file_path = os.path.join(EXCEEDED_DIR, file_name)
                    cv2.imwrite(exceeded_file_path, crop_img)
                    record_file.write(f"{obj_id}\t{sp} <-- exceeded\n")
                    self.exceeded += 1
                else:
                    record_file.write(f"{obj_id}\t{sp}\n")

            self.ids_DATA.append(obj_id)
            self.spd_DATA.append(sp)

    def dataset(self):
        return self.ids_DATA, self.spd_DATA

    def datavis(self, id_lst, spd_lst):
        x = id_lst
        y = spd_lst
        valx = [str(i) for i in x]

        plt.figure(figsize=(20, 5))
        style.use('dark_background')
        plt.axhline(y=LIMIT, color='r', linestyle='-', linewidth=5)
        plt.bar(x, y, width=0.5, linewidth=3, edgecolor='yellow', color='blue', align='center')
        plt.xlabel('ID')
        plt.ylabel('Speed')
        plt.xticks(x, valx)
        plt.legend(["Speed limit"])
        plt.title('Speed of Vehicles Crossing Road\n')

        output_path = os.path.join(BASE_DIR, "datavis.png")
        plt.savefig(output_path, bbox_inches='tight', pad_inches=1, edgecolor='w', orientation='landscape')

    def limit(self):
        return LIMIT

    def end(self):
        with open(record_file_path, "a") as file:
            file.write("\n------------------------------\n")
            file.write("           SUMMARY            \n")
            file.write("------------------------------\n")
            file.write(f"Total Vehicles: {self.count}\n")
            file.write(f"Exceeded speed limit: {self.exceeded}\n")
            file.write("------------------------------\n")
            file.write("             END              \n")
            file.write("------------------------------\n")
