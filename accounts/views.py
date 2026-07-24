from django.contrib import messages
from django.shortcuts import render,redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegisterForm, ProfileForm
from .models import MasterProfile


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            messages.success(request, 'Заявку створено. Очікуйте підтвердження адміністратора.')
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('appointments:index')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def profile_view(request):
    profile, created = MasterProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            form.save()
            photo = form.cleaned_data.get('photo')
            if photo:
                profile.photo = photo
                profile.save()

            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'form': form,
    })