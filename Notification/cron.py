from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .models import NotificationSettings, FCMToken
from .firebase_service import send_multiple_notifications
from django_apscheduler.models import DjangoJobExecution
from django.db import transaction
import threading
from datetime import datetime, timedelta

# สร้าง BackgroundScheduler
scheduler = BackgroundScheduler()
lock = threading.Lock()

def send_notifications(interval):
    """
    ฟังก์ชันที่รันตาม Scheduler เพื่อส่ง Notification
    Args:
        interval (int): ระยะเวลาการแจ้งเตือนเป็นนาที
    """
    with lock:
        try:
            print(f"Running notification job for interval: {interval} minutes")
            
            # ดึงเฉพาะผู้ใช้ที่มีการตั้งค่าตรงกับ interval ที่ระบุ
            settings_list = NotificationSettings.objects.filter(
                is_enabled=True,
                interval_minutes=interval
            ).select_related('user')
            
            tokens = []
            for settings in settings_list:
                try:
                    fcm_token = FCMToken.objects.get(user=settings.user)
                    if fcm_token.token:
                        tokens.append(fcm_token.token)
                except FCMToken.DoesNotExist:
                    print(f"ไม่มี FCM Token สำหรับผู้ใช้ {settings.user.username}")
                    continue
            
            if tokens:
                print(f"Sending notifications for {interval} minute interval to {len(tokens)} users")
                send_multiple_notifications(
                    tokens,
                    "การแจ้งเตือนออกกำลังกาย",
                    f"ถึงเวลาออกกำลังกายแล้ว! (แจ้งเตือนทุก {interval} นาที)"
                )
            else:
                print(f"No users to notify for {interval} minute interval")
                
        except Exception as e:
            print(f"Error in send_notifications for interval {interval}: {e}")

def create_notification_job(interval):
    """
    สร้าง job สำหรับการแจ้งเตือนที่ interval ที่กำหนด
    Args:
        interval (int): ระยะเวลาการแจ้งเตือนเป็นนาที
    """
    job_id = f'send_notifications_job_{interval}'
    scheduler.add_job(
        send_notifications,
        'interval',
        minutes=interval,
        id=job_id,
        args=[interval],
        replace_existing=True,
        next_run_time=datetime.now()  # เริ่มทำงานทันที
    )
    print(f"Created notification job for {interval} minute interval with ID: {job_id}")

def start_scheduler():
    print("Starting scheduler...")
    try:
        if not scheduler.running:
            scheduler.add_jobstore(DjangoJobStore(), "default")
            
            # ลบ jobs เก่า
            for job in scheduler.get_jobs():
                scheduler.remove_job(job.id)
                print(f"Removed existing job: {job.id}")
            
            # สร้าง jobs ใหม่
            intervals = [1, 45, 60]
            for interval in intervals:
                create_notification_job(interval)
            
            scheduler.start()
            print("Scheduler started successfully")
        else:
            print("Scheduler is already running")
    except Exception as e:
        print(f"Error starting scheduler: {e}")