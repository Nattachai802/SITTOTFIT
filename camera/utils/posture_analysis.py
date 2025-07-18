import numpy as np
import mediapipe as mp
import math as m
import cv2
from filterpy.kalman import KalmanFilter
import joblib


bst = joblib.load("camera/utils/spine_risk_lgbm.pkl")


def spine_risk_predict(angle_dict):
    feats = [[angle_dict[k] for k in
              ["hip_angle", "back_angle", "neck_angle",
               "shoulder_angle", "head_tilt_angle", "knee_angle"]]]
    
    print("Input features:", feats)
    prob = float(bst.predict(feats)[0])
    print(prob)    # 0-1
    return prob

def detect_extreme_posture(landmarks, width: int, *,
                           com_thr: float = 0.15,
                           shoulder_thr: float = 10,
                           head_offset_thr: float = 0.18,
                           knee_hip_diff: float = 0.05):
    """
    ตรวจพฤติกรรม "ท่าพิลึก" โดยไม่ระบุซ้าย/ขวา
    
    Returns
    -------
    flag : bool      มีท่าพิลึกไหม
    msg  : str       ข้อความไทยสั้น ๆ สำหรับ feedback
    code : str|null  รหัสเหตุผล เช่น 'COM_LEAN', 'SHOULDER_TILT', 'HEAD_OFFSET', 'KNEE_HIGH', 'CRITICAL_POSTURE'
    """
    # ----------- ดึง landmark ที่จำเป็น ------------
    # Access landmarks correctly
    LHIP, RHIP = [landmarks.landmark[i] for i in (
        mp.solutions.pose.PoseLandmark.LEFT_HIP.value,
        mp.solutions.pose.PoseLandmark.RIGHT_HIP.value)]
    LSH,  RSH = [landmarks.landmark[i] for i in (
        mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value,
        mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value)]
    LKNEE = landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value]
    NOSE = landmarks.landmark[mp.solutions.pose.PoseLandmark.NOSE.value]

    # ----------- 1) COM offset -----------------------
    mid_hip_x = (LHIP.x + RHIP.x) / 2
    mid_sh_x  = (LSH.x  + RSH.x ) / 2
    com_x     = 0.6 * mid_hip_x + 0.4 * mid_sh_x
    offset_x  = abs(com_x - 0.5)
    com_flag = offset_x > com_thr

    # ----------- 2) Shoulder tilt --------------------
    dx, dy = RSH.x - LSH.x, RSH.y - LSH.y
    shoulder_deg = abs(m.degrees(m.atan2(dy, dx)))
    shoulder_flag = shoulder_deg > shoulder_thr

    # ----------- 3) Head offset ----------------------
    head_off = abs(NOSE.x - 0.5)
    if head_off > head_offset_thr:
        return True, "ศีรษะเยื้องออกจากแกนกลางมาก", "HEAD_OFFSET"

    # ----------- 4) Knee higher than hip -------------
    if LKNEE.visibility > 0.5 and LHIP.visibility > 0.5:
        if LKNEE.y < LHIP.y - knee_hip_diff:
            return True, "เข่าสูงกว่าสะโพกผิดปกติ", "KNEE_HIGH"

    # ----------- 5) Critical posture -----------------
    if com_flag and shoulder_flag:
        return True, "ลำตัวเอียงและไหล่เอียงพร้อมกัน", "CRITICAL_POSTURE"

    # ----------- รายการธรรมดา -----------------------
    if com_flag:
        perc = offset_x * 100
        return True, f"ลำตัวเอียงจากแกนกลาง {perc:.0f}%", "COM_LEAN"
    
    if shoulder_flag:
        return True, f"ไหล่เอียง {shoulder_deg:.1f}°", "SHOULDER_TILT"

    return False, "", None


def init_kf(dt=5.0):
    """สร้าง Kalman filter 2-D constant-velocity"""
    kf = KalmanFilter(dim_x=4, dim_z=2)          # [x, y, vx, vy]
    kf.F = np.array([[1,0,dt,0], [0,1,0,dt],
                     [0,0,1,0],  [0,0,0,1]])     # model: x' = x + v·dt
    kf.H = np.array([[1,0,0,0], [0,1,0,0]])      # วัดได้แค่ (x,y)
    kf.Q = np.diag([1e-2, 1e-2, 1e-1, 1e-1])     # process-noise (ตั้งกว้างเพราะ dt=5 s)
    kf.P *= 1e-1                                 # เริ่มต้นเชื่อค่าที่วัด
    return kf

def kalman_step(point_xy, visibility, kf):

    kf.predict()
    if visibility > 0.01:
        # Convert point to proper shape for Kalman update
        z = np.asarray(point_xy)  # Shape: (2,1)
        
        # Update measurement noise based on visibility
        kf.R = np.eye(2) * (2e-3 / visibility)
        
        # Update filter with measurement
        kf.update(z)
    
    return kf.x[:2].flatten()

num_pts = len(mp.solutions.pose.PoseLandmark)    # >> 33
kf_bank = {i: init_kf(dt=5.0) for i in range(num_pts)}

class SimpleLandmark:
    """Simple class to hold smoothed landmark data"""
    def __init__(self, x, y, visibility):
        self.x = x
        self.y = y
        self.visibility = visibility

def calculate_angles(pose_landmarks,previous_pressure=None):
    # Smooth landmarks and convert to SimpleLandmark objects
    smoothed = []  
    for idx, lm in enumerate(pose_landmarks.landmark):
        xy = (lm.x, lm.y)
        vis = lm.visibility
        xy_sm = kalman_step(xy, vis, kf_bank[idx])
        smoothed.append(SimpleLandmark(xy_sm[0], xy_sm[1], vis))

    # ---------- 2. helper ฟังก์ชันภายใน ----------
    def safe_angle(landmark_a, landmark_b, landmark_c, threshold=0.5):
        """Return angle (deg) ifทุกจุดเห็นชัด, otherwise None"""
        if (landmark_a.visibility < threshold or
            landmark_b.visibility < threshold or
            landmark_c.visibility < threshold):
            return None
        return calculate_angle((landmark_a.x, landmark_a.y),
                               (landmark_b.x, landmark_b.y),
                               (landmark_c.x, landmark_c.y))

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
    def midpoint(a, b):
        return ((a.x + b.x) / 2.0, (a.y + b.y) / 2.0)

    # ---------- 3. ดึงจุดสำคัญ ----------
    LHIP  = smoothed[mp.solutions.pose.PoseLandmark.LEFT_HIP.value]
    RHIP  = smoothed[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value]
    LKNEE = smoothed[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value]
    LANKLE = smoothed[mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value]
    RANKLE = smoothed[mp.solutions.pose.PoseLandmark.RIGHT_ANKLE.value]
    LSHOULDER = smoothed[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value]
    LELBOW = smoothed[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value]
    RELBOW = smoothed[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value]
    LEAR = smoothed[mp.solutions.pose.PoseLandmark.LEFT_EAR.value]
    REAR = smoothed[mp.solutions.pose.PoseLandmark.RIGHT_EAR.value]
    RSHOULDER = smoothed[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value]
    NOSE = smoothed[mp.solutions.pose.PoseLandmark.NOSE.value]

    shoulder_abd_L = safe_angle(LELBOW, LSHOULDER, LEAR)
    shoulder_abd_R = safe_angle(RELBOW, RSHOULDER, REAR)
    print("Shoulder Abduction Left:", shoulder_abd_L, "Right:", shoulder_abd_R)

    # Initialize is_visible
    is_visible = True  # Set default value to True

    if not pose_landmarks or not pose_landmarks.landmark:
        raise ValueError("Pose landmarks are empty or invalid.")
    
    if LANKLE.visibility < 0.3 or RANKLE.visibility < 0.3:
        is_visible = False

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

    mid_shoulder = midpoint(LSHOULDER, RSHOULDER)
    mid_hip = midpoint(LHIP, RHIP)
    spine_base = midpoint(LHIP, RHIP)
    spine_top = midpoint(LSHOULDER, RSHOULDER)
    mid_ear = midpoint(LEAR, REAR)

    back_angle = calculate_angle(
        (spine_top[0], spine_top[1]),
        (mid_hip[0],  mid_hip[1]),   # pivot
        (LANKLE.x,    LANKLE.y)
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

    # มุมเอียงศีรษะ (Head Tilt Angle)
    head_tilt_angle = calculate_angle(
        (NOSE.x, NOSE.y),
        (mid_ear[0], mid_ear[1]),
        (LSHOULDER.x, LSHOULDER.y)  # pivot = ไหล่
    )

    # ---------- 5. Seat‑pressure heuristic ----------
    seat_half_norm = max(abs(LHIP.x - RHIP.x)/2, 1e-6)
    mid_hip_x = (LHIP.x + RHIP.x)/2
    mid_sh_x  = (LSHOULDER.x + RSHOULDER.x)/2
    com_x_norm = 0.6 * mid_hip_x + 0.4 * mid_sh_x
    raw_ratio = (com_x_norm - mid_hip_x) / seat_half_norm  # -1..1
    raw_ratio = float(np.clip(raw_ratio, -1.0, 1.0))

    if previous_pressure is None:
        seat_pressure_ratio = raw_ratio
    else:
        alpha = 0.2
        seat_pressure_ratio = alpha * raw_ratio + (1 - alpha) * previous_pressure
    
    calculate_angles._last_pressure = seat_pressure_ratio


    # ---------- 6. คืนค่าผลลัพธ์ทั้งหมด ----------
    return {
        "hip_angle": float(hip_angle),
        "back_angle": float(back_angle),
        "neck_angle": float(neck_angle),
        "shoulder_angle": float(shoulder_angle),
        "head_tilt_angle": float(head_tilt_angle),
        "knee_angle": float(knee_angle),
        "is_visible": bool(is_visible),
        "camera_aligned": bool(aligned),
        "seat_pressure_ratio": float(seat_pressure_ratio),
        "shoulder_symmetry": bool(shoulder_symmetry),
        "hip_symmetry": bool(hip_symmetry),
        "camera_alignment_message": str(message),
        "shoulder_abd_L": float(shoulder_abd_L) if shoulder_abd_L is not None else None,
        "shoulder_abd_R": float(shoulder_abd_R) if shoulder_abd_R is not None else None,
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
        
def calculate_score(angles,
                    width=None,
                    pose_landmarks=None):
    feedback = []
    final_score = 100

    # Add counter as static variable
    if not hasattr(calculate_score, 'asymmetry_counter'):
        calculate_score.asymmetry_counter = 0
    
    extreme_flag, extreme_msg, code = detect_extreme_posture(
        pose_landmarks,   # เพิ่ม field นี้ใน calculate_angles
        width=width,
    )
    if extreme_flag:
        feedback.append("⚠️ " + extreme_msg)
        final_score -= 10          # หรือคง 0 แต่ set risk_flag
        angles['extreme'] = code

    # กำหนดคะแนนเริ่มต้น
    feedback = []

    SP_result = spine_risk_predict(angles)

    if SP_result >= 0.7:
        feedback.append("⚠️ Critical: ความเสี่ยงกระดูกสันหลังสูงมาก! กรุณาปรับท่าทางทันที.")
    elif 0.4 <= SP_result < 0.7:
        feedback.append("⚠️ Warning: มีความเสี่ยงกระดูกสันหลังระดับปานกลาง. ลองปรับท่าทางเพื่อหลีกเลี่ยงปัญหา.")
    else:
        feedback.append("✅ Tip: ท่าทางปกติ. ทำดีต่อไป!")


    if not angles['is_visible']:
        feedback.append("ไม่สามารถวิเคราะห์ท่าทางได้ เนื่องจากบางจุดไม่ชัดเจน.")
        return 0, feedback

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

    seat_ratio = angles.get("seat_pressure_ratio")  # −1..1  (None if not available)
    if seat_ratio is not None:
        if abs(seat_ratio) >= 0.45:
            side = "ซ้าย" if seat_ratio < 0 else "ขวา"
            feedback.append(f"ลงน้ำหนัก{side}ต่อเนื่อง ควรขยับให้น้ำหนักสมดุล")
        elif abs(seat_ratio) >= 0.25:
            side = "ซ้าย" if seat_ratio < 0 else "ขวา"
            feedback.append(f"น้ำหนักเอนไปทาง{side} {abs(seat_ratio)*100:.0f}% ลองขยับเล็กน้อย")

    if knee_score < 80:
        if angles['knee_angle'] < 90:
            feedback.append("เข่างอเกินไป ลองยกเข่าขึ้นเล็กน้อย.")
        elif angles['knee_angle'] > 130:
            feedback.append("เข่าตั้งสูงเกินไป ลองลดเข่าลงเพื่อให้ท่าทางถูกต้อง.")
    
    # Calculate shoulder angle and symmetry
    shoulder_abd_L = angles.get('shoulder_abd_L')
    shoulder_abd_R = angles.get('shoulder_abd_R')
    
    # Calculate mean shoulder angle only if valid values exist
    valid_angles = [angle for angle in [shoulder_abd_L, shoulder_abd_R] if angle is not None]
    if valid_angles:
        angles['shoulder_angle'] = np.mean(valid_angles)
        shoulder_score = compute_plateau_angle_score(
            angles['shoulder_angle'],
            a=65, b=85, c=95, d=115,  # plateau [85..95]
            tail_prob=0.05,
            scale_100=True
        )
    else:
        angles['shoulder_angle'] = None  # ไม่มีค่าที่ถูกต้อง
        shoulder_score = 0  # ให้คะแนน 0 เมื่อไม่สามารถวัดมุมได้

    # Calculate shoulder symmetry score
    if shoulder_abd_L is not None and shoulder_abd_R is not None:
        delta_shldr = abs(shoulder_abd_L - shoulder_abd_R)
        symmetry_shldr_score = gaussian_plateau_score(
            delta_shldr,                # x
            a=0, b=5, c=10, d=15,      # plateau 0–5°, risk >10°
            sigma1=2, sigma2=2          # sigma values for Gaussian curves
        )
        
        # Add asymmetry detection with counter
        if delta_shldr > 10:
            calculate_score.asymmetry_counter += 1
            if calculate_score.asymmetry_counter >= 15:  # 0.5 วินาที @30 fps
                feedback.append(f"ไหล่เอียง {delta_shldr:.1f}° กรุณานั่งตัวตรง")
                calculate_score.asymmetry_counter = 0    # reset after warning
        else:
            calculate_score.asymmetry_counter = 0
            
        if symmetry_shldr_score < 0.8:  # less than 80%
            feedback.append("ไหล่ไม่สมมาตร ลองปรับให้ไหล่ทั้งสองข้างอยู่ในระดับเดียวกัน")
    else:
        symmetry_shldr_score = 0  
        delta_shldr = None
        calculate_score.asymmetry_counter = 0  # Reset counter when shoulders not detected

    # Calculate weighted average score
    scores_list = [
        hip_score,              # 25%
        back_score,            # 25%
        neck_score,            # 25%
        head_score,            # 10%
        shoulder_score,        # 5%
        symmetry_shldr_score * 100  # 10%
    ]
    
    weights = [0.25, 0.25, 0.25, 0.10, 0.05, 0.10]
    final_score = np.average(scores_list, weights=weights)

    # Add overall feedback based on weighted score
    if final_score >= 90:
        feedback.append("ท่าทางสมบูรณ์แบบ! ต่อไปทำดีแบบนี้เรื่อย ๆ")
    elif final_score >= 80:
        feedback.append("ท่าทางดีอยู่แล้ว แต่ยังมีการปรับปรุงเล็กน้อยที่ต้องทำ")
    elif final_score >= 60:
        feedback.append("ท่าทางพอใช้ได้ แต่ควรปรับปรุงเพิ่มเติม")
    else:
        feedback.append("ท่าทางต้องการการปรับปรุงมากเพื่อสุขภาพที่ดีขึ้น")

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
