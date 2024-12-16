from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PostureDetection, UserUsageHistory
'''
@receiver(post_save, sender=PostureDetection)
def create_user_usage_history(sender, instance, created, **kwargs):
    if created:
        # สร้างข้อมูลใน UserUsageHistory เมื่อมี PostureDetection ใหม่
        UserUsageHistory.objects.create(
            posture_detection=instance,  # เชื่อมโยงกับ PostureDetection
            timestamp=instance.timestamp,  # ใช้ timestamp เดียวกัน
            detect_type='Simple Detection'  # หรือกำหนดประเภทตามที่ต้องการ
        )
'''
