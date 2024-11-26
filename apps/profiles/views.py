from django.shortcuts import redirect, render
from django.views import View
from apps.accounts.mixins import LoginRequiredMixin
from apps.accounts.forms import UserEditForm
from .forms import ProfileEditForm


import sweetify


class MyProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile = request.user.profile

        context = {
            "profile": profile,
        }
        return render(request, "profiles/profile.html", context)


class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        return render(
            request,
            "profiles/edit.html",
            {"user_form": user_form, "profile_form": profile_form},
        )

    def post(self, request):
        user_form = UserEditForm(instance=request.user, data=request.POST)
        
        profile_form = ProfileEditForm(
            instance=request.user.profile, data=request.POST, files=request.FILES
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            sweetify.toast(request, "Profile updated successfully")
            return redirect("profiles:profile")

        return render(
            request,
            "profiles/edit.html",
            {"user_form": user_form, "profile_form": profile_form},
        )
