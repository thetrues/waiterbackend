from django.urls import path
from user import views

urlpatterns = [
    path("w/api/accounts/registration/", views.Registration.as_view()),
    path("w/api/accounts/auth-token/", views.CustomAuthToken.as_view()),
    path("w/api/accounts/users/", views.GetUsersView.as_view()),
]
