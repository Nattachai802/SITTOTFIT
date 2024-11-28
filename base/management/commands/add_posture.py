from django.core.management.base import BaseCommand
from base.models import UserInfomation, PostureDetection , UserUsageHistory
from faker import Faker
import random
from datetime import datetime

fake = Faker()

class Command(BaseCommand):
    help = 'Add PostureDetection data for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to add PostureDetection data for')
        parser.add_argument('count', type=int, help='Number of PostureDetection records to add')
        parser.add_argument('--timestamp', type=str, help='Timestamp for the records (format: YYYY-MM-DD HH:MM:SS)')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        count = kwargs['count']
        timestamp_str = kwargs.get('timestamp')

        try:
            user = UserInfomation.objects.get(username=username)
        except UserInfomation.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with username "{username}" does not exist'))
            return

        if timestamp_str:
            try:
                custom_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                self.stdout.write(self.style.ERROR(f'Invalid timestamp format. Use "YYYY-MM-DD HH:MM:SS".'))
                return
        else:
            custom_timestamp = None  # Use auto-generated timestamps if not provided

        # Create PostureDetection records
        for _ in range(count):
            PostureDetection.objects.create(
                user=user,
                detection_time=fake.time_delta(),
                score=random.randint(50, 100),
                timestamp=custom_timestamp or fake.date_time_this_year(),  # Use custom or random timestamp
            )

        self.stdout.write(self.style.SUCCESS(f'{count} PostureDetection records added for user "{username}"'))