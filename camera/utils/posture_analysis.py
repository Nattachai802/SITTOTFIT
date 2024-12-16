import numpy as np
import mediapipe as mp
import math as m
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
    hip_angle = calculate_angle(
                            (LHIP.x, LHIP.y),
                            (LKNEE.x, LKNEE.y),
                            (LANKLE.x, LANKLE.y)
    )
    back_angle = calculate_angle(
                            (LSHOULDER.x, LSHOULDER.y),
                            (LHIP.x, LHIP.y),
                            (LKNEE.x, LKNEE.y)
    )

    neck_angle = calculate_angle(
                            (LEAR.x, LEAR.y),
                            (LSHOULDER.x, LSHOULDER.y),
                            (LHIP.x, LHIP.y)
    )
    shoulder_angle = calculate_angle(
                            (LELBOW.x, LELBOW.y),
                            (LSHOULDER.x, LSHOULDER.y),
                            (LEAR.x, LEAR.y)
    )
    head_tilt_angle = calculate_angle(
                            (NOSE.x, NOSE.y),   # จมูก
                            (LEAR.x, LEAR.y),   # หูซ้าย
                            (REAR.x, REAR.y)
    )
    knee_angle = calculate_angle(
                            (LHIP.x, LHIP.y),
                            (LKNEE.x, LKNEE.y),
                            (LANKLE.x, LANKLE.y)
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

def calculate_score(angles):
    # กำหนดคะแนนเริ่มต้น
    score = 100
    feedback = []

    # มุมสะโพก (Hip Angle): ควรอยู่ระหว่าง 90° - 120°
    hip_angle = angles['hip_angle']
    if not (90 <= hip_angle <= 120):
        error = abs(hip_angle - 105)  # ค่าอ้างอิงที่เหมาะสมคือ 105°
        feedback.append(f"ข้อผิดพลาดมุมสะโพก: {error:.1f}°")
        score -= min(15, error * 0.75)
        if hip_angle < 90:
            feedback.append("มุมสะโพกต่ำเกินไป ลองยกสะโพกขึ้นเล็กน้อย.")
        elif hip_angle > 120:
            feedback.append("มุมสะโพกสูงเกินไป ลองลดสะโพกลงเพื่อให้ท่าทางถูกต้อง.")

    # มุมหลัง (Back Angle): ควรอยู่ระหว่าง 160° - 180°
    back_angle = angles['back_angle']
    if not (160 <= back_angle <= 180):
        error = abs(back_angle - 170)  # ค่าอ้างอิงที่เหมาะสมคือ 170°
        feedback.append(f"ข้อผิดพลาดมุมหลัง: {error:.1f}°")
        score -= min(15, error * 0.75)
        if back_angle < 160:
            feedback.append("มุมหลังต่ำเกินไป ลองนั่งตัวตรงขึ้น.")
        elif back_angle > 180:
            feedback.append("มุมหลังสูงเกินไป ลองผ่อนคลายและหลีกเลี่ยงการโค้งหลังมากเกินไป.")

    # มุมคอ (Neck Angle): ควรอยู่ระหว่าง 160° - 180°
    neck_angle = angles['neck_angle']
    if not (160 <= neck_angle <= 180):
        error = abs(neck_angle - 170)  # ค่าอ้างอิงที่เหมาะสมคือ 170°
        feedback.append(f"ข้อผิดพลาดมุมคอ: {error:.1f}°")
        score -= min(15, error * 0.75)
        if neck_angle < 160:
            feedback.append("มุมคอต่ำเกินไป ลองยกศีรษะให้ตรงกับกระดูกสันหลัง.")
        elif neck_angle > 180:
            feedback.append("มุมคอสูงเกินไป ลองลดศีรษะลงเล็กน้อยเพื่อหลีกเลี่ยงความตึงเครียด.")

    # มุมการเอียงศีรษะ (Head Tilt Angle): ควรอยู่ระหว่าง 85° - 95°
    head_tilt = angles['head_tilt_angle']
    if not (85 <= head_tilt <= 95):
        error = abs(head_tilt - 90)  # ค่าอ้างอิงที่เหมาะสมคือ 90°
        feedback.append(f"ข้อผิดพลาดมุมการเอียงศีรษะ: {error:.1f}°")
        score -= min(15, error * 0.75)
        if head_tilt < 85:
            feedback.append("มุมการเอียงศีรษะต่ำเกินไป ลองยกศีรษะขึ้นเพื่อหลีกเลี่ยงการห่อไหล่.")
        elif head_tilt > 95:
            feedback.append("มุมการเอียงศีรษะสูงเกินไป ลองลดศีรษะลงเพื่อหลีกเลี่ยงการตึงของคอ.")

    # ตรวจสอบว่าคะแนนต่ำกว่า 0 หรือไม่
    score = max(score, 0)

    # เพิ่มข้อเสนอแนะตามคะแนนที่ได้
    if score == 100:
        feedback.append("ท่าทางสมบูรณ์แบบ! ต่อไปทำดีแบบนี้เรื่อย ๆ.")
    elif score >= 80:
        feedback.append("ท่าทางดีอยู่แล้ว แต่ยังมีการปรับปรุงเล็กน้อยที่ต้องทำ.")
    elif score >= 60:
        feedback.append("ท่าทางพอใช้ได้ แต่ควรปรับปรุงเพิ่มเติม.")
    else:
        feedback.append("ท่าทางต้องการการปรับปรุงมากเพื่อสุขภาพที่ดีขึ้น.")

    return score, feedback
