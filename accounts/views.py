from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.shortcuts import render,redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegisterForm, ProfileForm
from .models import MasterProfile
from django.utils.translation import gettext_lazy as _



def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            messages.success(request, _('Your request has been submitted. Please wait for administrator approval'))
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def get_safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url,
                                                    allowed_hosts={request.get_host()},
                                                    require_https=request.is_secure()
                                                    ):
        return next_url
    return None


def login_view(request):
    next_url = get_safe_next_url(request)
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(next_url or settings.LOGIN_REDIRECT_URL)
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})

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

            messages.success(request, _('Your profile was successfully updated'))
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'form': form,
    })