from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, UserPreferencesForm
from .models import Profile, UserPreferences

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('account:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'account/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        preferences_form = UserPreferencesForm(request.POST, instance=request.user.userpreferences)
        if profile_form.is_valid() and preferences_form.is_valid():
            profile_form.save()
            preferences_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('account:profile')
    else:
        profile_form = UserProfileForm(instance=request.user.profile)
        preferences_form = UserPreferencesForm(instance=request.user.userpreferences)
    
    context = {
        'profile_form': profile_form,
        'preferences_form': preferences_form
    }
    return render(request, 'account/profile.html', context)

@login_required
def dashboard(request):
    user_profile = request.user.profile
    context = {
        'profile': user_profile,
    }
    return render(request, 'account/dashboard.html', context)

@login_required
def settings(request):
    if request.method == 'POST':
        preferences_form = UserPreferencesForm(request.POST, instance=request.user.userpreferences)
        if preferences_form.is_valid():
            preferences_form.save()
            messages.success(request, 'Your settings have been updated!')
            return redirect('account:settings')
    else:
        preferences_form = UserPreferencesForm(instance=request.user.userpreferences)
    
    context = {
        'preferences_form': preferences_form
    }
    return render(request, 'account/settings.html', context)
