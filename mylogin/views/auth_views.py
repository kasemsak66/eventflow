from io import BytesIO
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.forms import HiddenInput
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from mylogin.forms import (
    RegisterForm, LoginForm,
    UpdateProfileForm
)
from mylogin.models import ActivityParticipants, Favorite, Venue, VenueAmenity, Booking, Activity
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from openlocationcode import openlocationcode as olc
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView

# ========================================
# Login
# ========================================
def login(request):
    next_url = request.GET.get('next', None)

    # POST → ผู้ใช้ส่งฟอร์ม login
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        email = request.POST.get('username')
        password = request.POST.get('password')
        print(f'login with email={email}, password={password}')

        # ตรวจสอบข้อมูลเข้าสู่ระบบ
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)

            # ถ้า login มาจากหน้าอื่นจะ redirect กลับไปหน้าเดิม
            if next_url:
                return redirect(next_url)

            return redirect('landing')

        else:
            messages.error(request, "อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    # GET → แสดงฟอร์ม login เปล่า
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


# ========================================
# Logout
# ========================================
def logout(request):
    auth_logout(request)
    return redirect('login')


# ========================================
# Register
# ========================================
def register(request):

    # POST → ฟอร์มถูกส่งเพื่อสมัครสมาชิก
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            print(f'User created: {form.cleaned_data["email"]} with password: {form.cleaned_data["password1"]}')
            return redirect('login')

    # GET → แสดงฟอร์มว่าง
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


# ========================================
# หน้า Home (ต้อง login)
# ========================================
@never_cache
@login_required(login_url='login')
def home(request):
    user = request.user
    return render(request, 'home/home.html', {'user': user})


# ========================================
# Profile
# ========================================
@login_required
def profile_view(request):
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('venue')

    return render(request, 'home/profile.html', {
        'favorites': favorites,
    })


@login_required
def profile_edit(request):
    """
    GET: แสดงฟอร์มแก้ไขโปรไฟล์
    POST: บันทึกการแก้ไขข้อมูลผู้ใช้ (ไม่แก้ไขรหัสผ่าน)
    """
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()   # บันทึกเลย ไม่ยุ่งกับ password
            messages.success(request, 'อัปเดตข้อมูลเรียบร้อยแล้ว')
            return redirect('profile')

    else:
        form = UpdateProfileForm(instance=request.user)

    return render(request, 'home/profile_edit.html', {'form': form})

class PasswordChange(LoginRequiredMixin, PasswordChangeView):
    template_name = 'home/change_password.html'
    success_url = reverse_lazy('profile')