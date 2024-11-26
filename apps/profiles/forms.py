from django import forms
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class ProfileEditForm(forms.ModelForm):
    shipping_address = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    postal_code = forms.CharField(
        max_length=20, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    city = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    phone = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Profile
        fields = ["shipping_address", "postal_code", "city", "phone", "avatar"]
