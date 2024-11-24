from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

from django.urls import path , include
from base.views import *
app_name = 'base'
urlpatterns = [
    path('', HomepageView.as_view() , name='home' ),
    
    path('signup/', UserRegisterview.as_view(), name='Register'),
    path('login/', Userloginview.as_view() , name='Login'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('base:Login')), name='logout'),

    path('password-reset/', ResetPasswordview.as_view(), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html',
                                                     success_url=reverse_lazy('base:password_reset_complete')),
         name='password_reset_confirm'),
    
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),
     
    path('update-personal-information/', PersonalInformationUpdateView.as_view(), name='update_personal_information'),
    path('update-personal-health/', PersonalHealthInformationUpdateView.as_view(), name='update_personal_health'),

    path('change_username/',ChangeUsernameView.as_view(), name='change_name'),
    path('change_password/', ChangePasswordView.as_view(), name='change_pass'),


]