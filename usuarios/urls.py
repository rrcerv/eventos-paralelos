from django.contrib.auth.views import LoginView
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

from .forms import LoginForm

app_name = 'usuarios'

urlpatterns = [
    path('login/', LoginView.as_view(template_name='login.html', form_class=LoginForm), name='login'),
    path('logout/', views.logout_admin, name='logout'),
    path('teste', views.teste, name='teste')
]