import numpy as np
import mediapipe as mp
import math as m
import cv2

def calculate_angles(pose_landmarks):
    def check_symmetry(left_point, right_point, threshold=0.05):
        return abs(left_point.y - right_point.y) < threshold

    def findDistance(x1, y1, x2, y2):
        dist = m.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return dist

    def check_camera_alignment(l_shldr_x, l_shldr_y, r_shldr_x, r_shldr_y):
        offset = findDistance(l_shldr_x, l_shldr_y, r_shldr_x, r_shldr_y)
        if offset < 100:  # ค่า threshold
            return True, f"Camera Aligned: {offset:.1f}"
        else:
            return False, f"Camera Not Aligned: {offset:.1f}"

    def calculate_angle(a, b, c):
        """
        คำนวณมุมระหว่างจุด a, b, c โดยใช้เวกเตอร์
        - จุด a, b, c อยู่ในรูป (x, y) และค่า y จะถูกปรับให้พิกัดเป็น Cartesian (แกน y เพิ่มขึ้นด้านบน)
        """
        a = (a[0], 1.0 - a[1])
        b = (b[0], 1.0 - b[1])
        c = (c[0], 1.0 - c[1])

        ba = np.array([a[0] - b[0], a[1] - b[1]])
        bc = np.array([c[0] - b[0], c[1] - b[1]])

        dot_product = np.dot(ba, bc)
        magnitude_ba = np.linalg.norm(ba)
        magnitude_bc = np.linalg.norm(bc)
        cosine_angle = np.clip(dot_product / (magnitude_ba * magnitude_bc), -1.0, 1.0)

        angle = np.degrees(np.arccos(cosine_angle))
        return round(angle, 2)

    # ดึง Keypoints
    LHIP = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP]
    RHIP = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP]
    LKNEE = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_KNEE]
    LANKLE = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ANKLE]
    RANKLE = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_ANKLE]
    LSHOULDER = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
    LELBOW = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ELBOW]
    LEAR = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_EAR]
    REAR = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_EAR]
    RSHOULDER = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
    NOSE = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.NOSE]

    if not pose_landmarks or not pose_landmarks.landmark:
        raise ValueError("Pose landmarks are empty or invalid.")
    
    if LANKLE.visibility < 0.5 or RANKLE.visibility < 0.5:
        is_visible = "Feet Not Properly Placed"

    aligned, message = check_camera_alignment(LSHOULDER.x, LSHOULDER.y, RSHOULDER.x, RSHOULDER.y)
    shoulder_symmetry = check_symmetry(LSHOULDER, RSHOULDER)
    hip_symmetry = check_symmetry(LHIP, RHIP)

    # คำนวณมุม
    knee_angle = calculate_angle(
        (LHIP.x, LHIP.y),
        (LKNEE.x, LKNEE.y),  # pivot = เข่า
        (LANKLE.x, LANKLE.y)
    )

    hip_angle = calculate_angle(
        (LSHOULDER.x, LSHOULDER.y),
        (LHIP.x, LHIP.y),    # pivot = สะโพก
        (LKNEE.x, LKNEE.y)
    )

    back_angle = calculate_angle(
        (LSHOULDER.x, LSHOULDER.y),
        (LHIP.x, LHIP.y),    # pivot = สะโพก
        (LANKLE.x, LANKLE.y)
    )

    neck_angle = calculate_angle(
        (LEAR.x, LEAR.y),
        (LSHOULDER.x, LSHOULDER.y),  # pivot = ไหล่
        (LHIP.x, LHIP.y)
    )

    shoulder_angle = calculate_angle(
        (LELBOW.x, LELBOW.y),
        (LSHOULDER.x, LSHOULDER.y),  # pivot = ไหล่
        (LEAR.x, LEAR.y)
    )

    head_tilt_angle = calculate_angle(
        (NOSE.x, NOSE.y),
        (LEAR.x, LEAR.y),    # pivot = หูซ้าย
        (REAR.x, REAR.y)
    )

    return {
        "hip_angle": float(hip_angle),
        "back_angle": float(back_angle),
        "neck_angle": float(neck_angle),
        "shoulder_angle": float(shoulder_angle),
        "head_tilt_angle": float(head_tilt_angle),
        "knee_angle": float(knee_angle),
        "camera_aligned": bool(aligned),
        "shoulder_symmetry": bool(shoulder_symmetry),
        "hip_symmetry": bool(hip_symmetry),
        "camera_alignment_message": str(message)
    }

def calc_sigma_from_tail_prob(tail_prob, distance):
    """
    อธิบาย: 
      - tail_prob คือคะแนน (Score) ที่ต้องการที่ขอบ (เช่น 0.05)
      - distance คือระยะห่างระหว่างขอบ (edge) กับจุดศูนย์กลาง (center)
    
    การคำนวณ:
      tail_prob = exp(- distance^2 / (2 * sigma^2))
         => sigma = distance / sqrt(2 * ln(1 / tail_prob))
    """
    # ---- Edge Cases ----
    # 1) ถ้า tail_prob <= 0 หรือ >=1 ผิดนิยาม (ต้องอยู่ใน (0,1))
    if not (0 < tail_prob < 1):
        raise ValueError(f"tail_prob ควรอยู่ในช่วง (0,1), ได้ {tail_prob}")

    # 2) ถ้า distance เล็กมาก อาจทำให้ sigma เล็กสุดขั้ว -> โค้งชันมาก
    #    เลยตั้งระยะขั้นต่ำเป็น 1°
    MIN_DISTANCE = 1.0
    if distance < MIN_DISTANCE:
        distance = MIN_DISTANCE

    # ---- Caching การคำนวณ ln(1 / tail_prob) ----
    log_inv_tail = m.log(1.0 / tail_prob)
    denom = m.sqrt(2.0 * log_inv_tail)
    sigma = distance / denom
    return sigma

def gaussian_plateau_score(angle_deg, a, b, c, d, sigma1, sigma2):
    """
    สร้างคะแนนด้วยรูปผสม (Piecewise):
    - 0          นอกช่วง [a,d]
    - Gaussian↑  ใน (a,b) โดยมี center=b
    - 1          ใน [b,c]
    - Gaussian↓  ใน (c,d) โดยมี center=c

    ไม่ได้แก้ไขโค้ดหลัก แต่เพิ่มอธิบายตัวแปร:
      angle_deg = มุมจริง
      a,b,c,d   = ขอบช่วง Gaussian Plateau
      sigma1    = sigma ทางฝั่งซ้าย
      sigma2    = sigma ทางฝั่งขวา
    """
    if angle_deg <= a:
        return 0.0
    elif a < angle_deg < b:
        return m.exp(-((angle_deg - b)**2)/(2*(sigma1**2)))
    elif b <= angle_deg <= c:
        return 1.0
    elif c < angle_deg < d:
        return m.exp(-((angle_deg - c)**2)/(2*(sigma2**2)))
    else:
        return 0.0

def compute_plateau_angle_score(angle, a, b, c, d, tail_prob=0.05, scale_100=True):
    """
    รับมุม angle, แล้วสร้าง Score (0..1 หรือ 0..100) ด้วย Gaussian Plateau
    ในช่วง [b,c] = 1 (หรือ 100)
    ที่ขอบ a และ d = ประมาณ tail_prob (เช่น 0.05)

    ถ้า scale_100=True => คืนคะแนน 0..100
    """
    # คำนวณระยะทางซ้ายขวา
    dist_left = b - a
    dist_right = d - c

    # แก้หาค่า sigma ทั้งสองด้าน
    sigma_left = calc_sigma_from_tail_prob(tail_prob, dist_left)
    sigma_right = calc_sigma_from_tail_prob(tail_prob, dist_right)

    # เรียกใช้ Gaussian Plateau
    raw_score = gaussian_plateau_score(angle, a, b, c, d, sigma_left, sigma_right)

    if scale_100:
        return raw_score * 100.0
    else:
        return raw_score
        
def calculate_score(angles):
    # กำหนดคะแนนเริ่มต้น
    feedback = []

    hip_score = compute_plateau_angle_score(
        angles['hip_angle'],   # มุมจริง
        a=70,  b=90,  c=120, d=140,  # plateau [90..120]
        tail_prob=0.05,
        scale_100=True
    )

    if hip_score < 80:
        if angles['hip_angle'] < 90:
            feedback.append("สะโพกงอต่ำเกินไป ลองยกสะโพกขึ้นเล็กน้อย.")
        elif angles['hip_angle'] > 120:
            feedback.append("สะโพกตั้งสูงเกินไป ลองลดสะโพกลงเพื่อให้ท่าทางถูกต้อง.")

    back_score = compute_plateau_angle_score(
        angles['back_angle'],
        a=140, b=160, c=180, d=200,  # plateau [160..180]
        tail_prob=0.05,
        scale_100=True
    )

    if back_score < 80:
        if angles['back_angle'] < 160:
            feedback.append("มุมหลังต่ำเกินไป ลองนั่งตัวตรงขึ้น.")
        elif angles['back_angle'] > 180:
            feedback.append("มุมหลังสูงเกินไป ลองผ่อนคลาย หลีกเลี่ยงโค้งหลังมากเกินไป.")

    # มุมคอ (Neck Angle): ควรอยู่ระหว่าง 160° - 180°
    neck_score = compute_plateau_angle_score(
        angles['neck_angle'],
        a=145, b=160, c=180, d=195,  # plateau [160..180] (ปรับตามต้องการ)
        tail_prob=0.05,
        scale_100=True
    )

    if neck_score < 80:
        if angles['neck_angle'] < 160:
            feedback.append("คอต่ำเกินไป ลองยกศีรษะให้ตรงกระดูกสันหลัง.")
        elif angles['neck_angle'] > 180:
            feedback.append("คอเงยสูงเกินไป ลองลดศีรษะลงเพื่อหลีกเลี่ยงความตึง.")

    # มุมการเอียงศีรษะ (Head Tilt Angle): ควรอยู่ระหว่าง 85° - 95°
    head_score = compute_plateau_angle_score(
        angles['head_tilt_angle'],
        a=65, b=85, c=95, d=115,     # plateau [85..95]
        tail_prob=0.05,
        scale_100=True
    )

    if head_score < 80:
        if angles['head_tilt_angle'] < 85:
            feedback.append("ศีรษะเอียงต่ำเกินไป ลองยกขึ้นเพื่อหลีกเลี่ยงการห่อไหล่.")
        elif angles['head_tilt_angle'] > 95:
            feedback.append("ศีรษะเอียงสูงเกินไป ลองลดลงเพื่อหลีกเลี่ยงความตึงของคอ.")

    knee_score = compute_plateau_angle_score(
        angles['knee_angle'],
        a = 70 , b = 90 , c = 130 , d = 150,  # plateau [90..130]
        tail_prob=0.05,
        scale_100=True
    )

    if knee_score < 80:
        if angles['knee_angle'] < 90:
            feedback.append("เข่างอเกินไป ลองยกเข่าขึ้นเล็กน้อย.")
        elif angles['knee_angle'] > 130:
            feedback.append("เข่าตั้งสูงเกินไป ลองลดเข่าลงเพื่อให้ท่าทางถูกต้อง.")
    

    


    # ตรวจสอบว่าคะแนนต่ำกว่า 0 หรือไม่
    scores_list = [hip_score, back_score, neck_score, head_score]
    final_score = sum(scores_list) / len(scores_list)

    # เพิ่มข้อเสนอแนะตามคะแนนที่ได้
    if final_score >= 90:
        feedback.append("ท่าทางสมบูรณ์แบบ! ต่อไปทำดีแบบนี้เรื่อย ๆ.")
    elif final_score >= 80:
        feedback.append("ท่าทางดีอยู่แล้ว แต่ยังมีการปรับปรุงเล็กน้อยที่ต้องทำ.")
    elif final_score >= 60:
        feedback.append("ท่าทางพอใช้ได้ แต่ควรปรับปรุงเพิ่มเติม.")
    else:
        feedback.append("ท่าทางต้องการการปรับปรุงมากเพื่อสุขภาพที่ดีขึ้น.")

    return final_score, feedback

def draw_pose_landmarks(image, pose_landmarks, angles):
    """
    วาด keypoints, เวกเตอร์, และมุมลงในภาพ
    """
    image_h, image_w, _ = image.shape

    # กำหนดสีและขนาด
    color_keypoint = (0, 255, 0)  # สีเขียว
    color_line = (255, 0, 0)  # สีน้ำเงิน
    font_color = (0, 0, 255)  # สีแดง
    font_scale = 0.5
    thickness = 2

    # Keypoints ที่สำคัญ
    keypoints = {
        "LEFT_HIP": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP],
        "RIGHT_HIP": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP],
        "LEFT_KNEE": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_KNEE],
        "RIGHT_KNEE": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_KNEE],
        "LEFT_ANKLE": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ANKLE],
        "RIGHT_ANKLE": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_ANKLE],
        "LEFT_SHOULDER": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER],
        "RIGHT_SHOULDER": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER],
        "NOSE": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.NOSE],
        "LEFT_ELBOW": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ELBOW],
        "LEFT_EAR": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_EAR],
        "RIGHT_EAR": pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_EAR]
    }

    # วาด keypoints ลงในภาพ
    for landmark_id, point in keypoints.items():
        x, y = int(point.x * image_w), int(point.y * image_h)
        keypoint_name = mp.solutions.pose.PoseLandmark[landmark_id].name  # ดึงชื่อ keypoint ที่ถูกต้อง
        
        # ปรับตำแหน่งข้อความให้อยู่เหนือจุดเล็กน้อยเพื่อให้อ่านง่ายขึ้น
        text_x, text_y = x, y - 10  
    
        # วาดชื่อ keypoint ลงในภาพ
        cv2.putText(image, keypoint_name, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_color, thickness)
    
        # วาดจุด keypoint ลงในภาพ
        cv2.circle(image, (x, y), 5, color_keypoint, -1)  # วาดจุด keypoint

    # วาดเส้นเชื่อมโยงโครงสร้างของร่างกาย
    connections = [
        ("LEFT_SHOULDER", "LEFT_HIP"),
        ("LEFT_HIP", "LEFT_KNEE"),
        ("LEFT_KNEE", "LEFT_ANKLE"),
        ("RIGHT_SHOULDER", "RIGHT_HIP"),
        ("RIGHT_HIP", "RIGHT_KNEE"),
        ("RIGHT_KNEE", "RIGHT_ANKLE"),
        ("LEFT_SHOULDER", "RIGHT_SHOULDER"),
        ("LEFT_HIP", "RIGHT_HIP")
    ]
    for p1, p2 in connections:
        x1, y1 = int(keypoints[p1].x * image_w), int(keypoints[p1].y * image_h)
        x2, y2 = int(keypoints[p2].x * image_w), int(keypoints[p2].y * image_h)
        cv2.line(image, (x1, y1), (x2, y2), color_line, thickness)

    # สร้างข้อมูลเวกเตอร์สำหรับมุมที่คำนวณได้
    vector_info = {
        "hip_angle": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"),
        "back_angle": ("LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE"),
        "neck_angle": ("NOSE", "LEFT_SHOULDER", "LEFT_HIP"),
        "knee_angle": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"),
        "head_tilt_angle": ("NOSE", "LEFT_EAR", "RIGHT_EAR"),
        "shoulder_angle": ("LEFT_ELBOW", "LEFT_SHOULDER", "LEFT_EAR")
    }


    # ใส่ค่ามุมลงในภาพ
    for idx, (angle_name, _) in enumerate(vector_info.items()):
        text = f"{angle_name}: {angles[angle_name]}°"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        x = image_w - text_size[0] - 20  # ขยับให้อยู่ชิดขวาพอดี
        y = 30 + (idx * 30)
    
        cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_color, thickness)

    return image
