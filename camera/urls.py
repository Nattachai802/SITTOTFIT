from django.urls import path
from . import views
app_name = 'camera'
urlpatterns = [
    path('Detection/', views.CameraDetectionView.as_view(), name='camera_detection'),
    path('process_image/', views.process_image, name='process_image'),
    path('DetectHub/' , views.Selection_hubView.as_view(), name='DetectHub')
]
