from io import BytesIO
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.forms import HiddenInput
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from mylogin.forms import (
    BookingForm, PaymentSlipForm, OwnerBankForm, ActivityForm
)
from mylogin.models import ActivityParticipants, Venue, VenueAmenity, Booking, Activity
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal
from django.views.generic import TemplateView
from django.db.models import F, Q
from openlocationcode import openlocationcode as olc
import qrcode
from mylogin.utils import _completed_status_value


# ========================================
# BookingCreateView (สร้างการจอง)
# ========================================
class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'book/createBooking.html'
    success_url = reverse_lazy('booking_list')

    # ใช้ dispatch เพื่อโหลด venue จาก query string ก่อน (ใช้ได้ทั้ง GET/POST)
    def dispatch(self, request, *args, **kwargs):
        venue_id = self.request.GET.get('venue_id')
        self.venue = get_object_or_404(Venue, venue_id=venue_id)
        return super().dispatch(request, *args, **kwargs)
    
    # GET → ใส่ venue ลง context เพื่อใช้แสดงใน template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venue'] = self.venue
        return context

    # GET → initial value เริ่มต้นของฟอร์ม (ผูกกับ venue ปัจจุบัน)
    def get_initial(self):
        return {'venue': self.venue}

    # GET → ปรับ widget ของฟิลด์ venue ให้เป็น HiddenInput (ไม่ให้แก้จากหน้าเว็บ)
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['venue'].widget = HiddenInput()
        return form

    # POST → ตรวจสอบและบันทึกการจอง
    def form_valid(self, form):
        # ผูก user และ venue เข้ากับ booking
        form.instance.user = self.request.user
        form.instance.venue = self.venue

        # กันไม่ให้เจ้าของจองสถานที่ของตัวเอง
        if form.instance.venue.owner == self.request.user:
            form.add_error(None, "คุณไม่สามารถจองสถานที่ที่คุณเป็นเจ้าของได้")
            return self.form_invalid(form)

        # คำนวณจำนวนวันและราคารวม
        num_days = (form.instance.end_date - form.instance.start_date).days + 1
        form.instance.total_price = num_days * form.instance.venue.price_per_day

        messages.success(self.request, "จองสถานที่สำเร็จ")
        return super().form_valid(form)


# ========================================
# BookingListView (รายการจอง)
# ========================================
class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'book/listBooking.html'
    context_object_name = 'bookings'

    # GET → แสดงรายการจองที่เราจองเอง
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    # GET → เพิ่มรายการจองที่คนอื่นมาจองสถานที่ของเรา (owner_bookings)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owner_bookings'] = Booking.objects.filter(venue__owner=self.request.user)
        return context


# ========================================
# BookingDeleteView (ลบการจอง)
# ========================================
class BookingDeleteView(DeleteView):
    model = Booking
    template_name = 'book/deleteBooking.html'
    success_url = reverse_lazy('booking_list')

    # GET/POST → เช็คสิทธิ์ว่าคนลบต้องเป็นคนที่จองเท่านั้น
    def dispatch(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.user != request.user:  # type: ignore
            return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบการจองนี้")
        return super().dispatch(request, *args, **kwargs)


# helper function สำหรับเช็คว่า user เป็นเจ้าของสถานที่ของ booking หรือไม่
def _is_owner(user, booking: Booking) -> bool:
    return booking.venue.owner == user


# ========================================
# booking_approve_initial (เจ้าของอนุมัติคำขอครั้งแรก)
# ========================================
@login_required(login_url='login')
def booking_approve_initial(request, pk):
    """
    GET:
      - แสดงหน้าให้เจ้าของเพิ่มข้อมูลบัญชี (ถ้ายังไม่มี)
      - หรืออนุมัติคำขอจอง (ถ้าข้อมูลบัญชีครบแล้ว)
    POST:
      - เมื่อกรอกฟอร์ม OwnerBankForm แล้วกดบันทึก → เซฟข้อมูลธนาคาร แล้ว redirect ให้อนุมัติอีกรอบ
    """
    booking = get_object_or_404(Booking, pk=pk)

    # เฉพาะเจ้าของสถานที่เท่านั้นที่อนุมัติได้
    if not _is_owner(request.user, booking):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการนี้")

    # ถ้าเจ้าของยังไม่มีข้อมูลบัญชี/QR ให้บังคับกรอกก่อน
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

    # กรณีข้อมูลบัญชีครบแล้ว → อนุมัติคำขอจอง
    booking.status = 'approved'
    booking.approved_at = timezone.now()
    booking.save(update_fields=['status', 'approved_at'])
    messages.success(request, "อนุมัติคำขอแล้ว — ผู้เช่าจะเห็นรายละเอียดการชำระเงิน")
    return redirect('booking_list')


# ========================================
# booking_upload_slip (ผู้จองอัปโหลดสลิป)
# ========================================
@login_required(login_url='login')
def booking_upload_slip(request, pk):
    """
    GET:
      - แสดงฟอร์มอัปโหลดสลิปสำหรับ booking ที่สถานะ approved
    POST:
      - ตรวจ input: สิทธิ์เป็นผู้จอง, สถานะต้อง approved
      - ตรวจยอดเงินที่จ่าย == total_price
      - บันทึกสลิป, เปลี่ยนสถานะเป็น awaiting_confirmation
    """
    booking = get_object_or_404(Booking, pk=pk)

    # อนุญาตเฉพาะผู้จองเท่านั้น
    if booking.user != request.user:
        return HttpResponseForbidden("อนุญาตเฉพาะผู้จอง")

    # ต้องอยู่ในสถานะ approved เท่านั้นถึงจะอัปโหลดสลิปได้
    if booking.status != 'approved':
        messages.error(request, "สถานะไม่ถูกต้องสำหรับการอัปโหลดสลิป")
        return redirect('booking_list')

    if request.method == "POST":
        form = PaymentSlipForm(request.POST, request.FILES, instance=booking)
        if form.is_valid():
            amount = form.cleaned_data["amount_paid"]
            required = booking.total_price

            # ตรวจจำนวนเงินที่กรอกให้ตรงกับยอดที่ต้องจ่าย
            if Decimal(amount) != Decimal(required):
                form.add_error("amount_paid", f"ต้องชำระ {required} บาท (คุณกรอก {amount} บาท)")
            else:
                form.save()
                booking.status = 'awaiting_confirmation'
                booking.slip_uploaded_at = timezone.now()
                booking.save(update_fields=['status', 'slip_uploaded_at'])
                messages.success(request, "อัปโหลดสลิปเรียบร้อย รอเจ้าของตรวจสอบ")
                return redirect('booking_list')
    else:
        form = PaymentSlipForm(instance=booking)

    return render(request, 'book/upload_slip.html', {"form": form, "booking": booking})


# ========================================
# booking_confirm_payment (เจ้าของยืนยันการชำระเงิน)
# ========================================
@login_required(login_url='login')
def booking_confirm_payment(request, pk):
    """
    GET/POST:
      - ใช้สำหรับเจ้าของสถานที่ตรวจสอบสลิปและยืนยันการจอง
      - ตรวจสิทธิ์เจ้าของ, ตรวจสถานะ awaiting_confirmation
      - ตรวจว่ามีสลิป, มีจำนวนเงิน, จำนวนเงินตรงตาม total_price
      - ถ้าผ่านทั้งหมด → เปลี่ยนสถานะเป็น completed
    """
    booking = get_object_or_404(Booking, pk=pk)

    # เฉพาะเจ้าของสถานที่เท่านั้นที่ยืนยันได้
    if not _is_owner(request.user, booking):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการนี้")

    # ต้องอยู่สถานะ awaiting_confirmation
    if booking.status != 'awaiting_confirmation':
        messages.error(request, "สถานะไม่ถูกต้องสำหรับการยืนยันการจอง")
        return redirect('booking_list')

    # ต้องมีสลิปอัปโหลดแล้ว
    if not booking.payment_slip:
        messages.error(request, "ไม่พบสลิปการชำระเงิน")
        return redirect('booking_list')

    # ต้องมีจำนวนเงินที่ผู้เช่ากรอก
    if booking.amount_paid is None:
        messages.error(request, "รายการนี้ยังไม่มีจำนวนเงินที่ผู้เช่ากรอก")
        return redirect('booking_list')

    required = Decimal(booking.total_price)
    paid = Decimal(booking.amount_paid)

    # ตรวจจำนวนเงินที่จ่ายต้องตรงกับยอด
    if paid != required:
        diff = paid - required
        messages.error(
            request,
            f"จำนวนเงินไม่ตรงกับยอดที่ต้องชำระ: ต้องชำระ {required} บาท แต่ชำระมา {paid} บาท (ต่าง {diff:+})"
        )
        return redirect('booking_list')

    # ผ่านทุกเงื่อนไข → ปิดการจองเป็น completed
    booking.status = 'completed'
    booking.completed_at = timezone.now()
    booking.save(update_fields=['status', 'completed_at'])
    messages.success(request, "ยืนยันการจองเสร็จสมบูรณ์")
    return redirect('booking_list')


# ========================================
# booking_reject (เจ้าของปฏิเสธคำขอจอง)
# ========================================
@login_required(login_url='login')
def booking_reject(request, pk):
    """
    GET/POST:
      - เจ้าของสถานที่ใช้เปลี่ยนสถานะ booking เป็น rejected
    """
    booking = get_object_or_404(Booking, pk=pk)

    if not _is_owner(request.user, booking):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการนี้")

    booking.status = 'rejected'
    booking.save(update_fields=['status'])
    messages.info(request, "ปฏิเสธคำขอแล้ว")
    return redirect('booking_list')


# ========================================
# booking_cancel (ผู้จองยกเลิกการจองเอง)
# ========================================
@login_required(login_url='login')
def booking_cancel(request, pk):
    """
    GET/POST:
      - ผู้จองยกเลิก booking ของตัวเอง
      - ยกเลิกไม่ได้ถ้าสถานะเป็น completed หรือ cancelled แล้ว
    """
    booking = get_object_or_404(Booking, pk=pk)

    # ต้องเป็นผู้จองเท่านั้น
    if booking.user != request.user:
        return HttpResponseForbidden("อนุญาตเฉพาะผู้จอง")

    # ในสถานะ completed หรือ cancelled แล้ว ห้ามยกเลิกซ้ำ
    if booking.status in ['completed', 'cancelled']:
        messages.error(request, "ไม่สามารถยกเลิกในสถานะปัจจุบันได้")
        return redirect('booking_list')

    booking.status = 'cancelled'
    booking.save(update_fields=['status'])
    messages.info(request, "ยกเลิกแล้ว")
    return redirect('booking_list')
