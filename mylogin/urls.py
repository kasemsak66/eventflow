from django.urls import path
from mylogin.forms import CustomPasswordChangeView
from .views import home, login, logout, register
from mylogin import views
from django.conf import settings
from django.conf.urls.static import static
from .views import BookingCreateView, BookingListView, BookingDeleteView , VenueMapView



urlpatterns = [
    path('register/', register, name='register'),
    path('login/',    login,    name='login'),
    path('logout',   logout, name='logout'),

    path('',home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', CustomPasswordChangeView.as_view(), name='change_password'),

    path('venues/', views.VenueListView.as_view(), name='venue_list'),
    path('venues/create/', views.VenueCreateView.as_view(), name='venue_create'),
    path('venues/<int:pk>/', views.VenueDetailView.as_view(), name='venue_detail'),
    path('venues/<int:pk>/edit/', views.VenueUpdateView.as_view(), name='venue_update'),
    path('venues/<int:pk>/delete/', views.VenueDeleteView.as_view(), name='venue_delete'),
    path('venues/my/', views.MyVenueListView.as_view(), name='my_venues'),
    path("venues/map/", VenueMapView.as_view(), name="venue_map"),
    

    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('bookings/create/', BookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/delete/', BookingDeleteView.as_view(), name='booking_delete'),

    path('bookings/<int:pk>/approve-initial/', views.booking_approve_initial, name='booking_approve_initial'),
    path('bookings/<int:pk>/upload-slip/',     views.booking_upload_slip,    name='booking_upload_slip'),
    path('bookings/<int:pk>/confirm-payment/', views.booking_confirm_payment, name='booking_confirm_payment'),
    path('bookings/<int:pk>/reject/',          views.booking_reject,         name='booking_reject'),
    path('bookings/<int:pk>/cancel/',          views.booking_cancel,         name='booking_cancel'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)