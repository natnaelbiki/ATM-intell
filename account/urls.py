# urls.py
from django.urls import path
from .views import RegisterView
from django.contrib.auth import views as auth_views

urlpatterns = [

    # Registe
    path('register/', RegisterView.as_view(), name='register'),

    # Login view
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Logout view
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    
    # Password Change view
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), name='password_change'),
    
    # Password Change Done view
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
]
