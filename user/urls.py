from django.urls import path
from user import views

urlpatterns = [
    path("w/api/accounts/registration/", views.RegistrationView.as_view()),
    path("w/api/accounts/login/", views.LoginView.as_view()),
    path("w/api/accounts/auth-token/", views.CustomAuthTokenView.as_view()),
    path("w/api/accounts/users/", views.GetAllUsersView.as_view()),
    path("w/api/accounts/<int:pk>/user/", views.ManageUserView.as_view()),
    path("w/api/accounts/<int:pk>/user/change-password/", views.ChangeUserPasswordView.as_view()),
    path("w/api/accounts/<int:pk>/user/activate-deactivate-account/", views.ActivateDeactivateUserAccountView.as_view()),
]

