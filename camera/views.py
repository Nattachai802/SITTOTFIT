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
from .utils.posture_analysis import calculate_angles , calculate_score , draw_pose_landmarks
from base.models import PostureDetection , UserUsageHistory
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

class CameraDetectionView(LoginRequiredMixin,TemplateView):
    template_name = 'camera.html'

class Selection_hubView(LoginRequiredMixin,TemplateView):
    template_name = 'selection_hub.html'

class Detection_View(LoginRequiredMixin,TemplateView):
    template_name = 'detection.html'

class Image_View(LoginRequiredMixin,TemplateView):
    template_name = 'upload_image.html'

# โหลดโมเดล YOLOv8


model = YOLO('yolov8m.pt')
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def is_full_body(pose_landmarks):
    left_knee = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]

    if left_knee.visibility > 0.2 or right_knee.visibility > 0.2:
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
                'is_low_brightness': int(is_low_brightness),  # แปลงเป็น 1 (True) หรือ 0 (False)
                'is_full_body_detected': is_full_body_detected,
                'is_sitting': is_sitting  # True หากบุคคลนั่งบนเก้าอี้
            })
        except Exception as e:
            return JsonResponse({'error': f"Unexpected error: {str(e)}"}, status=500)


@csrf_exempt
@login_required
def posture_detection(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'เฉพาะ POST requests เท่านั้น'}, status=405)

    try:
        data = json.loads(request.body)
        image_data = data.get('image')
        detect_type = data.get('detect_type', 'Photo Detection')
        
        print(detect_type)

        if image_data is None:
            return JsonResponse({"error": "ไม่พบข้อมูลรูปภาพ"}, status=400)

        if detect_type not in ['Photo Detection', 'Side-part Detection']:
            return JsonResponse({'error': 'ประเภทการตรวจจับไม่ถูกต้อง.'}, status=400)

        # แปลงรูปจาก base64
        img_data = base64.b64decode(image_data.split(',')[1])
        img = Image.open(BytesIO(img_data))
        img = np.array(img)

        # ใช้ MediaPipe Pose
        mp_pose = mp.solutions.pose
        with mp_pose.Pose(static_image_mode=True) as pose:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results_pose = pose.process(img_rgb)

            if not results_pose.pose_landmarks:
                return JsonResponse({'error': 'ไม่พบจุดสังเกตท่าทาง'}, status=400)

            # คำนวณมุม
            angles = calculate_angles(results_pose.pose_landmarks)
            score, feedback = calculate_score(angles)

            # สร้าง response_data พื้นฐาน
            response_data = {
                "message": "ตรวจจับท่าทางสำเร็จ",
                "angles": angles,
                "score": score,
                "feedback": feedback
            }


            # กรณี Photo Detection ให้บันทึกข้อมูลลงฐานข้อมูล
            if detect_type == 'Photo Detection':
                print('Photo Detection')
                posture_detection_instance = PostureDetection.objects.create(
                    user=request.user,
                    score=score
                )
                UserUsageHistory.objects.create(
                    posture_detection=posture_detection_instance,
                    detect_type='Photo Detection'
                )

                # เพิ่มเงื่อนไขให้ส่งภาพกลับเฉพาะ Photo Detection
                img_with_pose = draw_pose_landmarks(img, results_pose.pose_landmarks, angles)
                _, buffer = cv2.imencode('.jpg', img_with_pose)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                response_data["image"] = img_base64  # เพิ่มภาพเข้า response
        

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
@login_required
def save_detection_result(request):
    # ฟังก์ชั่นนี้เรียกใช้ตอนที่ผู้ใช้กด Stop Detect ในกรณี Continuous Detection
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            score = data.get('score')
            detection_duration = data.get('detection_duration')

            if score is None:
                return JsonResponse({'error': 'คะแนนเป็นข้อมูลที่จำเป็น.'}, status=400)
            
            if detection_duration is None:
                return JsonResponse({'error': 'จำเป็นต้องมีข้อมูลระยะเวลาในการตรวจจับ.'}, status=400)


            posture_detection_instance = PostureDetection.objects.create(
                user=request.user,
                score=score
            )

            UserUsageHistory.objects.create(
                posture_detection=posture_detection_instance,
                detect_type='Side-part Detection',
                detection_time=detection_duration 
            )

            return JsonResponse({"message": "บันทึกผลการตรวจจับเรียบร้อยแล้ว."})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt

def process_frame(request):
    if request.method == 'POST':
        try:
            # รับรูปภาพจากฝั่ง Frontend
            data = json.loads(request.body)
            image_data = data.get('image')

            if not image_data:
                return JsonResponse({'error': 'No image data provided'}, status=400)

            image_bytes = base64.b64decode(image_data.split(',')[1])
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # รัน YOLOv8 และตรวจจับ Bounding Box
            results = model(frame)

            # สมมติว่า YOLO ตรวจจับวัตถุ 'person' เท่านั้น
            detections = []
            for result in results[0].boxes:
                cls = int(result.cls[0])  # คลาสของวัตถุ
                if model.names[cls] == 'person':  # ตรวจจับเฉพาะคน
                    x1, y1, x2, y2 = result.xyxy[0]
                    detections.append({
                        'x': int(x1),
                        'y': int(y1),
                        'width': int(x2 - x1),
                        'height': int(y2 - y1)
                    })

            return JsonResponse({'detections': detections})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)
