from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login , logout as auth_logout,update_session_auth_hash
from django.forms import HiddenInput
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from mylogin.forms import  CustomUserCreateForm, CustomUserLoginForm, CustomUserUpdateForm, VenueAmenityForm, VenueForm, VenueImageFormSet , BookingForm, PaymentSlipForm, OwnerBankForm
from mylogin.models import Venue, VenueAmenity , Booking
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView ,TemplateView
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal
from django.views.generic import TemplateView
from django.db.models import F, Q
from openlocationcode import openlocationcode as olc 

def login(request):
    next_url = request.GET.get('next', None)
    if request.method == 'POST':
        
        form = CustomUserLoginForm(request, data=request.POST)
        email = request.POST.get('username')
        password = request.POST.get('password')
        print(f'login with email={email}, password={password}')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, "อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    else:
        form = CustomUserLoginForm()

    for field in form.fields.values():
        field.widget.attrs.update({
        'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af] bg-white text-[#112d4e]'
    })

    return render(request, 'login.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            print(f'User created: {form.cleaned_data["email"]} with password: {form.cleaned_data["password1"]}')
            return redirect('login')
    else:
        form = CustomUserCreateForm()
    
    for field in form.fields.values():
        field.widget.attrs.update({
        'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af] bg-white text-[#112d4e]'
    })
    form.fields['email'].widget.attrs.update({'placeholder': 'กรอกอีเมล'})
    form.fields['first_name'].widget.attrs.update({'placeholder': 'กรอกชื่อ'})
    form.fields['last_name'].widget.attrs.update({'placeholder': 'กรอกนามสกุล'})
    form.fields['phone_num'].widget.attrs.update({'placeholder': 'กรอกหมายเลขโทรศัพท์'})
    form.fields['dob'].widget.attrs.update({'placeholder': 'วัน/เดือน/ปี'})
    form.fields['password1'].widget.attrs.update({'placeholder': 'กรอกรหัสผ่าน'})
    form.fields['password2'].widget.attrs.update({'placeholder': 'ยืนยันรหัสผ่าน'})


    return render(request, 'register.html', {'form': form})


@never_cache
@login_required(login_url='login')
def home(request):
    user = request.user
    context = {'user': user}
    return render(request, 'home/home.html', context)


@login_required
def profile_view(request):
    return render(request, 'home/profile.html')

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')

            if password:  # เฉพาะตอนมีรหัสผ่านใหม่เท่านั้นที่เปลี่ยน
                user.set_password(password)
                update_session_auth_hash(request, user)  # ป้องกัน logout
            else:
                user.password = request.user.password  # ใช้รหัสผ่านเดิม

            user.save()
            messages.success(request, 'อัปเดตข้อมูลเรียบร้อยแล้ว')
            return redirect('profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)

    return render(request, 'home/profile_edit.html', {'form': form})


class VenueListView(ListView):
    model = Venue
    template_name = 'venue/listVenue.html'
    context_object_name = 'venues'
    paginate_by = 10


class VenueDetailView(DetailView):
    model = Venue
    template_name = 'venue/detailVenue.html'
    context_object_name = 'venue'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["images"] = self.object.images.all()[:5]  #type: ignore
        return ctx


class VenueCreateView(CreateView):
    model = Venue
    form_class = VenueForm
    template_name = 'venue/createVenue.html'
    success_url = reverse_lazy('venue_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["amenity_form"] = kwargs.get("amenity_form") or VenueAmenityForm()
        ctx["image_formset"] = kwargs.get("image_formset") or VenueImageFormSet()
        return ctx

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
                # ไม่ต้อง set code — โมเดลจะคำนวณเองใน save()
                venue.save()

                amenity = amenity_form.save(commit=False)
                amenity.venue = venue
                amenity.save()

                image_formset.instance = venue
                image_formset.save()

            return redirect(self.success_url)

        return self.render_to_response(self.get_context_data(
            form=form,
            amenity_form=amenity_form,
            image_formset=image_formset
        ))

class VenueUpdateView(UpdateView):
    model = Venue
    form_class = VenueForm
    template_name = 'venue/updateVenue.html'
    success_url = reverse_lazy('venue_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        venue = self.object

        # amenity form
        amenity, _ = VenueAmenity.objects.get_or_create(venue=venue)
        ctx["amenity_form"] = kwargs.get("amenity_form") or VenueAmenityForm(instance=amenity)

        # image formset (ใส่ prefix='images' เสมอ)
        ctx["image_formset"] = kwargs.get("image_formset") or VenueImageFormSet(
            instance=venue, prefix='images'
        )

        # นับเหลือกี่รูป (ปรับ related name ตามโมเดลของคุณ)
        images_qs = getattr(venue, "images", None)
        if images_qs is not None:
            ctx["images_left"] = max(0, 5 - images_qs.count())
        else:
            # fallback ถ้า related name เป็นอย่างอื่น เช่น venueimage_set
            ctx["images_left"] = max(0, 5 - getattr(venue, "venueimage_set").count())

        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        # amenity form
        amenity = VenueAmenity.objects.get_or_create(venue=self.object)[0]
        amenity_form = VenueAmenityForm(request.POST, instance=amenity)

        # image formset (ต้อง prefix='images' ให้ตรงกับ GET)
        image_formset = VenueImageFormSet(
            request.POST, request.FILES, instance=self.object, prefix='images'
        )

        if form.is_valid() and amenity_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                venue = form.save(commit=False)
                # ปล่อยให้โมเดล/logic ภายใน save() คำนวณ Plus Code เองจาก lat/lng
                venue.save()
                amenity_form.save()
                image_formset.save()
            return redirect(self.success_url)

        # ไม่ผ่าน validation → ส่งกลับ template พร้อม error และ formset ที่มี prefix แล้ว
        return self.render_to_response(self.get_context_data(
            form=form,
            amenity_form=amenity_form,
            image_formset=image_formset
        ))
class VenueDeleteView(DeleteView):
    model = Venue
    template_name = 'venue/deleteVenue.html'
    success_url = reverse_lazy('venue_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user: #type:  ignore
            return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบสถานที่นี้")
        return super().dispatch(request, *args, **kwargs)
    
class MyVenueListView(LoginRequiredMixin, ListView):
    model = Venue
    template_name = 'venue/my_venues.html'
    context_object_name = 'venues'
    paginate_by = 10

    def get_queryset(self):
        return Venue.objects.filter(owner=self.request.user)
    

class VenueMapView(TemplateView):
    template_name = "venue/venue_map.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # ส่งทุกรายการ แล้วให้ JS คัดเฉพาะที่มีพิกัด (กันกรองพลาดจนไม่มีหมุด)
        qs = (
            Venue.objects
            .annotate(id=F("venue_id"))  # ถ้า PK ชื่อ venue_id
            .values("id", "name", "code", "latitude", "longitude")
            .order_by("name")
        )
        data = list(qs)
        ctx["venues"] = data
        ctx["venues_count"] = len(data)  # เผื่อ debug ใน template
        return ctx

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'book/createBooking.html'
    success_url = reverse_lazy('booking_list')

    def dispatch(self, request, *args, **kwargs):
        # ✅ ดึง venue_id จาก query string แทน kwargs
        venue_id = self.request.GET.get('venue_id')
        self.venue = get_object_or_404(Venue, venue_id=venue_id)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venue'] = self.venue  
        return context

    def get_initial(self):
        return {'venue': self.venue}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['venue'].widget = HiddenInput()  
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.venue = self.venue

        if form.instance.venue.owner == self.request.user:
            form.add_error(None, "คุณไม่สามารถจองสถานที่ที่คุณเป็นเจ้าของได้")
            return self.form_invalid(form)

        num_days = (form.instance.end_date - form.instance.start_date).days + 1
        form.instance.total_price = num_days * form.instance.venue.price_per_day

        messages.success(self.request, "จองสถานที่สำเร็จ")
        return super().form_valid(form)

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'book/listBooking.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        # รายการที่ฉันจอง
        return Booking.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # รายการที่คนอื่นจองสถานที่ของฉัน
        context['owner_bookings'] = Booking.objects.filter(venue__owner=self.request.user)
        return context

class BookingDeleteView(DeleteView):
    model = Booking
    template_name = 'book/deleteBooking.html'
    success_url = reverse_lazy('booking_list')

    def dispatch(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.user != request.user: #type:  ignore
            return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบการจองนี้")
        return super().dispatch(request, *args, **kwargs)
    
def _is_owner(user, booking: Booking) -> bool:
    return booking.venue.owner == user

@login_required(login_url='login')
def booking_approve_initial(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not _is_owner(request.user, booking):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการนี้")

    # ต้องมีข้อมูลธนาคารหรือรูป QR ก่อน
    if not (request.user.bank_qr or (request.user.bank_name and request.user.bank_account_number)):
        messages.warning(request, "กรุณาเพิ่มข้อมูลบัญชี/QR ก่อนอนุมัติ")
        if request.method == "POST":
            form = OwnerBankForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "บันทึกข้อมูลการรับชำระแล้ว ลองอนุมัติอีกครั้ง")
                return redirect('booking_approve_initial', pk=booking.pk)
        else:
            form = OwnerBankForm(instance=request.user)
        return render(request, 'book/owner_bank_required.html', {"form": form, "booking": booking})

    # ผ่านเงื่อนไขธนาคาร → อนุมัติรอบแรก
    booking.status = 'approved'   # รอชำระเงิน
    booking.approved_at = timezone.now()
    booking.save(update_fields=['status', 'approved_at'])
    messages.success(request, "อนุมัติคำขอแล้ว — ผู้เช่าจะเห็นรายละเอียดการชำระเงิน")
    return redirect('booking_list')

@login_required(login_url='login')
def booking_upload_slip(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if booking.user != request.user:
        return HttpResponseForbidden("อนุญาตเฉพาะผู้จอง")
    if booking.status != 'approved':
        messages.error(request, "สถานะไม่ถูกต้องสำหรับการอัปโหลดสลิป")
        return redirect('booking_list')

    if request.method == "POST":
        form = PaymentSlipForm(request.POST, request.FILES, instance=booking)
        if form.is_valid():
            # ✅ กันเผื่อเช็คซ้ำความเท่ากันของยอด
            amount = form.cleaned_data["amount_paid"]
            required = booking.total_price
            if Decimal(amount) != Decimal(required):
                form.add_error("amount_paid", f"ต้องชำระ {required} บาท (คุณกรอก {amount} บาท)")
            else:
                form.save()  # บันทึก amount_paid + payment_slip
                booking.status = 'awaiting_confirmation'
                booking.slip_uploaded_at = timezone.now()
                booking.save(update_fields=['status', 'slip_uploaded_at'])
                messages.success(request, "อัปโหลดสลิปเรียบร้อย รอเจ้าของตรวจสอบ")
                return redirect('booking_list')
    else:
        form = PaymentSlipForm(instance=booking)

    return render(request, 'book/upload_slip.html', {"form": form, "booking": booking})

@login_required(login_url='login')
def booking_confirm_payment(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not _is_owner(request.user, booking):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการนี้")
    if booking.status != 'awaiting_confirmation':
        messages.error(request, "สถานะไม่ถูกต้องสำหรับการยืนยันการจอง")
        return redirect('booking_list')

    # ต้องมีสลิป
    if not booking.payment_slip:
        messages.error(request, "ไม่พบสลิปการชำระเงิน")
        return redirect('booking_list')

    # ต้องมีจำนวนเงิน
    if booking.amount_paid is None:
        messages.error(request, "รายการนี้ยังไม่มีจำนวนเงินที่ผู้เช่ากรอก")
        return redirect('booking_list')

    # เทียบยอด “ต้องเท่ากันเป๊ะ”
    # (ถ้าต้องการยอมรับส่วนต่างเล็กน้อย เช่น ค่าปัดเศษ โค้ดตัวอย่าง tolerance ด้านล่าง)
    required = Decimal(booking.total_price)
    paid = Decimal(booking.amount_paid)

    if paid != required:
        diff = paid - required
        # แสดงข้อความชัดเจน
        messages.error(
            request,
            f"จำนวนเงินไม่ตรงกับยอดที่ต้องชำระ: ต้องชำระ {required} บาท แต่ชำระมา {paid} บาท (ต่าง {diff:+})"
        )
        # คงสถานะไว้ที่ 'awaiting_confirmation' ให้เจ้าของตัดสินใจว่าจะ 'reject' หรือให้ผู้เช่าแก้ไข
        return redirect('booking_list')

    # ผ่านเงื่อนไข → ยืนยันสำเร็จ
    booking.status = 'completed'
    booking.completed_at = timezone.now()
    booking.save(update_fields=['status', 'completed_at'])
    messages.success(request, "ยืนยันการจองเสร็จสมบูรณ์")
    return redirect('booking_list')

@login_required(login_url='login')
def booking_reject(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not _is_owner(request.user, booking):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการนี้")
    booking.status = 'rejected'
    booking.save(update_fields=['status'])
    messages.info(request, "ปฏิเสธคำขอแล้ว")
    return redirect('booking_list')

@login_required(login_url='login')
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if booking.user != request.user:
        return HttpResponseForbidden("อนุญาตเฉพาะผู้จอง")
    if booking.status in ['completed', 'cancelled']:
        messages.error(request, "ไม่สามารถยกเลิกในสถานะปัจจุบันได้")
        return redirect('booking_list')
    booking.status = 'cancelled'
    booking.save(update_fields=['status'])
    messages.info(request, "ยกเลิกแล้ว")
    return redirect('booking_list')
