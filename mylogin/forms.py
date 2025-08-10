from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm , UserChangeForm
from django.urls import reverse_lazy
from .models import CustomUser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView

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