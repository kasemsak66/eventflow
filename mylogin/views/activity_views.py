from datetime import timedelta
from io import BytesIO
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from mylogin.forms import (
    ActivityManualRegistrationForm,ActivityForm
)
from mylogin.models import ActivityParticipants, Booking, Activity
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Q, Count , Avg
from openlocationcode import openlocationcode as olc
import qrcode
from mylogin.utils import _completed_status_value
from django.db.models.functions import TruncDate




# ========================================
# ActivityCreateView
# GET : แสดงฟอร์มสร้างกิจกรรมใหม่ + ส่ง list กิจกรรมของฉัน
# POST: รับข้อมูลฟอร์ม สร้างกิจกรรมใหม่ แล้ว redirect ไปหน้า detail
# ========================================
class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/createActivity.html'

    def get_success_url(self):
        return reverse_lazy('activity_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        # ใช้ทั้ง GET/POST: เตรียม kwargs ให้ฟอร์ม (user + booking queryset)
        kwargs = super().get_form_kwargs()

        COMPLETED = _completed_status_value()
        owner_bookings = (
            Booking.objects
            .filter(
                user=self.request.user,
                status=COMPLETED,
                activity__isnull=True
            )
            .select_related('venue')
            .order_by('-start_date')
        )

        kwargs['initial'] = {'booking__queryset': owner_bookings}
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # POST: ก่อน save ให้กำหนด organizer = user ที่ล็อกอิน
        form.instance.organizer = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # GET: ส่ง my_activities (กิจกรรมที่เราจัดเอง) ไปให้ template
        ctx = super().get_context_data(**kwargs)
        ctx['my_activities'] = (
            Activity.objects
            .filter(organizer=self.request.user)
            .select_related('booking', 'booking__venue', 'organizer')
            .order_by('-start_date', '-start_time')
        )
        return ctx


# ========================================
# ActivityListView
# GET: แสดง list กิจกรรมทั้งหมด + กิจกรรมของฉันใน context
# ========================================
class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = 'activities/listActivity.html'
    context_object_name = 'all_activities'

    def get_queryset(self):
        # GET: ดึงกิจกรรมทั้งหมด พร้อม annotate จำนวนผู้เข้าร่วม (joined_count)
        return (
            Activity.objects
            .select_related('booking', 'booking__venue', 'organizer')
            .annotate(
                joined_count=Count(
                    'activity_participations',
                    filter=Q(activity_participations__status='joined')
                )
            )
            .order_by('-start_date', '-start_time')
        )

    def get_context_data(self, **kwargs):
        # GET: เพิ่ม my_activities = กิจกรรมที่เราเป็น organizer
        ctx = super().get_context_data(**kwargs)
        ctx['my_activities'] = (
            self.get_queryset()
            .filter(organizer=self.request.user)
        )
        return ctx


# ========================================
# ActivityDetailView
# GET: แสดงรายละเอียดกิจกรรม + ผู้เข้าร่วม + สิทธิ์ดู booking
# ========================================
class ActivityDetailView(LoginRequiredMixin, DetailView):
    model = Activity
    template_name = 'activities/detailActivity.html'
    context_object_name = 'activity'

    def get_queryset(self):
        # GET: preload activity + booking + venue + user ที่เกี่ยวข้อง
        return (
            Activity.objects
            .select_related('booking', 'booking__venue', 'booking__user', 'organizer')
        )

    def get_context_data(self, **kwargs):
        # GET: ใส่ participants, is_joined, can_view_booking ลง context
        ctx = super().get_context_data(**kwargs)
        activity = self.object

        participants_qs = (
            ActivityParticipants.objects
            .filter(activity=activity, status='joined')
            .select_related('user')
        )
        ctx['participants'] = participants_qs

        if self.request.user.is_authenticated:
            ctx['is_joined'] = participants_qs.filter(
                user=self.request.user,
                is_manual=False
            ).exists()
        else:
            ctx['is_joined'] = False

        can_view_booking = False
        if self.request.user.is_authenticated and activity.booking_id:
            if (
                activity.organizer_id == self.request.user.id
                or activity.booking.user_id == self.request.user.id
                or self.request.user.is_staff
            ):
                can_view_booking = True

        ctx['can_view_booking'] = can_view_booking
        return ctx


# ========================================
# ActivityUpdateView
# GET : แสดงฟอร์มแก้ไขกิจกรรม (เฉพาะของตัวเอง)
# POST: บันทึกการแก้ไข แล้ว redirect ไปหน้า detail
# ========================================
class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/createActivity.html'  # ใช้ template เดียวกับ create

    def get_success_url(self):
        return reverse_lazy('activity_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        # ใช้ทั้ง GET/POST: ส่ง user เข้าไปให้ form ตรวจสิทธิ์/กรอง booking
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        # ใช้ทั้ง GET/POST: กันผู้ใช้ที่ไม่มีสิทธิ์แก้ไข
        try:
            self.get_object()
        except Exception:
            return HttpResponseForbidden("คุณไม่มีสิทธิ์แก้ไขกิจกรรมนี้")
        return super().dispatch(request, *args, **kwargs)


# ========================================
# ActivityDeleteView
# GET : แสดงหน้า confirm ลบกิจกรรมของตัวเอง
# POST: ลบกิจกรรม แล้ว redirect ไปหน้า list
# ========================================
class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = Activity
    template_name = 'activities/deleteActivity.html'
    success_url = reverse_lazy('activity_list')

    def get_queryset(self):
        # จำกัดให้ลบได้เฉพาะกิจกรรมที่เราเป็น organizer
        return Activity.objects.filter(organizer=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        # ใช้ทั้ง GET/POST: เช็คสิทธิ์ก่อนลบ
        try:
            self.get_object()
        except Exception:
            return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบกิจกรรมนี้")
        return super().dispatch(request, *args, **kwargs)


# ========================================
# activity_join_toggle
# POST (ตามปกติจากปุ่มกด): toggle เข้าร่วม / ถอนตัวจากกิจกรรม
# ========================================
@login_required
def activity_join_toggle(request, pk):
    activity = get_object_or_404(Activity, pk=pk)

    if activity.participants.filter(pk=request.user.pk).exists():
        activity.participants.remove(request.user)
    else:
        activity.participants.add(request.user)

    return redirect(reverse('activity_detail', kwargs={'pk': activity.pk}))


# ========================================
# activity_register
# GET : แสดงหน้าลงทะเบียนกิจกรรม (เลือกลงแบบ member หรือ manual)
# POST: บันทึกการลงทะเบียน (member หรือ manual ตามปุ่มที่กด)
# ========================================
def activity_register(request, pk):
    """
    หน้าลงทะเบียนกิจกรรมผ่าน QR / ลิงก์ตรง
    - member: ต้องล็อกอิน ใช้บัญชีผู้ใช้ (user ไม่เป็น null)
    - manual: ไม่ต้องล็อกอิน กรอกข้อมูลเองเก็บในฟิลด์ manual_*
    """
    activity = get_object_or_404(Activity, pk=pk)

    is_joined = False
    if request.user.is_authenticated:
        is_joined = ActivityParticipants.objects.filter(
            activity=activity,
            user=request.user,
            status='joined',
            is_manual=False,
        ).exists()

    manual_form = ActivityManualRegistrationForm(request.POST or None)

    if request.method == 'POST':

        # ลงทะเบียนด้วยบัญชีผู้ใช้
        if 'register_member' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'กรุณาเข้าสู่ระบบก่อนลงทะเบียนด้วยบัญชีผู้ใช้')
                return redirect('login')

            participant, created = ActivityParticipants.objects.update_or_create(
                activity=activity,
                user=request.user,
                defaults={
                    'status': 'joined',
                    'is_manual': False,
                    'manual_full_name': '',
                    'manual_email': '',
                    'manual_phone': '',
                    'manual_note': '',
                },
            )

            if created:
                messages.success(request, 'ลงทะเบียนเข้าร่วมกิจกรรมเรียบร้อยแล้ว')
            else:
                messages.info(request, 'คุณได้ลงทะเบียนเข้าร่วมกิจกรรมนี้แล้ว')

            return redirect('activity_detail', pk=activity.pk)

        # ลงทะเบียนแบบ guest (manual)
        if 'register_manual' in request.POST:
            if request.user.is_authenticated:
                messages.error(
                    request,
                    'คุณมีบัญชีผู้ใช้ในระบบแล้ว กรุณาใช้การลงทะเบียนด้วยบัญชีผู้ใช้ทางด้านซ้าย'
                )
                return redirect('activity_register', pk=activity.pk)

            if manual_form.is_valid():
                manual_participant = manual_form.save(commit=False)
                manual_participant.activity = activity
                manual_participant.user = None
                manual_participant.is_manual = True
                manual_participant.status = 'joined'
                manual_participant.save()

                messages.success(request, 'ลงทะเบียนแบบไม่ต้องล็อกอินเรียบร้อยแล้ว')
                return redirect('activity_register', pk=activity.pk)

    context = {
        'activity': activity,
        'is_joined': is_joined,
        'manual_form': manual_form,
    }
    return render(request, 'activities/registerActivity.html', context)


# ========================================
# activity_qr
# GET: แสดงหน้า QR สำหรับให้ organizer เอาไปให้คนสแกนลงทะเบียน
# ========================================
@login_required
def activity_qr(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if activity.organizer != request.user:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึง QR ของกิจกรรมนี้')
        return redirect('activity_detail', pk=activity.pk)

    register_url = request.build_absolute_uri(
        reverse('activity_register', args=[activity.pk])
    )

    context = {
        'activity': activity,
        'register_url': register_url,
    }
    return render(request, 'activities/qrActivity.html', context)


# ========================================
# activity_qr_image
# GET: สร้างรูป PNG ของ QR code และส่งกลับเป็น image/png
# ========================================
@login_required
def activity_qr_image(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if activity.organizer != request.user:
        return HttpResponse(status=403)

    register_url = request.build_absolute_uri(
        reverse('activity_register', args=[activity.pk])
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(register_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_png = buffer.getvalue()
    buffer.close()

    return HttpResponse(image_png, content_type="image/png")

class OwnerActivityAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/owner_activity_analytics.html"

    def _pct_change(self, current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        owner = self.request.user
        now = timezone.now()
        today = timezone.localdate()
        
        # ช่วงเวลา
        start_7d = now - timedelta(days=7)
        start_prev_7d = now - timedelta(days=14)
        start_7d_date = today - timedelta(days=7)

        # Base Querysets
        my_activities = Activity.objects.filter(booking__venue__owner=owner).select_related("booking__venue")
        my_participations = ActivityParticipants.objects.filter(activity__booking__venue__owner=owner)

        # Totals & Highlights
        total_activities = my_activities.count()
        ctx["total_activities"] = total_activities
        ctx["total_participants_joined"] = my_participations.filter(status="joined").count()

        # 7 Day Activity Stats
        act_7d = my_activities.filter(start_date__gte=start_7d_date, start_date__lt=today).count()
        act_prev = my_activities.filter(start_date__gte=today - timedelta(days=14), start_date__lt=start_7d_date).count()
        ctx.update({
            "activities_7d": act_7d,
            "activities_delta": act_7d - act_prev,
            "activities_pct": self._pct_change(act_7d, act_prev)
        })

        # 7 Day Join Stats
        join_7d = my_participations.filter(status="joined", joined_at__gte=start_7d).count()
        join_prev = my_participations.filter(status="joined", joined_at__gte=start_prev_7d, joined_at__lt=start_7d).count()
        ctx.update({
            "joined_7d": join_7d,
            "joined_delta": join_7d - join_prev,
            "joined_pct": self._pct_change(join_7d, join_prev)
        })

        # กราฟสถิติการ Join ย้อนหลัง 7 วัน
        chart_dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        daily_joins = (
            my_participations.filter(status="joined", joined_at__date__gte=start_7d_date)
            .annotate(date=TruncDate('joined_at'))
            .values('date')
            .annotate(count=Count('id'))
        )
        join_map = {item['date']: item['count'] for item in daily_joins}
        
        ctx["chart_labels"] = [d.strftime("%d %b") for d in chart_dates]
        ctx["chart_data"] = [join_map.get(d, 0) for d in chart_dates]

        # ข้อมูลอื่นๆ
        ctx["guest_joined_total"] = my_participations.filter(status="joined").filter(Q(user__isnull=True) | Q(is_manual=True)).count()
        ctx["member_joined_total"] = my_participations.filter(status="joined", user__isnull=False, is_manual=False).count()
        
        avg_joined = my_activities.annotate(joined_count=Count("activity_participations", filter=Q(activity_participations__status="joined"))).aggregate(avg=Avg("joined_count"))["avg"] or 0
        ctx["avg_joined_per_activity"] = round(float(avg_joined), 1)

        finished = my_activities.filter(status="finished").count()
        ctx["finished_count"] = finished
        ctx["completion_rate"] = round((finished / total_activities * 100), 1) if total_activities else 0

        ctx["activities_by_status"] = my_activities.values("status").annotate(count=Count("activity_id")).order_by("-count")
        ctx["top_activities"] = my_activities.annotate(joined_count=Count("activity_participations", filter=Q(activity_participations__status="joined"))).order_by("-joined_count")[:5]
        ctx["recent_activities"] = my_activities.annotate(joined_count=Count("activity_participations", filter=Q(activity_participations__status="joined"))).order_by("-start_date")[:5]

        return ctx