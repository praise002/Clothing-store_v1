from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("profile/", views.MyProfileView.as_view(), name="profile"),
]
