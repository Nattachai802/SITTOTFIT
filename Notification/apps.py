from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import threading

class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Notification"

    def ready(self):
        from Notification import cron
        if not any(thread.name == "SchedulerThread" for thread in threading.enumerate()):
            print('Start')
            cron.start_scheduler()

    def on_migrate(self, sender, **kwargs):
        print("Database is ready after migration.")

