from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import NotificationSettingsForm
from .models import NotificationSettings , FCMToken

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
def notification_settings_view(request):
    settings, created = NotificationSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('Notification:notification')
    else:
        form = NotificationSettingsForm(instance=settings)

    return render(request, 'notification_settings.html', {'form': form, 'message': None})

@csrf_exempt
def save_fcm_token(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        token = data.get('token')

        if request.user.is_authenticated:
            FCMToken.objects.update_or_create(
                user=request.user,
                defaults={'token': token}
            )
            return JsonResponse({'message': 'Token saved successfully!'})
        else:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

    return JsonResponse({'error': 'Invalid request method'}, status=400)