from django.urls import path
from mylogin.forms import CustomPasswordChangeView
from .views import VenueListView, home, login, logout, register
from mylogin import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('register/', register, name='register'),
    path('login/',    login,    name='login'),
    path('logout',   logout, name='logout'),

    path('',     home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', CustomPasswordChangeView.as_view(), name='change_password'),

    path('venues/', views.VenueListView.as_view(), name='venue_list'),
    path('venues/create/', views.VenueCreateView.as_view(), name='venue_create'),
    path('venues/<int:pk>/', views.VenueDetailView.as_view(), name='venue_detail'),
    path('venues/<int:pk>/edit/', views.VenueUpdateView.as_view(), name='venue_update'),
    path('venues/<int:pk>/delete/', views.VenueDeleteView.as_view(), name='venue_delete'),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)