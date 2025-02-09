
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    age = models.IntegerField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    has_pain = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f'{self.user.username if self.user else "No User"} - {self.goal or "No Goal"}'

    

class PostureDetection(models.Model):
    user = models.ForeignKey(UserInfomation, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now, null=True)  # ย้าย timestamp มาที่นี่
    score = models.IntegerField()

    def __str__(self):
        return f'{self.user.username} - Posture Score: {self.score} - Timestamp: {self.timestamp}'


class UserUsageHistory(models.Model):
    posture_detection = models.ForeignKey(PostureDetection, on_delete=models.CASCADE)
    detect_type = models.CharField(
        max_length=50, 
        choices=[
            ('Photo Detection', 'Photo Detection'),
            ('Side-part Detection', 'Side-part Detection')
        ]
    )
    detection_time = models.FloatField(null=True, blank=True)  # ย้าย detection_time มาที่นี่

    def clean(self):
        # ถ้า detect_type เป็น 'Photo Detection' ต้องไม่ให้กรอกค่า detection_time
        if self.detect_type == 'Photo Detection' and self.detection_time is not None:
            raise ValidationError({'detection_time': 'Detection time must be empty for Photo Detection.'})

    def __str__(self):
        return f'{self.posture_detection.user.username} - {self.detect_type} - Detection Time: {self.detection_time}'



