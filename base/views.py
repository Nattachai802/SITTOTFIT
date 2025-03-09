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
from django.core.mail import send_mail
from django.shortcuts import render
from django.http import HttpResponse

#สร้างคลาสสำหรับการแปลงค่า BMI ให้เป็นหมวดหมู่
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


#สร้างคลาสสำหรับการแสดงหน้าสมัครสมาชิก โดยสืบทอดคุณสมบัติจาก Createview
class UserRegisterview(CreateView):
    form_class = UserRegisterForms #เรียกใช้ฟอร์มสำหรับการสมัครสมาชิก
    template_name = 'Authen/register.html' #เรียกใช้ Template สำหรับการสมัครสมาชิก
    success_url = reverse_lazy('base:Register') #เมื่อสมัครสมาชิกสำเร็จจะเปลี่ยนไปหน้า Login

    #ฟังก์ชั่นสำหรับการตรวจสอบข้อมูลที่กรอกเข้ามา ในกรณีที่ถูกต้องจะส่งข้อมูลไปยังฐานข้อมูล
    def form_valid(self, form): 
        user = form.save() #บันทึกข้อมูลลงฐานข้อมูล
        messages.success(self.request, 'สมัครสมาชิกสำเร็จ! กรุณารอสักครู่...')
        return super().form_valid(form)
    
    #ฟังก์ชั่นสำหรับการตรวจสอบข้อมูลที่กรอกเข้ามา ในกรณีที่ไม่ถูกต้องจะแสดงชื่อข้อผิดพลาด
    def form_invalid(self, form):
        messages.error(self.request, 'เกิดข้อผิดพลาดในการลงทะเบียน กรุณาตรวจสอบข้อมูลอีกครั้ง.')
        return super().form_invalid(form)

#สร้างคลาสสำหรับการแสดงหน้า Login โดยสืบทอดคุณสมบัติจาก LoginView
class Userloginview(LoginView):
    template_name = 'Authen/login.html' #เรียกใช้ Template สำหรับการ Login
    
    def get_success_url(self):
        return reverse_lazy('base:home') #เมื่อ Login สำเร็จจะเปลี่ยนไปหน้า Home

#สร้างคลาสสำหรับการแสดงหน้า Home โดยสืบทอดคุณสมบัติจาก ListView
class HomepageView(LoginRequiredMixin, ListView):
    model = UserInfomation  # โมเดลหลักที่ใช้สำหรับ ListView
    template_name = 'account.html' #เรียกใช้ Template สำหรับการแสดงหน้า Home
    context_object_name = 'User_items' #ตั้งชื่อตัวแปรที่ใช้เก็บข้อมูลที่ดึงมาจากฐานข้อมูล
    
    def get_queryset(self): #ฟังก์ชั่นสำหรับการดึงข้อมูลจากฐานข้อมูล

        return UserInfomation.objects.filter(id=self.request.user.id) #ดีงข้อมูลของuserนั้นๆ

    def get_context_data(self, **kwargs): #ฟังก์ชั่นสำหรับการส่งข้อมูลไปยัง Template
        context = super().get_context_data(**kwargs) #ดึงข้อมูลที่ส่งมาจากฟังก์ชั่นเดิม
        user = self.request.user #ดึงข้อมูลของuserที่ Login อยู่
        personal_info = PersonalInformation.objects.filter(user=user).first()
        context['Personal_items'] = PersonalInformation.objects.filter(user=user) #ส่งข้อมูลของuserที่ Login อยู่ไปยัง Template

        #ตรวจสอบว่าข้อมูลส่วนสูงกับน้ำหนักไหม หากมีจะคำนวณค่า BMI และหมวดหมู่ของ BMI
        if personal_info and personal_info.height and personal_info.weight:
            height_m = personal_info.height / 100
            bmi = round(personal_info.weight / (height_m ** 2), 2)
            context['bmi'] = bmi
            context['bmi_category'] = classify_bmi(bmi)
        else:
            context['bmi'] = None
            context['bmi_category'] = "Not Available"
        

        return context #ส่งข้อมูลไปยัง Template

#สร้างคลาสสำหรับการแสดงหน้า เปลี่ยนรหัสผ่าน โดยสืบทอดคุณสมบัติจาก PasswordResetView
class ResetPasswordview(SuccessMessageMixin, PasswordResetView):
    template_name = 'Authen/password_reset.html'
    email_template_name = 'Authen/password_reset_email.html'
    subject_template_name = 'Authen/password_reset_subject.txt'
    success_message = 'เราได้ส่งลิงค์ในการ reset รหัสผ่านไปทางอีเมลที่คุณแจ้งแล้ว โปรดตรวจสอบที่ email ของคุณ'
    success_url = reverse_lazy('base:password_reset')

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)#ส่งข้อมูลไปยัง Template

#สร้างคลาสสำหรับการแสดงหน้า ข้อมูลส่วนตัว โดยสืบทอดคุณสมบัติจาก UpdateView
class PersonalInformationUpdateView(LoginRequiredMixin, UpdateView):
    model = PersonalInformation # โมเดลหลักที่ใช้สำหรับ UpdateView
    fields = ['goal', 'job_name', 'job_type', 'job_hours', 'break_hours', 'age', 'height', 'weight', 'has_pain']
    template_name = 'update_user_data.html'
    success_url = reverse_lazy('base:home') 

    def get_object(self, queryset=None): #ฟังก์ชั่นสำหรับการดึงข้อมูลจากฐานข้อมูล
        obj, created = PersonalInformation.objects.get_or_create(user=self.request.user) #ดึงข้อมูลของuserนั้นๆ หากหาไม่เจอจะสร้างข้อมูลใหม่
        return obj #ส่งข้อมูลไปยัง Template

    def get_context_data(self, **kwargs): #ฟังก์ชั่นสำหรับการส่งข้อมูลไปยัง Template
        context = super().get_context_data(**kwargs) #ดึงข้อมูลที่ส่งมาจากฟังก์ชั่นเดิม
        context['form_type'] = 'personal_information'  # ระบุประเภทฟอร์ม
        return context #ส่งข้อมูลไปยัง Template

#สร้างคลาสสำหรับการเปลี่ยนชื่อผู้ใช้งาน โดยสืบทอดคุณสมบัติจาก UpdateView
class ChangeUsernameView(LoginRequiredMixin,SuccessMessageMixin,UpdateView):
    model = UserInfomation # โมเดลหลักที่ใช้สำหรับ UpdateView
    form_class = UserChangeForm #เรียกใช้ฟอร์มสำหรับการเปลี่ยนชื่อ
    template_name = r'change/change_username.html'
    success_url = reverse_lazy('base:change_name') #เมื่อเปลี่ยนชื่อสำเร็จจะเปลี่ยนไปหน้า Home
    success_message = '๊Username changed successfully!' #ข้อความที่แสดงเมื่อเปลี่ยนชื่อสำเร็จ

    def get_object(self): #ฟังก์ชั่นสำหรับการดึงข้อมูลจากฐานข้อมูล
        return self.request.user #ดึงข้อมูลของuserนั้นๆ

#สร้างคลาสสำหรับการเปลี่ยนรหัสผ่าน โดยสืบทอดคุณสมบัติจาก PasswordChangeView
class ChangePasswordView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm #เรียกใช้ฟอร์มสำหรับการเปลี่ยนรหัสผ่าน
    template_name = r'change/change_password.html'
    success_url = reverse_lazy('base:change_pass') #เมื่อเปลี่ยนรหัสผ่านสำเร็จจะเปลี่ยนไปหน้า Profile
    success_message = "Password ถูกเปลี่ยนเรียบร้อยแล้ว!"

    def form_valid(self, form): 
        response = super().form_valid(form)
        update_session_auth_hash(self.request, self.object) # อัพเดต session ของผู้ใช้หลังจากเปลี่ยนรหัสผ่าน โดยไม่ต้องให้ผู้ใช้ logout แล้ว login ใหม่
        return response #ส่งข้อมูลไปยัง Template

#สร้างฟังก์ชั่นสำหรับระบบติดต่อผู้พัฒนาระบบ โดยรับ request จากผู้ใช้งาน
def contact_view(request):
    if request.method == 'POST': #ตรวจสอบว่าเป็นการส่งข้อมูลหรือไม่ ด้วยเมธอด POST หรือไม่
        form = ContactForm(request.POST) #สร้างฟอร์มสำหรับการติดต่อ
        if form.is_valid(): #ตรวจสอบข้อมูลที่กรอกเข้ามาว่าถูกต้องหรือไม่
            name = form.cleaned_data['name'] #ดึงค่าข้อมูลที่ผ่านการตรวจสอบจากฟอร์มมาใช้งาน 
            email = form.cleaned_data['email'] #ดึงค่าข้อมูลที่ผ่านการตรวจสอบจากฟอร์มมาใช้งาน 
            message = form.cleaned_data['message'] #ดึงค่าข้อมูลที่ผ่านการตรวจสอบจากฟอร์มมาใช้งาน 
            full_message = f"Message from {name} ({email}):\n\n{message}"

            # ส่งอีเมล
            send_mail(
                'Contact from User',
                full_message,
                email,
                ['sittofit.noreply@gmail.com'],
            )
            return render(request, 'contact.html', {'form': form, 'success': True})
    else:
        form = ContactForm() #สร้างฟอร์มสำหรับการติดต่อ

    return render(request, 'contact.html', {'form': form, 'success': False}) #ส่งข้อมูลไปยัง Template

#สร้างคลาสสำหรับการแสดงหน้า วิธีการใช้งาน โดยสืบทอดคุณสมบัติจาก TemplateView
class InstructionsView(TemplateView):
    template_name = 'Howto.html'