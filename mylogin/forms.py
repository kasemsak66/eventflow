from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm , UserChangeForm
from django.urls import reverse_lazy
from .models import CustomUser, Venue , VenueAmenity, VenueImage, Booking
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import ValidationError
from decimal import Decimal

# ---------- Auth Forms ----------
class CustomUserCreateForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['email','first_name', 'last_name', 'phone_num', 'dob']
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
                'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af] bg-white text-[#112d4e]'
            })

class CustomUserUpdateForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # ★ เพิ่มฟิลด์ธนาคาร + QR ให้แก้ได้จริง
        fields = ['first_name', 'last_name', 'phone_num', 'dob', 'bank_name', 'bank_account_number', 'bank_qr']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'phone_num': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'dob': forms.DateInput(attrs={'type':'date', 'class': 'w-full p-2 rounded'}),
            'bank_name': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'w-full p-2 rounded'}),
        }

class CustomUserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'อีเมล'
        self.fields['password'].label = 'รหัสผ่าน'
        self.fields['username'].widget.attrs.update({
            'placeholder': 'กรอกอีเมล',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af] bg-white text-[#112d4e]'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'กรอกรหัสผ่าน',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af] bg-white text-[#112d4e]'
        })

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'home/change_password.html'
    success_url = reverse_lazy('profile')

# ---------- Venue Forms ----------
from django import forms
from .models import Venue

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = [
            "name",
            "description",
            "address",
            "price_per_day",
            "extra_amenities",
            "latitude",     # ✅ เพิ่ม
            "longitude",    # ✅ เพิ่ม
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af]",
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
                "w-full rounded-lg border-gray-300 shadow-sm focus:ring focus:ring-blue-200"
            )

        # ปรับหน้าตา price_per_day เพิ่มเติม
        self.fields["price_per_day"].widget.attrs.update({
            "class": "w-full rounded-lg border border-gray-300 shadow-sm focus:ring focus:ring-blue-200 text-left",
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
        widgets = {f: forms.CheckboxInput() for f in [
            "wifi","parking","equipment","sound_system","projector",
            "air_conditioning","seating","drinking_water","first_aid","cctv"
        ]}
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
            'venue': forms.Select(attrs={'placeholder': 'เลือกสถานที่','class': 'w-full border border-gray-300 rounded-lg px-3 py-2'}),
            'start_date': forms.DateInput(attrs={'type': 'date','placeholder': 'วันที่เริ่มต้น','class': 'w-full border border-gray-300 rounded-lg px-3 py-2'}),
            'end_date': forms.DateInput(attrs={'type': 'date','placeholder': 'วันที่สิ้นสุด','class': 'w-full border border-gray-300 rounded-lg px-3 py-2'}),
            'start_time': forms.TimeInput(attrs={'type': 'time','placeholder': 'เวลาเริ่มต้น','class': 'w-full border border-gray-300 rounded-lg px-3 py-2'}),
            'end_time': forms.TimeInput(attrs={'type': 'time','placeholder': 'เวลาสิ้นสุด','class': 'w-full border border-gray-300 rounded-lg px-3 py-2'}),
            'notes': forms.Textarea(attrs={'placeholder': 'หมายเหตุเพิ่มเติม (ถ้ามี)','rows': 3,'class': 'w-full border border-gray-300 rounded-lg px-3 py-2'}),
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
        if end_date < start_date:
            raise ValidationError("วันสิ้นสุดต้องไม่น้อยกว่าวันเริ่มต้น")
        if start_date == end_date and end_time <= start_time:
            raise ValidationError("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น")
        overlapping = Booking.objects.filter(
            venue=venue, start_date__lte=end_date, end_date__gte=start_date
        ).exclude(start_time__gte=end_time).exclude(end_time__lte=start_time)
        if overlapping.exists():
            raise ValidationError("ช่วงเวลานี้มีผู้ใช้อื่นจองสถานที่แล้ว กรุณาเลือกวันหรือเวลาใหม่")

# ---------- ใหม่: ฟอร์มแนบสลิป + ยอด ----------
class PaymentSlipForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["payment_slip", "amount_paid"]
        widgets = {
            "amount_paid": forms.NumberInput(
                attrs={"min":"0","step":"0.01","class":"w-full border border-gray-300 rounded-lg px-3 py-2"}
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

        # ✅ เช็คให้ยอดชำระเท่ากับยอดจองเป๊ะตั้งแต่ขั้นอัปโหลด
        required = (self.instance.total_price or Decimal("0.00"))
        if Decimal(amount) != Decimal(required):
            raise ValidationError(f"ยอดไม่ตรงกับยอดที่ต้องชำระ ({required} บาท)")

        return cleaned

# ---------- ใหม่: ฟอร์มข้อมูลบัญชี/QR เจ้าของสถานที่ ----------
class OwnerBankForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["bank_name", "bank_account_number", "bank_qr"]
