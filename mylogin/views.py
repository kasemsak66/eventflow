from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect, render
from mylogin.forms import CustomUserCreateForm, CustomUserLoginForm, CustomUserUpdateForm
from mylogin.models import CustomUser
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages



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



