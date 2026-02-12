from django.urls import path
from mylogin import views
from django.conf import settings
from django.conf.urls.static import static

from mylogin.views.activity_views import OwnerActivityAnalyticsView
from mylogin.views.admin_views import AdminActivityDeleteView, AdminActivityListView, AdminActivityUpdateView, AdminDashboardView, AdminUserDeleteView, AdminUserListView, AdminUserUpdateView, AdminVenueDeleteView, AdminVenueListView, AdminVenueUpdateView
from mylogin.views.auth_views import PasswordChange
from mylogin.views.landing_views import LandingView
from mylogin.views.venue_views import OwnerVenueAnalyticsView
from .views import FavoriteListView, FavoriteToggleView
from .views import BookingCreateView, BookingListView, BookingDeleteView
from .views import ActivityListView, ActivityCreateView, ActivityDetailView, ActivityUpdateView, ActivityDeleteView
from .views import ReviewCreateView, ReviewUpdateView, ReviewDeleteView
from .views import  VenueMapView

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/',    views.login,    name='login'),
    path('logout',  views.logout, name='logout'),

    path("", LandingView.as_view(), name="landing"),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', PasswordChange.as_view(), name='change_password'),

    path('venues/', views.VenueListView.as_view(), name='venue_list'),
    path('venues/create/', views.VenueCreateView.as_view(), name='venue_create'),
    path('venues/<int:pk>/', views.VenueDetailView.as_view(), name='venue_detail'),
    path('venues/<int:pk>/edit/', views.VenueUpdateView.as_view(), name='venue_update'),
    path('venues/<int:pk>/delete/', views.VenueDeleteView.as_view(), name='venue_delete'),
    path('venues/my/', views.MyVenueListView.as_view(), name='my_venues'),
    path("venues/map/", VenueMapView.as_view(),name="venue_map"),
    path('venues/<int:venue_id>/favorite/',FavoriteToggleView.as_view(),name='venue_favorite_toggle'),
    
    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('bookings/create/', BookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/approve-initial/',views.booking_approve_initial,name='booking_approve_initial'),
    path('bookings/<int:pk>/upload-slip/',views.booking_upload_slip,name='booking_upload_slip'),
    path('bookings/<int:pk>/confirm-payment/',views.booking_confirm_payment,name='booking_confirm_payment'),
    path('bookings/<int:pk>/reject/',views.booking_reject,name='booking_reject'),
    path('bookings/<int:pk>/cancel/',views.booking_cancel,name='booking_cancel'),
    
    path('activities/', ActivityListView.as_view(), name='activity_list'),
    path('activities/create/', ActivityCreateView.as_view(), name='activity_create'),
    path('activities/<int:pk>/', ActivityDetailView.as_view(), name='activity_detail'),
    path('activities/<int:pk>/update/', ActivityUpdateView.as_view(), name='activity_update'),
    path('activities/<int:pk>/delete/', ActivityDeleteView.as_view(), name='activity_delete'),
    path('activities/<int:pk>/join-toggle/', views.activity_join_toggle, name='activity_join_toggle'),
    path('activities/<int:pk>/qr/', views.activity_qr, name='activity_qr'),
    path('activities/<int:pk>/qr-image/', views.activity_qr_image, name='activity_qr_image'),
    path('activities/<int:pk>/register/', views.activity_register, name='activity_register'),
    path("owner/analytics/activities/", OwnerActivityAnalyticsView.as_view(), name="owner_activity_analytics"),
    
    path('venues/<int:venue_id>/chat/',views.start_venue_chat,name='venue_chat_start'),
    path('chat/thread/<int:pk>/',views.chat_thread_view,name='chat_thread_view'),
    path('chat/history/',views.chat_history,name='chat_history'),
    
    path('venues/<int:venue_id>/reviews/create/',ReviewCreateView.as_view(),name='review_create'),
    path('reviews/<int:pk>/edit/',ReviewUpdateView.as_view(),name='review_update'),
    path('reviews/<int:pk>/delete/',ReviewDeleteView.as_view(),name='review_delete'),
    
    path('favorites/',FavoriteListView.as_view(),name='favorite_list'),
    
    path("owner/venue-analytics/", OwnerVenueAnalyticsView.as_view(), name="owner_venue_analytics"),
    
    path("adminpanel/", AdminDashboardView.as_view(), name="admin_dashboard"),

    path("adminpanel/users/", AdminUserListView.as_view(), name="admin_users_list"),
    path("adminpanel/users/<int:pk>/edit/", AdminUserUpdateView.as_view(), name="admin_users_edit"),
    path("adminpanel/users/<int:pk>/delete/", AdminUserDeleteView.as_view(), name="admin_users_delete"),

    path("adminpanel/venues/", AdminVenueListView.as_view(), name="admin_venues_list"),
    path("adminpanel/venues/<int:pk>/edit/", AdminVenueUpdateView.as_view(), name="admin_venues_edit"),
    path("adminpanel/venues/<int:pk>/delete/", AdminVenueDeleteView.as_view(), name="admin_venues_delete"),

    path("adminpanel/activities/", AdminActivityListView.as_view(), name="admin_activities_list"),
    path("adminpanel/activities/<int:pk>/edit/", AdminActivityUpdateView.as_view(), name="admin_activities_edit"),
    path("adminpanel/activities/<int:pk>/delete/", AdminActivityDeleteView.as_view(), name="admin_activities_delete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)