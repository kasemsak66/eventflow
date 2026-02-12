from datetime import timedelta
from io import BytesIO
from pyexpat.errors import messages
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.forms import HiddenInput
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from mylogin.forms import VenueAmenityForm, VenueForm, VenueImageFormSet
from mylogin.models import ActivityParticipants, Favorite, Venue, VenueAmenity, Booking, Activity
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F , Sum , Count 
from django.db.models.functions import TruncDate

# ========================================
# Venue List (แสดงสถานที่ทั้งหมด)
# ========================================
class VenueListView(ListView):
    model = Venue
    template_name = 'venue/listVenue.html'
    context_object_name = 'venues'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        favorite_ids = []
        if self.request.user.is_authenticated:
            favorite_ids = list(
                Favorite.objects
                .filter(user=self.request.user)
                .values_list('venue_id', flat=True)
            )

        ctx['favorite_venue_ids'] = favorite_ids
        return ctx


# ========================================
# Venue Detail (ดูรายละเอียดสถานที่)
# ========================================
class VenueDetailView(DetailView):
    model = Venue
    template_name = 'venue/detailVenue.html'
    context_object_name = 'venue'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        venue = self.object

        # รูปภาพ
        ctx["images"] = venue.images.all()[:5]

        # สถานที่ที่ถูกใจกับ user ปัจจุบัน
        is_favorited = False
        if self.request.user.is_authenticated:
            is_favorited = Favorite.objects.filter(
                user=self.request.user,
                venue=venue,
            ).exists()

        ctx["is_favorited"] = is_favorited
        return ctx


# ========================================
# VenueCreateView (สร้างสถานที่ใหม่)
# ========================================
class VenueCreateView(CreateView):
    model = Venue
    form_class = VenueForm
    template_name = 'venue/createVenue.html'
    success_url = reverse_lazy('venue_list')

    # GET → แสดงฟอร์ม Venue + Amenity + Images
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["amenity_form"] = kwargs.get("amenity_form") or VenueAmenityForm()
        ctx["image_formset"] = kwargs.get("image_formset") or VenueImageFormSet()
        return ctx

    # POST → รับค่าจากทุกฟอร์มและสร้าง Venue แบบ atomic (save ทั้งหมดหรือไม่ save เลย)
    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        amenity_form = VenueAmenityForm(request.POST)
        image_formset = VenueImageFormSet(request.POST, request.FILES)

        if form.is_valid() and amenity_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                venue = form.save(commit=False)
                if request.user.is_authenticated:
                    venue.owner = request.user
                venue.save()

                amenity = amenity_form.save(commit=False)
                amenity.venue = venue
                amenity.save()

                image_formset.instance = venue
                image_formset.save()

            return redirect(self.success_url)

        # ถ้าไม่ผ่าน validation → render ฟอร์มเดิมพร้อม error
        return self.render_to_response(self.get_context_data(
            form=form,
            amenity_form=amenity_form,
            image_formset=image_formset
        ))


# ========================================
# VenueUpdateView (แก้ไขสถานที่)
# ========================================
class VenueUpdateView(UpdateView):
    model = Venue
    form_class = VenueForm
    template_name = 'venue/updateVenue.html'
    success_url = reverse_lazy('venue_list')

    # GET → โหลดฟอร์ม Venue + Amenity + Images
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        venue = self.object

        amenity, _ = VenueAmenity.objects.get_or_create(venue=venue)
        ctx["amenity_form"] = kwargs.get("amenity_form") or VenueAmenityForm(instance=amenity)

        ctx["image_formset"] = kwargs.get("image_formset") or VenueImageFormSet(
            instance=venue, prefix='images'
        )

        # จำนวนภาพที่ยังเพิ่มได้ (สูงสุด 5)
        images_qs = getattr(venue, "images", None)
        if images_qs is not None:
            ctx["images_left"] = max(0, 5 - images_qs.count())
        else:
            ctx["images_left"] = max(0, 5 - getattr(venue, "venueimage_set").count())

        return ctx

    # POST → ตรวจสอบและบันทึกการแก้ไขทั้งหมดแบบ atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        amenity = VenueAmenity.objects.get_or_create(venue=self.object)[0]
        amenity_form = VenueAmenityForm(request.POST, instance=amenity)

        image_formset = VenueImageFormSet(
            request.POST, request.FILES, instance=self.object, prefix='images'
        )

        if form.is_valid() and amenity_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                venue = form.save(commit=False)
                venue.save()
                amenity_form.save()
                image_formset.save()
            return redirect(self.success_url)

        # validation ไม่ผ่าน → render template พร้อม error
        return self.render_to_response(self.get_context_data(
            form=form,
            amenity_form=amenity_form,
            image_formset=image_formset
        ))

    # จำกัดสิทธิ์เฉพาะเจ้าของสถานที่เท่านั้นที่แก้ไขได้
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user:  # type: ignore
            return HttpResponseForbidden("คุณไม่มีสิทธิ์แก้ไขสถานที่นี้")
        return super().dispatch(request, *args, **kwargs)


# ========================================
# VenueDeleteView (ลบสถานที่)
# ========================================
class VenueDeleteView(DeleteView):
    model = Venue
    template_name = 'venue/deleteVenue.html'
    success_url = reverse_lazy('venue_list')

    # ต้องเป็นเจ้าของสถานที่เท่านั้นที่ลบได้
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user:  # type: ignore
            return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบสถานที่นี้")
        return super().dispatch(request, *args, **kwargs)


# ========================================
# MyVenueListView (สถานที่ของฉัน)
# ========================================
class MyVenueListView(LoginRequiredMixin, ListView):
    model = Venue
    template_name = 'venue/my_venues.html'
    context_object_name = 'venues'
    paginate_by = 10

    # GET → ดึงเฉพาะสถานที่ที่ผู้ใช้เป็นเจ้าของ
    def get_queryset(self):
        return Venue.objects.filter(owner=self.request.user)


# ========================================
# VenueMapView (หน้าแผนที่)
# ========================================
class VenueMapView(TemplateView):
    template_name = "venue/venue_map.html"

    # GET → เตรียมข้อมูลสถานที่ทั้งหมดในรูปแบบดิบสำหรับ map
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs = (
            Venue.objects
            .annotate(id=F("venue_id"))
            .values("id", "name", "code", "latitude", "longitude")
            .order_by("name")
        )

        data = list(qs)
        ctx["venues"] = data
        ctx["venues_count"] = len(data)

        return ctx

class FavoriteToggleView(LoginRequiredMixin, View):
    """
    กดใจ / ยกเลิกใจ สถานที่
    URL: /venues/<venue_id>/favorite/
    """
    def post(self, request, venue_id):
        venue = get_object_or_404(Venue, pk=venue_id)

        # เช็กก่อนว่ามี favorite อยู่แล้วไหม
        fav = Favorite.objects.filter(
            user=request.user,
            venue=venue,
        ).first()

        # เคสนี้คือ "ยกเลิกถูกใจ" → ลบได้เสมอ ไม่เกี่ยวกับ limit
        if fav:
            fav.delete()
            favorited = False

        else:
            # จะเพิ่ม favorite ใหม่ → เช็ก limit ก่อน
            current_count = Favorite.objects.filter(user=request.user).count()
            if current_count >= 15:
                # เกิน 15 แล้ว ห้ามเพิ่ม
                error_msg = "คุณบันทึกสถานที่ที่ถูกใจครบ 15 แห่งแล้ว"

                # ถ้าเป็น AJAX (fetch/htmx) → ตอบ JSON กลับไป
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({
                        "favorited": False,   # ยังไม่ถูกใจสถานที่นี้
                        "limited": True,
                        "error": error_msg,
                    })

                # ถ้าเป็น form submit ปกติ → redirect กลับหน้าเดิม พร้อม flash message
                messages.error(request, error_msg)
                next_url = (
                    request.POST.get("next")
                    or request.META.get("HTTP_REFERER")
                    or reverse("venue_detail", kwargs={"pk": venue.pk})
                )
                return redirect(next_url)

            # ยังไม่ถึง limit → เพิ่ม favorite ได้
            Favorite.objects.create(
                user=request.user,
                venue=venue,
            )
            favorited = True
            # messages.success(request, "บันทึกเป็นสถานที่ที่คุณถูกใจแล้ว ❤️")

        # ถ้าเป็น AJAX (fetch/htmx) → ตอบกลับ JSON ไม่ต้อง redirect หน้า
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "favorited": favorited,
                "limited": False,
            })

        # กรณี fallback (ส่งฟอร์มปกติ)
        next_url = (
            request.POST.get("next")
            or request.META.get("HTTP_REFERER")
            or reverse("venue_detail", kwargs={"pk": venue.pk})
        )
        return redirect(next_url)


class FavoriteListView(LoginRequiredMixin, ListView):
    """
    แสดงรายการสถานที่ที่ผู้ใช้กดถูกใจไว้
    URL: /favorites/
    """
    model = Favorite
    template_name = 'home/profile.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return (
            Favorite.objects
            .filter(user=self.request.user)
            .select_related('venue')
            .order_by('-created_at')
        )
        
class OwnerVenueAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/owner_venue_analytics.html"

    def _pct_change(self, current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        owner = self.request.user
        now = timezone.now()
        start_7d = now - timedelta(days=7)
        start_prev_7d = now - timedelta(days=14)

        # ข้อมูลพื้นฐาน
        my_venues = Venue.objects.filter(owner=owner)
        my_bookings = Booking.objects.filter(venue__owner=owner).select_related("venue", "user")
        my_activities = Activity.objects.filter(booking__venue__owner=owner)
        my_participations = ActivityParticipants.objects.filter(activity__booking__venue__owner=owner)

        # 1. Bookings Highlights
        b_7d = my_bookings.filter(created_at__gte=start_7d).count()
        b_prev = my_bookings.filter(created_at__gte=start_prev_7d, created_at__lt=start_7d).count()
        ctx["bookings_7d"] = b_7d
        ctx["bookings_delta"] = b_7d - b_prev
        ctx["bookings_pct"] = self._pct_change(b_7d, b_prev)

        # 2. Revenue Highlights
        rev_status = ["approved", "awaiting_confirmation", "completed"]
        r_7d = my_bookings.filter(status__in=rev_status, created_at__gte=start_7d).aggregate(s=Sum("total_price"))["s"] or 0
        r_prev = my_bookings.filter(status__in=rev_status, created_at__gte=start_prev_7d, created_at__lt=start_7d).aggregate(s=Sum("total_price"))["s"] or 0
        ctx["revenue_7d"] = r_7d
        ctx["revenue_delta"] = r_7d - r_prev
        ctx["revenue_pct"] = self._pct_change(float(r_7d), float(r_prev))

        # 3. Totals
        ctx["total_bookings"] = my_bookings.count()
        ctx["total_activities"] = my_activities.count()
        ctx["total_joined"] = my_participations.filter(status="joined").count()

        # 4. Chart Data (7 Days)
        chart_dates = [(now - timedelta(days=i)).date() for i in range(6, -1, -1)]
        daily_data = my_bookings.filter(created_at__gte=start_7d).annotate(date=TruncDate('created_at')).values('date').annotate(c=Count('booking_id'))
        b_map = {item['date']: item['c'] for item in daily_data}
        
        ctx["chart_labels"] = [d.strftime("%d %b") for d in chart_dates]
        ctx["chart_data"] = [b_map.get(d, 0) for d in chart_dates]

        # 5. Tables
        ctx["bookings_by_status"] = my_bookings.values("status").annotate(count=Count("booking_id")).order_by("-count")
        ctx["top_venues"] = my_bookings.values("venue__name").annotate(count=Count("booking_id")).order_by("-count")[:5]
        
        return ctx
    