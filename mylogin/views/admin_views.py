from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, UpdateView, DeleteView

from mylogin.models import Venue, Activity


User = get_user_model()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """บังคับให้เป็น staff เท่านั้น"""

    def test_func(self):
        return bool(self.request.user and self.request.user.is_staff)


# ========= Dashboard =========
class AdminDashboardView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"


# ========= USERS =========
class AdminUserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = "adminpanel/users_list.html"
    context_object_name = "users"
    paginate_by = 20
    ordering = ["-date_joined"]  # CustomUser มี date_joined auto_now_add

class AdminUserUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    template_name = "adminpanel/users_form.html"
    fields = ["email", "first_name", "last_name", "phone_num", "dob", "is_staff", "is_active"]
    success_url = reverse_lazy("admin_users_list")

class AdminUserDeleteView(StaffRequiredMixin, DeleteView):
    model = User
    template_name = "adminpanel/users_confirm_delete.html"
    success_url = reverse_lazy("admin_users_list")


# ========= VENUES =========
class AdminVenueListView(StaffRequiredMixin, ListView):
    model = Venue
    template_name = "adminpanel/venues_list.html"
    context_object_name = "venues"
    paginate_by = 20
    ordering = ["-venue_id"]

class AdminVenueUpdateView(StaffRequiredMixin, UpdateView):
    model = Venue
    template_name = "adminpanel/venues_form.html"
    fields = ["name", "description", "address", "price_per_day", "max_capacity", "latitude", "longitude", "owner"]
    success_url = reverse_lazy("admin_venues_list")

class AdminVenueDeleteView(StaffRequiredMixin, DeleteView):
    model = Venue
    template_name = "adminpanel/venues_confirm_delete.html"
    success_url = reverse_lazy("admin_venues_list")


# ========= ACTIVITIES =========
class AdminActivityListView(StaffRequiredMixin, ListView):
    model = Activity
    template_name = "adminpanel/activities_list.html"
    context_object_name = "activities"
    paginate_by = 20
    ordering = ["-start_date", "-start_time"]

class AdminActivityUpdateView(StaffRequiredMixin, UpdateView):
    model = Activity
    template_name = "adminpanel/activities_form.html"
    fields = ["name", "description", "start_date", "end_date", "start_time", "end_time",
              "max_participants", "status", "organizer", "booking"]
    success_url = reverse_lazy("admin_activities_list")

class AdminActivityDeleteView(StaffRequiredMixin, DeleteView):
    model = Activity
    template_name = "adminpanel/activities_confirm_delete.html"
    success_url = reverse_lazy("admin_activities_list")
