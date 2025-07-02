from django.urls import path
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from .views import profile, register, login_view, logout_view

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-change/', PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url='/users/password-change-done/'
    ), name='password_change'),
    path('password-change-done/', PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),
]
