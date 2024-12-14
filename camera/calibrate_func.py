import cv2
import numpy as np


def calculate_iou(bbox1, bbox2):
    x1_1, y1_1, x2_1, y2_1 = bbox1 # สกัด position ของ แกนx และ y ของ bounding box person
    x1_2, y1_2, x2_2, y2_2 = bbox2 # สกัด position ของ แกนx และ y ของ bounding box chair

    
    x_max_left = max(x1_1, x1_2) #หาจุดตัดของขอบซ้าย
    y_max_top = max(y1_1, y1_2) #หาจุดตัดของขอบวา
    x_min_right = min(x2_1, x2_2) #หาจุดตัดของขอบบน
    y_min_bottom = min(y2_1, y2_2) #หาจุดตัดของขอบล่าง

    # คำนวณหาจุดของ ความกว้าง และ ความสูง ของพื้นที่ทับซ้อน
    inter_width = max(0, x_min_right - x_max_left)
    inter_height = max(0, y_min_bottom - y_max_top)

    # คำนวณหาขนาดของพื้นที่ที่ทับซ้อนกัน
    intersection_area = inter_width * inter_height

    # คำนวณหาจุดที่ สองกล่อง Unionกัน
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    # คำนวณหาพื้นที่ที่สองกล่อง Union กัน
    union_area = area1 + area2 - intersection_area

    # คำรวณหาค่าIoU
    iou = intersection_area / union_area if union_area > 0 else 0

    return iou

def check_brightness(frame, threshold=50):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray_frame)
    return avg_brightness, int(avg_brightness < threshold)  # แปลงเป็น Integer

def is_sit_chair(user_bbox, chair_bbox, threshold=0.3):
    iou = calculate_iou(user_bbox, chair_bbox) #คำนวณหาค่าIoUของ bbox_user และ bbox_chair
    return iou >= threshold

