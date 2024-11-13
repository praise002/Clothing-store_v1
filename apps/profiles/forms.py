from django import forms
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["shipping_address", "avatar"]
