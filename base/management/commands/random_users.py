from django.core.management.base import BaseCommand
from base.models import UserInfomation, PersonalInformation, PersonalHealthInformation, UserUsageHistory, PostureDetection, NotificationLog
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Generate sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument('users', type=int, help='Number of users to create')

    def handle(self, *args, **kwargs):
        users_count = kwargs['users']

        for _ in range(users_count):
            # สร้าง UserInfomation
            user = UserInfomation.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password123',
                contact_number=fake.phone_number(),
                role='Beginner Sitter',
            )
            self.stdout.write(f'User {user.username} created')

            # สร้าง PersonalInformation
            PersonalInformation.objects.create(
                user=user,
                goal=random.choice(['Improve posture', 'Health maintenance', 'Posture correction']),
                job_name=fake.job(),
                job_type=fake.job(),
                job_hours=random.uniform(4, 10),
                break_hours=random.uniform(0.5, 2),
            )
            self.stdout.write(f'PersonalInformation for {user.username} created')

            # สร้าง PersonalHealthInformation
            PersonalHealthInformation.objects.create(
                user=user,
                age=random.randint(18, 65),
                height=random.uniform(150, 200),
                weight=random.uniform(50, 100),
                has_pain=random.choice([True, False]),
            )
            self.stdout.write(f'PersonalHealthInformation for {user.username} created')

            UserUsageHistory.objects.create(
                user=user,
                detect_type=random.choice(['Simple Detection', 'Advanced Detection']),
                usage_count=random.randint(1, 10),
            )

            PostureDetection.objects.create(
                user=user,
                detection_time=fake.time_delta(),
                score=random.randint(50, 100),
            )

            NotificationLog.objects.create(
                user=user,
                message=fake.sentence(),
                admin_message=fake.sentence(),
            )

        self.stdout.write('Sample data generated successfully.')