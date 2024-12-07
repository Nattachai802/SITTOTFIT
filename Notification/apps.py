from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Notification"

    def ready(self):
        # เชื่อมต่อ signal 'post_migrate' ก่อนที่จะเริ่ม cron scheduler
        post_migrate.connect(self.on_migrate, sender=self)
        
        # เรียกใช้งาน cron.start_scheduler() หลังจากเชื่อมต่อ signal
        from Notification import cron
        cron.start_scheduler()

    def on_migrate(self, sender, **kwargs):
        # ฟังก์ชันนี้จะทำงานหลังจาก migration เสร็จสิ้น
        print("Database is ready after migration.")
