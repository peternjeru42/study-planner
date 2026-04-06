from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.forms import RegistrationForm, StudentProfileForm, UserUpdateForm
from planner.services import generate_plan


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    user_form = RegistrationForm(request.POST or None)
    profile_form = StudentProfileForm(request.POST or None)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user = user_form.save()
        profile = user.profile
        for field, value in profile_form.cleaned_data.items():
            setattr(profile, field, value)
        profile.save()
        login(request, user)
        generate_plan(user, trigger_reason="registration")
        messages.success(request, "Your account is ready. Start by adding subjects and assessments.")
        return redirect("dashboard:home")

    return render(request, "accounts/register.html", {"user_form": user_form, "profile_form": profile_form})


@login_required
def profile_view(request):
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = StudentProfileForm(request.POST or None, instance=request.user.profile)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        generate_plan(request.user, trigger_reason="preferences_updated")
        messages.success(request, "Profile and planner preferences updated.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {"user_form": user_form, "profile_form": profile_form})
