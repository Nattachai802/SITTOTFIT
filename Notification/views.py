from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import NotificationSettingsForm
from .models import NotificationSettings , FCMToken
from django.contrib import messages

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
            messages.success(request, "การตั้งค่าการแจ้งเตือนถูกบันทึกเรียบร้อยแล้ว!")
            return redirect('Notification:notification')
        else:
            messages.error(request, "เกิดข้อผิดพลาด! กรุณาตรวจสอบข้อมูลที่กรอกและลองใหม่อีกครั้ง.")
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


import os
import pdfkit
from django.http import HttpResponse
from django.conf import settings

# กำหนด path ของ wkhtmltopdf (Windows ใช้ path นี้, Linux/Mac อาจไม่ต้อง)
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe\bin\wkhtmltopdf.exe")

def app_to_pdf(request, app_name):
    app_path = os.path.join(settings.BASE_DIR, app_name)
    pdf_filename = f"{app_name}.pdf"

    if not os.path.exists(app_path):
        return HttpResponse("App not found", status=404)

    html_content = f"<h1>Source Code of App: {app_name}</h1>"

    for root, dirs, files in os.walk(app_path):
        for file in files:
            if file.endswith((".py", ".html", ".css", ".js")):  # แปลงเฉพาะไฟล์ที่ต้องการ
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:  # ✅ อ่านไฟล์เป็น UTF-8
                    html_content += f"<h2>{file}</h2><pre>{f.read()}</pre>"

    # ✅ ใช้ pdfkit พร้อมกำหนดให้ใช้ encoding UTF-8
    options = {'encoding': 'UTF-8'}
    pdfkit.from_string(html_content, pdf_filename, configuration=PDFKIT_CONFIG, options=options)

    with open(pdf_filename, "rb") as pdf:
        response = HttpResponse(pdf.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{pdf_filename}"'
        return response
