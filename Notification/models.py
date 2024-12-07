from django.db import models
from base.models import *
# Create your models here.
class FCMToken(models.Model):
    user = models.OneToOneField(UserInfomation, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)  # เก็บ FCM Token
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.token}"

class NotificationSettings(models.Model):
    user = models.OneToOneField(UserInfomation, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)  # เปิด/ปิดการแจ้งเตือน
    interval_minutes = models.IntegerField(
        choices=[(45, '45 นาที'), (60, '60 นาที'),(1,' 1 นาที')],
        default=45
    )

    def __str__(self):
        return f"Notification Settings for {self.user.username}"