from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.urls import reverse, reverse_lazy
from .models import CustomUser, Review, Venue, VenueAmenity, VenueImage, Booking
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from django.forms import HiddenInput, ModelChoiceField
from .models import Activity, ActivityParticipants
from django.db.models import Q

# ---------- Auth Forms ----------
class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_num', 'dob']
        widgets = {
            'password': forms.PasswordInput(),
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'อีเมล'
        self.fields['first_name'].label = 'ชื่อ'
        self.fields['last_name'].label = 'นามสกุล'
        self.fields['phone_num'].label = 'เบอร์โทรศัพท์'
        self.fields['dob'].label = 'วันเดือนปีเกิด'
        self.fields['password1'].label = 'รหัสผ่าน'
        self.fields['password2'].label = 'ยืนยันรหัสผ่าน'

        self.fields['email'].widget.attrs.update({'placeholder': 'กรอกอีเมล'})
        self.fields['first_name'].widget.attrs.update({'placeholder': 'กรอกชื่อ'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'กรอกนามสกุล'})
        self.fields['phone_num'].widget.attrs.update({'placeholder': 'กรอกหมายเลขโทรศัพท์'})
        self.fields['dob'].widget.attrs.update({'placeholder': 'วัน/เดือน/ปี'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'กรอกรหัสผ่าน'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'ยืนยันรหัสผ่าน'})

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded '
                         'focus:outline-none focus:ring-2 focus:ring-[#3f72af] '
                         'bg-white text-[#112d4e]'
            })


class UpdateProfileForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_num', 'dob',
            'bank_name', 'bank_account_number', 'bank_qr'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'phone_num': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 rounded'}),
            'bank_name': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
        }


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'อีเมล'
        self.fields['password'].label = 'รหัสผ่าน'
        self.fields['username'].widget.attrs.update({
            'placeholder': 'กรอกอีเมล',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded '
                     'focus:outline-none focus:ring-2 focus:ring-[#3f72af] '
                     'bg-white text-[#112d4e]'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'กรอกรหัสผ่าน',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded '
                     'focus:outline-none focus:ring-2 focus:ring-[#3f72af] '
                     'bg-white text-[#112d4e]'
        })

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = [
            "name",
            "description",
            "address",
            "price_per_day",
            "extra_amenities",
            "latitude",
            "longitude",
            "max_capacity",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded "
                         "focus:outline-none focus:ring-2 focus:ring-[#3f72af]",
                "placeholder": "เช่น โรงยิม A"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded resize-none",
                "placeholder": "รายละเอียดสถานที่",
                "rows": 4
            }),
            "address": forms.Textarea(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded resize-none",
                "placeholder": "ที่อยู่",
                "rows": 3
            }),
            "price_per_day": forms.NumberInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded text-right",
                "min": "0",
                "step": "1",
                "placeholder": "เช่น 1500"
            }),
            "extra_amenities": forms.Textarea(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded resize-none",
                "placeholder": "สิ่งอำนวยความสะดวกเพิ่มเติม (ถ้ามี)",
                "rows": 3
            }),
            "code": forms.TextInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded",
                "placeholder": "ระบบจะสร้าง Plus Code ให้อัตโนมัติ (แก้ได้)"
            }),
            "latitude": forms.NumberInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded",
                "step": "0.000001",
                "readonly": "readonly",
                "placeholder": "คลิกบนแผนที่เพื่อเลือกพิกัด"
            }),
            "longitude": forms.NumberInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded",
                "step": "0.000001",
                "readonly": "readonly",
                "placeholder": "คลิกบนแผนที่เพื่อเลือกพิกัด"
            }),
            "max_capacity": forms.NumberInput(attrs={
            "class": "w-full px-4 py-2 border border-gray-300 rounded",
            "min": "1",
            "placeholder": "จำนวนผู้เข้าร่วมสูงสุด เช่น 50"
            }),
        }
        labels = {
            "name": "ชื่อสถานที่",
            "description": "รายละเอียด",
            "address": "ที่อยู่ (หากไม่ระบุ ระบบจะเพิ่มให้อัตโนมัติจากพิกัด)",
            "price_per_day": "ราคา/วัน",
            "extra_amenities": "สิ่งอำนวยความสะดวกเพิ่มเติม",
            "code": "Plus Code",
            "latitude": "ละติจูด (Latitude)",
            "longitude": "ลองจิจูด (Longitude)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ใส่ class พื้นฐานให้ทุกฟิลด์ ถ้ายังไม่มี
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-lg border-gray-300 shadow-sm "
                "focus:ring focus:ring-blue-200"
            )

        # ปรับหน้าตา price_per_day เพิ่มเติม
        self.fields["price_per_day"].widget.attrs.update({
            "class": "w-full rounded-lg border border-gray-300 shadow-sm "
                     "focus:ring focus:ring-blue-200 text-left",
            "placeholder": "กรอกราคา/วัน"
        })

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("latitude")
        lng = cleaned.get("longitude")

        # บังคับให้เลือกพิกัด
        if lat is None or lng is None:
            raise forms.ValidationError("กรุณาเลือกพิกัดบนแผนที่ก่อนบันทึก")

        # เช็กช่วงค่าพิกัด
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except (TypeError, ValueError):
            raise forms.ValidationError("พิกัดไม่ถูกต้อง")

        if not (-90.0 <= lat_f <= 90.0):
            self.add_error("latitude", "Latitude ต้องอยู่ระหว่าง -90 ถึง 90")
        if not (-180.0 <= lng_f <= 180.0):
            self.add_error("longitude", "Longitude ต้องอยู่ระหว่าง -180 ถึง 180")

        return cleaned


class VenueAmenityForm(forms.ModelForm):
    class Meta:
        model = VenueAmenity
        exclude = ["venue"]
        widgets = {
            f: forms.CheckboxInput() for f in [
                "wifi", "parking", "equipment", "sound_system", "projector",
                "air_conditioning", "seating", "drinking_water", "first_aid", "cctv"
            ]
        }
        labels = {
            "wifi": "Wi-Fi อินเทอร์เน็ต",
            "parking": "ที่จอดรถ",
            "equipment": "อุปกรณ์กีฬา",
            "sound_system": "ระบบเสียง / ไมโครโฟน",
            "projector": "โปรเจกเตอร์ / หน้าจอ",
            "air_conditioning": "เครื่องปรับอากาศ",
            "seating": "เก้าอี้ / โต๊ะ",
            "drinking_water": "เครื่องกดน้ำ",
            "first_aid": "ชุดปฐมพยาบาล",
            "cctv": "กล้องวงจรปิด / ระบบรักษาความปลอดภัย",
        }


class LimitedImageFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        active = 0
        for form in self.forms:
            if form.cleaned_data.get("DELETE"):
                continue
            if form.cleaned_data.get("image") or form.instance.pk:
                active += 1
        if active > 5:
            raise forms.ValidationError("อัปโหลดรูปได้สูงสุด 5 รูปต่อสถานที่")


VenueImageFormSet = forms.inlineformset_factory(
    parent_model=Venue,
    model=VenueImage,
    fields=["image", "order"],
    extra=5,
    can_delete=True,
    max_num=5,
    validate_max=True,
    formset=LimitedImageFormSet
)


# ---------- Booking Form (เดิม) ----------
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['venue', 'start_date', 'end_date', 'start_time', 'end_time', 'notes']
        widgets = {
            'venue': forms.Select(attrs={
                'placeholder': 'เลือกสถานที่',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'วันที่เริ่มต้น',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'วันที่สิ้นสุด',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'placeholder': 'เวลาเริ่มต้น',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'placeholder': 'เวลาสิ้นสุด',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'
            }),
            'notes': forms.Textarea(attrs={
                'placeholder': 'หมายเหตุเพิ่มเติม (ถ้ามี)',
                'rows': 3,
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'
            }),
        }

    def clean(self):  # type: ignore
        cleaned_data = super().clean()
        venue = cleaned_data.get('venue')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if not all([venue, start_date, end_date, start_time, end_time]):
            return

        today = timezone.localdate()
        now_time = timezone.localtime().time()

        # ห้ามจองย้อนหลัง: start date ต้องไม่เป็นอดีต
        if start_date < today:
            raise ValidationError("ไม่สามารถจองย้อนหลังได้ (วันที่เริ่มต้นต้องเป็นวันนี้หรือวันที่ในอนาคต)")

        # ถ้าเริ่มวันนี้ ให้เวลาเริ่มมากกว่าเวลาปัจจุบัน
        if start_date == today and start_time <= now_time:
            raise ValidationError("ไม่สามารถจองย้อนหลังได้ (เวลาเริ่มต้นต้องมากกว่าเวลาปัจจุบัน)")

        if end_date < start_date:
            raise ValidationError("วันสิ้นสุดต้องไม่น้อยกว่าวันเริ่มต้น")
        if start_date == end_date and end_time <= start_time:
            raise ValidationError("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น")

        # หาก end อยู่วันนี้ ตรวจว่าเวลา end ไม่เป็นอดีต
        if end_date == today and end_time <= now_time:
            raise ValidationError("ไม่สามารถจองช่วงที่สิ้นสุดในอดีตได้ (เวลาในอดีต)")

        overlapping = Booking.objects.filter(
            venue=venue,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exclude(start_time__gte=end_time).exclude(end_time__lte=start_time)

        if overlapping.exists():
            raise ValidationError(
                "ช่วงเวลานี้มีผู้ใช้อื่นจองสถานที่แล้ว กรุณาเลือกวันหรือเวลาใหม่"
            )


# ---------- ฟอร์มแนบสลิป + ยอด ----------
class PaymentSlipForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["payment_slip", "amount_paid"]
        widgets = {
            "amount_paid": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                    "class": "w-full border border-gray-300 rounded-lg px-3 py-2"
                }
            )
        }

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get("amount_paid")
        slip = cleaned.get("payment_slip")

        if amount is None:
            raise ValidationError("กรุณากรอกจำนวนเงินที่ชำระ")
        if amount <= 0:
            raise ValidationError("จำนวนเงินต้องมากกว่า 0")
        if not slip:
            raise ValidationError("กรุณาแนบรูปสลิปการชำระเงิน")

        # เช็คให้ยอดชำระเท่ากับยอดจองเป๊ะตั้งแต่ขั้นอัปโหลด
        required = (self.instance.total_price or Decimal("0.00"))
        if Decimal(amount) != Decimal(required):
            raise ValidationError(f"ยอดไม่ตรงกับยอดที่ต้องชำระ ({required} บาท)")

        return cleaned


# ---------- ฟอร์มข้อมูลบัญชี/QR เจ้าของสถานที่ ----------
class OwnerBankForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["bank_name", "bank_account_number", "bank_qr"]


# ---------- Activity Forms ----------
class ActivityForm(forms.ModelForm):
    booking = ModelChoiceField(
        queryset=Booking.objects.none(),
        label="เลือกการจอง (Booking)",
        help_text="เลือก Booking ที่สถานะเสร็จสมบูรณ์และยังไม่มีกิจกรรม"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        initial = kwargs.get('initial') or {}
        custom_qs = initial.pop('booking__queryset', None)
        kwargs['initial'] = initial

        super().__init__(*args, **kwargs)
        self.user = user

        # เตรียมข้อมูล instance ปัจจุบัน (ใช้ตอนแก้ไข)
        current_booking = None
        if self.instance is not None and self.instance.pk:
            current_booking = getattr(self.instance, "booking", None)

        # กรอง queryset ของ booking
        base_qs = Booking.objects.all()
        if user is not None:
            base_qs = base_qs.filter(user=user)

        COMPLETED = getattr(getattr(Booking, 'Status', None), 'COMPLETED', 'completed')
        base_qs = base_qs.filter(status=COMPLETED)

        # ถ้าเป็นฟอร์มแก้ไข: อนุญาต booking เดิมของตัวเองด้วย
        if current_booking:
            base_qs = base_qs.filter(
                Q(activity__isnull=True) | Q(pk=current_booking.pk)
            )
        else:
            base_qs = base_qs.filter(activity__isnull=True)

        # ถ้า view ฝั่ง Create ส่ง custom queryset มา ให้ intersect อีกชั้น
        if custom_qs is not None:
            base_qs = custom_qs.filter(pk__in=base_qs.values('pk'))

        self.fields['booking'].queryset = base_qs
        self.fields['booking'].widget.attrs.update({
            'class': 'w-full border rounded p-2 focus:border-[#3f72af] form-select',
        })

        # ถ้าเป็นฟอร์มแก้ไข ล็อก booking ไม่ให้เปลี่ยน
        if current_booking:
            self.fields['booking'].disabled = True

        # Widgets สำหรับ field วันที่/เวลา/จำนวนคน
        self.fields['start_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full border rounded p-2 focus:border-[#3f72af] form-input'
        })
        self.fields['end_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full border rounded p-2 focus:border-[#3f72af] form-input'
        })
        self.fields['start_time'].widget = forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full border rounded p-2 focus:border-[#3f72af] form-input'
        })
        self.fields['end_time'].widget = forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full border rounded p-2 focus:border-[#3f72af] form-input'
        })
        self.fields['max_participants'].widget.attrs.update({
            'class': 'w-full border rounded p-2 focus:border-[#3f72af] form-input',
            'min': '1',
        })

    class Meta:
        model = Activity
        fields = [
            'booking',
            'name',
            'description',
            'start_date',
            'end_date',
            'start_time',
            'end_time',
            'max_participants',
            'status',
        ]

    def clean_booking(self):
        booking = self.cleaned_data.get('booking')
        if not booking:
            raise ValidationError("กรุณาเลือกการจองที่จะผูกกับกิจกรรม")

        COMPLETED = getattr(getattr(Booking, 'Status', None), 'COMPLETED', 'completed')
        if str(booking.status) != str(COMPLETED):
            raise ValidationError("การจองนี้ยังไม่เสร็จสมบูรณ์ ไม่สามารถผูกกิจกรรมได้")

        # อนุญาตให้ใช้ booking ที่มี activity อยู่แล้ว ถ้าเป็น activity ตัวเดิม
        if hasattr(booking, 'activity') and booking.activity is not None:
            if not self.instance.pk or booking.activity.pk != self.instance.pk:
                raise ValidationError("การจองนี้มีกิจกรรมผูกอยู่แล้ว")

        if self.user and getattr(booking, 'user_id', None) != self.user.id:
            raise ValidationError("คุณไม่มีสิทธิ์ใช้การจองนี้")
        return booking

    def clean(self):
        cleaned = super().clean()

        booking = cleaned.get('booking') or getattr(self.instance, "booking", None)
        start_date = cleaned.get('start_date')
        end_date = cleaned.get('end_date')
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')

        # A) เติม end_date ให้เป็นวันเดียวกับ start_date ถ้าไม่กรอก
        if start_date and not end_date:
            cleaned['end_date'] = start_date
            end_date = start_date

        # B) ตรวจสอบความถูกต้องพื้นฐานของช่วงวัน/เวลา
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("วันที่จบกิจกรรมต้องไม่น้อยกว่าวันที่เริ่มกิจกรรม")

        if start_date and end_date and start_time and end_time:
            if end_date == start_date and end_time <= start_time:
                raise ValidationError("เวลาจบกิจกรรมต้องมากกว่าเวลาเริ่มกิจกรรม")

        # C) กฎใหม่: ช่วงกิจกรรมต้องอยู่ในช่วง Booking
        if booking and start_date and end_date:
            # 1) ช่วงวันต้องไม่เฉออกนอก Booking
            if not (booking.start_date <= start_date <= end_date <= booking.end_date):
                msg = (
                    "ช่วงวันที่ของกิจกรรมต้องอยู่ภายในช่วงวันที่ที่คุณจองสถานที่ไว้ "
                    f"(ช่วงที่จอง: {booking.start_date} ถึง {booking.end_date})"
                )
                self.add_error('start_date', msg)
                self.add_error('end_date', msg)

            # # 2) ถ้ากิจกรรมเป็นวันเดียว → เช็คเวลาในวันนั้น
            # if start_date == end_date and start_time and end_time:
            #     if booking.start_time and booking.end_time:
            #         if not (booking.start_time <= start_time < end_time <= booking.end_time):
            #             msg_time = (
            #                 "ช่วงเวลาของกิจกรรมต้องอยู่ภายในช่วงเวลาที่จองสถานที่ไว้ "
            #                 f"(ช่วงที่จอง: {booking.start_time} ถึง {booking.end_time})"
            #             )
            #             self.add_error('start_time', msg_time)
            #             self.add_error('end_time', msg_time)

        return cleaned


class ActivityParticipantsForm(forms.ModelForm):
    class Meta:
        model = ActivityParticipants
        fields = ['activity', 'user', 'status']
        widgets = {
            'activity': HiddenInput(),
            'user': HiddenInput()
        }


class ActivityManualRegistrationForm(forms.ModelForm):
    class Meta:
        model = ActivityParticipants
        fields = ['manual_full_name', 'manual_email', 'manual_phone', 'manual_note']
        labels = {
            'manual_full_name': 'ชื่อ-นามสกุล',
            'manual_email': 'อีเมล',
            'manual_phone': 'เบอร์โทร',
            'manual_note': 'หมายเหตุ',
        }
        widgets = {
            'manual_full_name': forms.TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'placeholder': 'ชื่อ-นามสกุล',
            }),
            'manual_email': forms.EmailInput(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'placeholder': 'อีเมล (ถ้ามี)',
            }),
            'manual_phone': forms.TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'placeholder': 'เบอร์โทร (ถ้ามี)',
            }),
            'manual_note': forms.Textarea(attrs={
                'class': 'w-full border rounded px-3 py-2',
                'rows': 3,
                'placeholder': 'หมายเหตุ (ถ้ามี)',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('manual_full_name'):
            self.add_error('manual_full_name', 'กรุณากรอกชื่อ-นามสกุล')
        return cleaned


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'border rounded-md px-3 py-2 text-sm w-full'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'border rounded-md px-3 py-2 text-sm w-full',
                'rows': 4,
                'placeholder': 'เขียนรีวิวสถานที่นี้...'
            }),
        }
        labels = {
            'rating': 'ให้คะแนน',
            'comment': 'รีวิว',
        }