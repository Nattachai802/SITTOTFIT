from django.db.models.signals import post_save
from django.dispatch import receiver
from base.models import UserInfomation
from .models import NotificationSettings, FCMToken

@receiver(post_save, sender=UserInfomation)
def create_notification_settings(sender, instance, created, **kwargs):

    if created:
        # ตรวจสอบว่า NotificationSettings และ FCMToken สำหรับ user นี้มีอยู่แล้วหรือไม่
        NotificationSettings.objects.get_or_create(user=instance.user)
        FCMToken.objects.get_or_create(user=instance.user)
