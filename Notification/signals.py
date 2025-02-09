from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from base.models import UserInfomation
from .models import NotificationSettings, FCMToken

@receiver(post_save, sender=UserInfomation)
def create_notification_settings(sender, instance, created, **kwargs):
    """
    สร้างการตั้งค่าแจ้งเตือนเริ่มต้นสำหรับผู้ใช้ใหม่
    """
    if created:
        with transaction.atomic():
            NotificationSettings.objects.get_or_create(
                user=instance,
                defaults={
                    'is_enabled': False,
                    'interval_minutes': 45  # ค่าเริ่มต้น
                }
            )
            FCMToken.objects.get_or_create(
                user=instance,
                defaults={'token': ''}  # สร้าง placeholder สำหรับ token
            )