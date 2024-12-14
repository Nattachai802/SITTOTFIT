from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Notification"

    def ready(self):
        # เชื่อมต่อ signal 'post_migrate' ที่จะถูกเรียกใช้งานหลังจาก migration เสร็จสิ้น
        post_migrate.connect(self.on_migrate, sender=self)

    def on_migrate(self, sender, **kwargs):
        # ฟังก์ชันนี้จะทำงานหลังจาก migration เสร็จสิ้น
        print("Database is ready after migration.")

        # เริ่ม cron scheduler อย่างปลอดภัยหลังจาก migration
        from Notification import cron
        cron.start_scheduler()
