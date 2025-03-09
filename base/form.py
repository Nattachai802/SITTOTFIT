from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from base.models import UserInfomation , PersonalInformation
from django.contrib.auth.forms import UserCreationForm

#สร้างฟอร์มสำหรับการสมัครสมาชิก
class UserRegisterForms(UserCreationForm):
    email = forms.EmailField(required=True) #สร้างฟิลด์สำหรับกรอกอีเมล
    contact_number = forms.CharField(max_length=20, required=True) #สร้างฟิลด์สำหรับกรอกเบอร์โทรศัพท์
    class Meta: #สร้างคลาส Meta สำหรับการกำหนดโมเดลที่จะใช้ และฟิลด์ที่จะใช้
        model = UserInfomation
        fields = ['username', 'email', 'first_name', 'last_name', 'contact_number', 'password1', 'password2']
    
    def save(self , commit=True): #สร้างฟังก์ชั่นสำหรับการบันทึกข้อมูล
        user = super().save(commit=False) #ดึงข้อมูลจากฟอร์มมาใช้งาน
        user.email = self.cleaned_data['email']
        user.contact_number = self.cleaned_data['contact_number']
        user.role = 'Beginner Sitter'
        if commit:
            user.save()
        return user

class UserInfomationForm(forms.ModelForm): #สร้างฟอร์มสำหรับการแสดงข้อมูลผู้ใช้งาน
    class Meta:
        model = UserInfomation
        fields = ['username', 'email', 'contact_number', 'role']
        widgets = {
            'role': forms.TextInput(attrs={'readonly': 'readonly'}) #กำหนดให้ฟิลด์ role ไม่สามารถแก้ไขได้
        }

class PersonalInformationForm(forms.ModelForm): #สร้างฟอร์มสำหรับการแสดงข้อมูลส่วนตัว
    class Meta:
        model = PersonalInformation
        fields = ['goal', 'job_name', 'job_type', 'job_hours', 'break_hours','age', 'height', 'weight', 'has_pain']

        

class UserChangeForm(forms.ModelForm): #สร้างฟอร์มสำหรับการเปลี่ยนชื่อผู้ใช้งาน
    class Meta:
        model = UserInfomation
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'กรอกชื่อผู้ใช้งานใหม่'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm): #สร้างฟอร์มสำหรับการเปลี่ยนรหัสผ่าน
    old_password = forms.CharField(
        label="รหัสผ่านเดิม",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label="รหัสผ่านใหม่",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="ยืนยันรหัสผ่านใหม่",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class ContactForm(forms.Form): #สร้างฟอร์มสำหรับการติดต่อผู้พัฒนาระบบ
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
