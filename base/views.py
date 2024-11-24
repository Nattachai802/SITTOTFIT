from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView ,FormView
from django.contrib.auth.views import LoginView , PasswordResetView , PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect, render
from django.http import Http404
from base.models import *
from base.form import *

def classify_bmi(bmi):
    if bmi < 16:
        return "Severe Thinness"
    elif 16 <= bmi < 17:
        return "Moderate Thinness"
    elif 17 <= bmi < 18.5:
        return "Mild Thinness"
    elif 18.5 <= bmi < 25:
        return "Normal"
    elif 25 <= bmi < 30:
        return "Overweight"
    elif 30 <= bmi < 35:
        return "Obese Class I"
    elif 35 <= bmi < 40:
        return "Obese Class II"
    else:
        return "Obese Class III"



class UserRegisterview(CreateView):
    form_class = UserRegisterForms
    template_name = 'Authen/register.html'
    success_url = reverse_lazy('base:Login')

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'สมัครสมาชิกสำเร็จ! กรุณารอสักครู่...')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'เกิดข้อผิดพลาดในการลงทะเบียน กรุณาตรวจสอบข้อมูลอีกครั้ง.')
        return super().form_invalid(form)

class Userloginview(LoginView):
    template_name = 'Authen/login.html'
    
    def get_success_url(self):
        return reverse_lazy('base:home')

class HomepageView(LoginRequiredMixin,ListView):
    model = UserInfomation  # โมเดลหลักที่ใช้สำหรับ ListView
    template_name = 'account.html'
    context_object_name = 'User_items'
    def get_queryset(self):
        return UserInfomation.objects.filter(id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        personal_health = PersonalHealthInformation.objects.filter(user=user).first()
        context['Personal_items'] = PersonalInformation.objects.filter(user=user)
        context['Health_items'] = PersonalHealthInformation.objects.filter(user=user)

        if personal_health and personal_health.height and personal_health.weight:
            height_m = personal_health.height/100
            bmi = round(personal_health.weight / (height_m ** 2), 2)
            context['bmi'] = bmi
            context['bmi_category'] = classify_bmi(bmi)
        else:
            context['bmi'] = None
            context['bmi_category'] = "Not Available"

        return context

class ResetPasswordview(SuccessMessageMixin,PasswordResetView):
    template_name = r'Authen/password_reset.html'
    email_template_name = r'Authen/password_reset_email.html'
    subject_template_name = r'Authen/password_reset_subject.txt'
    success_message = 'เราได้ส่งลิงค์ในการ reset รหัสผ่านไปทางอีเมลที่คุณแจ้งแล้ว โปรดตรวจสอบที่emailของคุณ'
    success_url = reverse_lazy('base:Login')
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return self.render_to_response(self.get_context_data(form=form))

class PersonalInformationUpdateView(LoginRequiredMixin, UpdateView):
    model = PersonalInformation
    fields = ['goal', 'job_name', 'job_type', 'job_hours', 'break_hours']
    template_name = 'update_user_data.html'  # ใช้ Template เดียวกัน
    success_url = reverse_lazy('base:home')

    def get_object(self, queryset=None):
        obj, created = PersonalInformation.objects.get_or_create(user=self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_type'] = 'personal_information'  # ระบุประเภทฟอร์ม
        return context


class PersonalHealthInformationUpdateView(LoginRequiredMixin, UpdateView):
    model = PersonalHealthInformation
    fields = ['age', 'height', 'weight', 'has_pain']
    template_name = 'update_user_data.html'  # ใช้ Template เดียวกัน
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        obj, created = PersonalHealthInformation.objects.get_or_create(user=self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_type'] = 'personal_health_information'  # ระบุประเภทฟอร์ม
        return context

class ChangeUsernameView(LoginRequiredMixin,SuccessMessageMixin,UpdateView):
    model = UserInfomation
    form_class = UserChangeForm
    template_name = r'change/change_username.html'
    success_url = reverse_lazy('base:home')
    success_message = 'เปลี่ยนชื่อให้แล้วนะจั๊บจุ้บุจุ้บุ'

    def get_object(self):
        return self.request.user

class ChangePasswordView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = r'change/change_password.html'
    success_url = reverse_lazy('profile')
    success_message = "Password ถูกเปลี่ยนเรียบร้อยแล้ว!"

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, self.object)
        return response