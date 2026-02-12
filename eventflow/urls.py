from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mylogin.urls')),
    path('accounts/', include('allauth.urls')),
    path('social-login/callback/', TemplateView.as_view(template_name='callback.html'), name='social_login_callback'),
]
