from django.urls import path
from user import views

urlpatterns = [
    path("w/api/accounts/registration/", views.RegistrationView.as_view()),
    path("w/api/accounts/auth-token/", views.CustomAuthTokenView.as_view()),
    path("w/api/accounts/users/", views.GetAllUsersView.as_view()),
    path("w/api/accounts/<int:pk>/user/", views.ManageUserView.as_view()),
    path("w/api/accounts/<int:pk>/user/change-password/", views.ChangeUserPasswordView.as_view()),
    path("w/api/accounts/<int:pk>/user/activate-deactivate-account/", views.ActivateDeactivateUserAccountView.as_view()),
]

# 81160220127503cbfe9874014a8ac592c02d44d4