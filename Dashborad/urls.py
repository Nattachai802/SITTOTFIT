from django.contrib import admin

from django.urls import path , include
from .views import *
app_name = 'Dashboard'
urlpatterns = [
    path('Dashboard/', DashboardHomeView.as_view(), name='dashboard_home'),
    path('dashboard/data/', DashboradDataView.as_view(), name='dashboard-data'),
    path('dashboard/weekly-usage-stats/' , WeeklyUsageStatsView.as_view() ,name='weekly_status'),
    path('dashboard/yesterday-usage-stats/', YesterdayDataView.as_view(),name='Yesterday_status'),
    path('dashboard/weekly-average-scores/', WeeklyAverageScoresView.as_view(),name='Yesterday_status'),
    path('dashboard/today-usage-history/', TodayUsageHistoryView.as_view(),name='Yesterday_status'),
    path('dashboard/heatmap-data/', HeatmapDataView.as_view(), name='heatmap_data'),
    path('detailed-usage-data/', DetailedUsageDataView.as_view(), name='detailed-usage-data'),
]