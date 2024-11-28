from django.shortcuts import render
from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.db.models.functions import ExtractWeekDay
from django.db.models import Avg

from base.models import *
from django.views.generic import TemplateView, View
from django.db.models.functions import TruncHour, TruncMinute
from django.db.models import Count
from collections import defaultdict
from datetime import date , timedelta , datetime
from django.utils.timezone import now, localdate
# Create your views here.

GOAL_DESCRIPTIONS = {
    'Improve posture': 'พัฒนาบุคลิกการนั่งให้ดูเหมาะสม และ ดีต่อสุขภาพ',
    'Health maintenance': 'เพื่อสุขภาพที่ยั่งยืน อาการปวดหลังลดน้อยลง',
    'Posture correction': 'เพื่อนั่งให้ได้อย่างถูกต้อง',
}

class DashboardHomeView(TemplateView):
    template_name = 'Dashboard.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        user_info = UserInfomation.objects.filter(username =user.username).first()
        usage_history = UserUsageHistory.objects.filter(posture_detection__user=user_info )
        posture_data = PostureDetection.objects.filter(user=user_info )
        Notification = NotificationLog.objects.filter(user=user_info )
        personal_info = PersonalInformation.objects.filter(user=user_info ).first()

        usage_count = posture_data.count()
        
        Rank = user_info.role if user_info else "ไม่มีข้อมูล Role"


        context['usage_history'] = usage_history
        context['posture_data'] = posture_data
        context['notification_logs'] = Notification

        # Calculate daily scores
        daily_scores = defaultdict(list)
        for entry in posture_data:
            day = entry.timestamp.date()
            daily_scores[day].append(entry.score)
        
        today = localdate()  # วันที่ปัจจุบันใน timezone ของเซิร์ฟเวอร์
        
        start_of_day = make_aware(datetime.combine(today, datetime.min.time()))
        end_of_day = make_aware(datetime.combine(today, datetime.max.time()))

        scores_today = PostureDetection.objects.filter(timestamp__range=(start_of_day, end_of_day))

        # คำนวณช่วงเวลาที่ใช้งานบ่อยที่สุดสำหรับวันนี้
        peak_time = (
            scores_today.annotate(hour=TruncHour('timestamp'))  # ตัดช่วงเวลาเป็นรายชั่วโมง
            .values('hour')  # รวมกลุ่มตามชั่วโมง
            .annotate(count=Count('id'))  # นับจำนวน
            .order_by('-count')  # เรียงลำดับจากมากไปน้อย
        )

        if peak_time.exists():
            peak_hour = peak_time[0]['hour']
            peak_hour_count = peak_time[0]['count']
        else:
            peak_hour = None
            peak_hour_count = 0

        # Calculate today's average score
        today = date.today()
        scores_today = daily_scores.get(today, [])
        avg_score_today = sum(scores_today) / len(scores_today) if scores_today else 0

        
        goal = personal_info.goal if personal_info else "ผู้ใช้งานยังไม่ได้เลือกเป้าหมาย"
        
        tooltip_text = GOAL_DESCRIPTIONS.get(goal, "ผู้ใช้งานยังไม่ได้เลือกเป้าหมาย")

        

        context = {
        'goal': goal,
        'tooltip_text': tooltip_text,
            }
        
        
        yesterday = date.today() - timedelta(days=1)

        # Filter records for yesterday
        yesterday_usage = PostureDetection.objects.filter(
            timestamp__date=yesterday,
            user=user
        )

        # Group scores by day
        daily_scores = defaultdict(list)
        for entry in yesterday_usage:
            day = entry.timestamp.date()
            daily_scores[day].append(entry.score)

        # Calculate yesterday's average score
        scores_yesterday = daily_scores.get(yesterday, [])
        avg_score_yesterday = (
            sum(scores_yesterday) / len(scores_yesterday)
            if scores_yesterday
            else 0
        )
        print(avg_score_yesterday)

        
        context['usage_count'] = usage_count
        context['yesterday_score'] = avg_score_yesterday
        context['max_yesterday'] = max(scores_yesterday)
        context['min_yesterday'] = min(scores_yesterday)
        context['Rank'] = Rank
        context['avg_score'] = avg_score_today
        context['today_count'] = len(scores_today)
        context['peak_hour'] = peak_hour
        context['peak_count'] = peak_hour_count
        context['max_score'] = max(scores_today)
        context['min_score'] = min(scores_today)


        return context

class DashboradDataView(View):
    def get(self, request, *args, **kwargs):
        user = request.user

        posture_data = PostureDetection.objects.filter(user=user)

        # Calculate daily scores
        daily_scores = defaultdict(list)
        for entry in posture_data:
            day = entry.timestamp.date()
            daily_scores[day].append(entry.score)

        # Calculate today's average score
        today = date.today()
        scores_today = daily_scores.get(today, [])
        avg_score_today = sum(scores_today) / len(scores_today) if scores_today else 0

        # Prepare JSON response
        data = {
            'categories': ['Score', 'Remaining'],
            'values': [avg_score_today, 100 - avg_score_today],
        }
        return JsonResponse(data)


class UsageHistoryDataView(View):

    def get(self, request, *args, **kwargs):
        usage_data = UserUsageHistory.objects.all().values('time_stamp', 'usage_count')
        return JsonResponse(list(usage_data), safe=False)

class YesterdayDataView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Calculate yesterday's date
        yesterday = date.today() - timedelta(days=1)

        # Filter records for yesterday
        yesterday_usage = PostureDetection.objects.filter(
            timestamp__date=yesterday,
            user=user
        )

        # Group scores by day
        daily_scores = defaultdict(list)
        for entry in yesterday_usage:
            day = entry.timestamp.date()
            daily_scores[day].append(entry.score)

        # Calculate yesterday's average score
        scores_yesterday = daily_scores.get(yesterday, [])
        avg_score_yesterday = (
            sum(scores_yesterday) / len(scores_yesterday)
            if scores_yesterday
            else 0
        )

        data = {
            'categories': ['Score', 'Remaining'],
            'values': [avg_score_yesterday, 100 - avg_score_yesterday],
        }

        return JsonResponse(data)

class WeeklyUsageStatsView(View):
    def get(self, request, *args, **kwargs):
        user = request.user

        start_of_week = date.today() - timedelta(days=date.today().weekday())        
        end_of_week = start_of_week + timedelta(days=6)

        weekly_usage = UserUsageHistory.objects.filter(
            timestamp__date__gte=start_of_week,
            timestamp__date__lte=end_of_week,
            posture_detection__user=user
        ).annotate(weekday=ExtractWeekDay('timestamp')).values('weekday').annotate(count=Count('id'))
        
        weekday_map = {
            2: 'จันทร์', 3: 'อังคาร', 4: 'พุธ', 5: 'พฤหัสบดี', 6: 'ศุกร์', 7: 'เสาร์', 1: 'อาทิตย์'
        }
        usage_data = {weekday_map[i]: 0 for i in range(1, 8)}  # เริ่มจากค่าเริ่มต้น 0
        
        for item in weekly_usage:
            usage_data[weekday_map[item['weekday']]] = item['count']

        return JsonResponse({'usage_data': usage_data})

class PostureDetectionDataView(View):

    def get(self, request, *args, **kwargs):
        posture_data = PostureDetection.objects.all().values('time_stamp', 'score')
        return JsonResponse(list(posture_data), safe=False)


class NotificationLogDataView(View):

    def get(self, request, *args, **kwargs):
        notification_data = NotificationLog.objects.all().values('notification_time', 'message')
        return JsonResponse(list(notification_data), safe=False)

class WeeklyAverageScoresView(View):
    def get(self, request, *args, **kwargs):
        user = request.user

        # คำนวณช่วงเวลาในสัปดาห์นี้
        start_of_week = date.today() - timedelta(days=date.today().weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # ดึงข้อมูลการใช้งานในสัปดาห์นี้
        weekly_scores = PostureDetection.objects.filter(
            timestamp__date__gte=start_of_week,
            timestamp__date__lte=end_of_week,
            user=user
        ).annotate(weekday=ExtractWeekDay('timestamp')).values('weekday').annotate(avg_score=Avg('score'))

        weekday_map = {1: 'SUN', 2: 'MON', 3: 'TUE', 4: 'WED', 5: 'THU', 6: 'FRI', 7: 'SAT'}
        usage_data = {weekday_map[i]: 0 for i in range(1, 8)}  # เริ่มต้นข้อมูลทุกวันด้วย 0
        for item in weekly_scores:
            usage_data[weekday_map[item['weekday']]] = round(item['avg_score'], 2)  # เก็บค่าเฉลี่ยโดยปัดทศนิยม 2 ตำแหน่ง
        

        return JsonResponse({'usage_data': usage_data})

class TodayUsageHistoryView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # ดึงข้อมูลของวันนี้
        today = date.today()
        today_data = PostureDetection.objects.filter(
            timestamp__date=today,
            user=user
        ).values('timestamp', 'detection_time', 'score')

        # แปลงข้อมูลให้อยู่ในรูปแบบ JSON
        history_data = [
            {
                "time": item['timestamp'].strftime('%H:%M'),
                "duration": str(item['detection_time']),
                "score": item['score']
            }
            for item in today_data
        ]

        return JsonResponse({'history': history_data})