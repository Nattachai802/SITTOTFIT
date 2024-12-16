from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .models import NotificationSettings, FCMToken
from .firebase_service import send_multiple_notifications
from django_apscheduler.models import DjangoJobExecution
from django.db import transaction
import threading

# สร้าง BackgroundScheduler
scheduler = BackgroundScheduler()

# ตัวแปรล็อคเพื่อป้องกันการทำงานซ้ำ
lock = threading.Lock()

def send_notifications():
    """
    ฟังก์ชันที่รันตาม Scheduler เพื่อส่ง Notification
    """
    # ใช้ lock เพื่อป้องกันการทำงานซ้ำ
    with lock:
        settings_list = NotificationSettings.objects.filter(is_enabled=True)
        tokens = []  # เก็บ FCM Token ที่ต้องส่ง

        for settings in settings_list:
            try:
                fcm_token = FCMToken.objects.get(user=settings.user).token
                tokens.append(fcm_token)
            except FCMToken.DoesNotExist:
                print(f"ไม่มี FCM Token สำหรับผู้ใช้ {settings.user.username}")

        # ส่ง Notification หากมี token
        if tokens:
            send_multiple_notifications(tokens, "การแจ้งเตือน", "คุณได้รับการแจ้งเตือนตามการตั้งค่าของคุณ")

# เพิ่ม JobStore และ Job
def start_scheduler():
    print('start_corn')
    try:
        # ถ้าหาก scheduler เริ่มไปแล้ว ให้ไม่เริ่มใหม่
        if not scheduler.running:
            scheduler.add_jobstore(DjangoJobStore(), "default")

            # ตรวจสอบว่ามี job นี้อยู่แล้วหรือไม่
            existing_job = scheduler.get_job('send_notifications_job')
            if existing_job:
                print("Job already exists, skipping job creation.")
            else:
                # เพิ่ม Job ส่ง Notification
                scheduler.add_job(
                    send_notifications, 
                    'interval', 
                    minutes=15, 
                    id='send_notifications_job',  # ID ของงาน
                    replace_existing=True
                )

            scheduler.start()
            print("Scheduler started successfully")
        else:
            print("Scheduler is already running.")
    except Exception as e:
        print(f"Error starting scheduler: {e}")
