
from django.http import JsonResponse
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2
import json
from django.views.generic import TemplateView
from ultralytics import YOLO
from camera.calibrate_func import *
import mediapipe as mp


class CameraDetectionView(TemplateView):
    template_name = 'camera.html'

class Selection_hubView(TemplateView):
    template_name = 'selection_hub.html'


# โหลดโมเดล YOLOv8
model = YOLO('yolov8n.pt')
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def is_full_body(pose_landmarks):
    left_knee = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]

    if left_knee.visibility > 0.2 and right_knee.visibility > 0.2:
        return True
    return False


def process_image(request):
    if request.method == 'POST':
        try:
            # รับข้อมูลภาพจาก request
            data = json.loads(request.body)
            image_data = data.get('image')

            if not image_data:
                return JsonResponse({'error': 'No image data provided'}, status=400)

            try:
                # แปลง Base64 เป็น NumPy array
                img_data = base64.b64decode(image_data.split(',')[1])  # ลบ prefix base64
                img = Image.open(BytesIO(img_data))

                # แปลง RGBA เป็น RGB (ถ้าจำเป็น)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                img = np.array(img)

                # แปลง RGB เป็น BGR (OpenCV ใช้ BGR เป็นค่าเริ่มต้น)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            except Exception as e:
                return JsonResponse({'error': f"Error decoding image: {str(e)}"}, status=500)

            # ตรวจสอบขนาดของภาพ
            try:
                height, width, _ = img_bgr.shape
                print(f"Image size: {width}x{height}")
            except Exception as e:
                return JsonResponse({'error': f"Error processing image dimensions: {str(e)}"}, status=500)

            # ตรวจสอบความสว่าง
            try:
                avg_brightness, is_low_brightness = check_brightness(img_bgr)
            except Exception as e:
                return JsonResponse({'error': f"Error checking brightness: {str(e)}"}, status=500)

            # ตรวจจับวัตถุด้วย YOLOv8
            try:
                results = model(img_bgr)  # ตรวจจับวัตถุ
                detections = []
                person_bbox = None  # เก็บ bounding box ของ person
                chair_bbox = None   # เก็บ bounding box ของ chair
                
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # แปลง Tensor เป็น List และ Map เป็น int
                        class_id = int(box.cls)  # class id
                        if class_id == 0 or class_id == 56:
                            class_name = model.names[class_id]  # ชื่อ class
                            confidence = float(box.conf[0]) * 100  # ความมั่นใจ (%) แปลง Tensor เป็น float
                            bbox = [x1, y1, x2, y2]  # Bounding box

                            # เพิ่ม bounding box ลงใน detections
                            detections.append({
                                'class_name': class_name,
                                'confidence': confidence,
                                'bbox': bbox
                            })

                            # แยก Bounding Box สำหรับ person และ chair
                            if class_id == 0:  # Person
                                person_bbox = bbox
                            elif class_id == 56:  # Chair
                                chair_bbox = bbox
            except Exception as e:
                return JsonResponse({'error': f"Error in YOLOv8 detection: {str(e)}"}, status=500)

            # ตรวจสอบว่าบุคคลนั่งบนเก้าอี้หรือไม่
            is_sitting = False
            if person_bbox and chair_bbox:
                is_sitting = is_sit_chair(person_bbox, chair_bbox)
            try:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                results_pose = pose.process(img_rgb)
                print(results_pose)
                is_full_body_detected = False

                if results_pose.pose_landmarks:
                    is_full_body_detected = is_full_body(results_pose.pose_landmarks)
            except Exception as e:
                return JsonResponse({'error': f"Error in MediaPipe Pose detection: {str(e)}"}, status=500)


            # ส่งผลลัพธ์กลับ
            return JsonResponse({
                'message': 'Image processed successfully',
                'width': width,
                'height': height,
                'avg_brightness': avg_brightness,
                'is_low_brightness': int(is_low_brightness),  # แปลงเป็น 1 (True) หรือ 0 (False)
                'is_full_body_detected': is_full_body_detected,
                'detections': detections,
                'is_sitting': is_sitting  # True หากบุคคลนั่งบนเก้าอี้
            })
        except Exception as e:
            return JsonResponse({'error': f"Unexpected error: {str(e)}"}, status=500)