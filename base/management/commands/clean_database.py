from django.core.management.base import BaseCommand
from base.models import PostureDetection, UserUsageHistory , UserInfomation

class Command(BaseCommand):
    help = 'Clear data from specific tables'

    def add_arguments(self, parser):
        parser.add_argument('--table', nargs='+', help='Specify table(s) to clear')

    def handle(self, *args, **options):
        tables = options['table']
        if 'PostureDetection' in tables:
            PostureDetection.objects.all().delete()
            self.stdout.write('PostureDetection cleared.')

        if 'UserUsageHistory' in tables:
            UserUsageHistory.objects.all().delete()
            self.stdout.write('UserUsageHistory cleared.')
        
        if 'UserInfomation' in tables:
            UserInfomation.objects.all().delete()
            self.stdout.write('UserInfomation cleared.')

        if not tables:
            self.stdout.write('No tables specified.')
