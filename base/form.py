from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from base.models import UserInfomation , PersonalInformation , PersonalHealthInformation
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForms(UserCreationForm):
    email = forms.EmailField(required=True)
    contact_number = forms.CharField(max_length=20, required=True)
    class Meta:
        model = UserInfomation
        fields = ['username', 'email', 'first_name', 'last_name', 'contact_number', 'password1', 'password2']
    
    def save(self , commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.contact_number = self.cleaned_data['contact_number']
        user.role = 'Beginner Sitter'
        if commit:
            user.save()
        return user

class UserInfomationForm(forms.ModelForm):
    class Meta:
        model = UserInfomation
        fields = ['username', 'email', 'contact_number', 'role']
        widgets = {
            'role': forms.TextInput(attrs={'readonly': 'readonly'})
        }

class PersonalInformationForm(forms.ModelForm):
    class Meta:
        model = PersonalInformation
        fields = ['goal', 'job_name', 'job_type', 'job_hours', 'break_hours']

class PersonalHealthInformationForm(forms.ModelForm):
    class Meta:
        model = PersonalHealthInformation
        fields = ['age', 'height', 'weight', 'has_pain']

class UserChangeForm(forms.ModelForm):
    class Meta:
        model = UserInfomation
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'กรอกชื่อผู้ใช้งานใหม่'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
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