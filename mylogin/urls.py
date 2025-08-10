from django.urls import path
from mylogin.forms import CustomPasswordChangeView
from .views import home, login, logout, register
from mylogin import views

urlpatterns = [
    path('register/', register, name='register'),
    path('login/',    login,    name='login'),
    path('logout',   logout, name='logout'),
    path('home/',     home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
]