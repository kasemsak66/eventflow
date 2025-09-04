from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm , UserChangeForm
from django.urls import reverse_lazy
from .models import CustomUser, Venue , VenueAmenity, VenueImage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import ValidationError
from .models import Booking

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
        # เพิ่ม placeholder + Tailwind CSS
        self.fields['email'].widget.attrs.update({'placeholder': 'กรอกอีเมล'},error_messages={'required': 'กรุณากรอกอีเมล'})
        self.fields['first_name'].widget.attrs.update({'placeholder': 'กรอกชื่อ'},error_messages={'required': 'กรุณากรอกชื่อ'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'กรอกนามสกุล'},error_messages={'required': 'กรุณากรอกนามสกุล'})
        self.fields['phone_num'].widget.attrs.update({'placeholder': 'กรอกหมายเลขโทรศัพท์'},error_messages={'required': 'กรุณากรอกหมายเลขโทรศัพท์'})
        self.fields['dob'].widget.attrs.update({'placeholder': 'วัน/เดือน/ปี'},error_messages={'required': 'กรุณากรอกนามสกุล'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'กรอกรหัสผ่าน'},error_messages={'required': 'กรุณากรอกรหัสผ่าน'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'ยืนยันรหัสผ่าน'},error_messages={'required': 'กรุณายืนยันรหัสผ่าน'})

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af] bg-white text-[#112d4e]'
            })

class CustomUserUpdateForm(UserChangeForm): 
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_num', 'dob']  # ลบ 'password' ออก
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

        # เปลี่ยน placeholder และเพิ่มคลาส Tailwind
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

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ["name", "description", "address", "price_per_day", "extra_amenities"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-[#3f72af]",
                "placeholder": "เช่น โรงยิม A"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded resize-none",
                "placeholder": "รายละเอียดสถานที่"
            }),
            "address": forms.Textarea(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded resize-none",
                "placeholder": "ที่อยู่"
            }),
            "price_per_day": forms.NumberInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded text-right",
                "min": "0",
                "step": "1",
                "placeholder": "เช่น 1500"
            }),
            "extra_amenities": forms.Textarea(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded resize-none",
                "placeholder": "สิ่งอำนวยความสะดวกเพิ่มเติม (ถ้ามี)"
            }),
        }
        labels = {
            "name": "ชื่อสถานที่",
            "description": "รายละเอียด",
            "address": "ที่อยู่",
            "price_per_day": "ราคา/วัน",
            "extra_amenities": "สิ่งอำนวยความสะดวกเพิ่มเติม",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'w-full rounded-lg border-gray-300 shadow-sm focus:ring focus:ring-blue-200'
            )
        self.fields['price_per_day'].widget.attrs.update({
        'class': 'w-full rounded-lg border border-gray-300 shadow-sm focus:ring focus:ring-blue-200 text-left',
        'placeholder': 'กรอกราคา/วัน'
    })

class VenueAmenityForm(forms.ModelForm):
    class Meta:
        model = VenueAmenity
        exclude = ["venue"]
        widgets = {
            f: forms.CheckboxInput()
            for f in [
                "wifi","parking","equipment","sound_system","projector",
                "air_conditioning","seating","drinking_water","first_aid","cctv"
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
            # นับเฉพาะฟอร์มที่มีรูปใหม่หรือเป็นรูปเดิมที่ยังอยู่
            if form.cleaned_data.get("image") or form.instance.pk:
                active += 1
        if active > 5:
            raise forms.ValidationError("อัปโหลดรูปได้สูงสุด 5 รูปต่อสถานที่")

VenueImageFormSet = forms.inlineformset_factory(
    parent_model=Venue,
    model=VenueImage,
    fields=["image", "order"],
    extra=5,                # มีช่องว่างให้เพิ่มอย่างน้อย 1
    can_delete=True,
    max_num=5,
    validate_max=True,
    formset=LimitedImageFormSet
)


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

    def clean(self): #type:  ignore
        cleaned_data = super().clean()
        venue = cleaned_data.get('venue')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if not all([venue, start_date, end_date, start_time, end_time]):
            return

        # ✨ ตรวจสอบ end_date >= start_date
        if end_date < start_date: #type:  ignore
            raise ValidationError("วันสิ้นสุดต้องไม่น้อยกว่าวันเริ่มต้น")

        # ✨ ถ้าเป็นวันเดียวกัน ตรวจสอบเวลาสิ้นสุด > เริ่มต้น
        if start_date == end_date and end_time <= start_time: #type:  ignore
            raise ValidationError("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น")

        # ✨ ตรวจสอบการจองซ้ำ (overlap)
        overlapping = Booking.objects.filter(
            venue=venue,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exclude(
            start_time__gte=end_time
        ).exclude(
            end_time__lte=start_time
        )

        if overlapping.exists():
            raise ValidationError("ช่วงเวลานี้มีผู้ใช้อื่นจองสถานที่แล้ว กรุณาเลือกวันหรือเวลาใหม่")
