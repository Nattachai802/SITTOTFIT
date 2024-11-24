
from django.db import models
from django.contrib.auth.models import AbstractUser

class UserInfomation(AbstractUser):
    contact_number = models.CharField(max_length= 20 , blank = True)
    role = models.CharField(max_length= 50 )
    created_at = models.DateTimeField(auto_now_add= True)

    def __str__(self):
        return self.username

class PersonalInformation(models.Model):
    user = models.OneToOneField(UserInfomation, on_delete=models.CASCADE, null=True, blank=True)
    goal = models.CharField(
        max_length=50, 
        choices=[
            ('Improve posture', 'Improve posture'),
            ('Health maintenance', 'Health maintenance'),
            ('Posture correction', 'Posture correction')
        ],
        null=True,
        blank=True
    )
    job_name = models.CharField(max_length=100, null=True, blank=True)
    job_type = models.CharField(max_length=100, null=True, blank=True)
    job_hours = models.FloatField(null=True, blank=True)
    break_hours = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username if self.user else "No User"} - {self.job_name or "No Job Name"}'
    
class PersonalHealthInformation(models.Model):
    user = models.OneToOneField(UserInfomation, on_delete=models.CASCADE, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    has_pain = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f'{self.user.username if self.user else "No User"} - Health Info'
    
class UserUsageHistory(models.Model):
    user = models.ForeignKey(UserInfomation, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    detect_type = models.CharField(max_length=50, choices=[
        ('Simple Detection', 'Simple Detection'),
        ('Advanced Detection', 'Advanced Detection')
    ])
    usage_count = models.IntegerField()

    def __str__(self):
        return f'{self.user.username} - {self.detect_type}'

class PostureDetection(models.Model):
    user = models.ForeignKey(UserInfomation, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    detection_time = models.DurationField()
    score = models.IntegerField()

    def __str__(self):
        return f'{self.user.username} - Posture Score: {self.score}'

class NotificationLog(models.Model):
    user = models.ForeignKey(UserInfomation, on_delete=models.CASCADE)
    message = models.TextField()
    notification_time = models.DateTimeField(auto_now_add=True)
    admin_message = models.TextField(blank=True)

    def __str__(self):
        return f'Notification for {self.user.username} at {self.notification_time}'

