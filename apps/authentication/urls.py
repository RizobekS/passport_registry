from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import AuthView, CustomLoginView

app_name = "auth"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "register/",
        AuthView.as_view(template_name="auth_register_basic.html"),
        name="register",
    ),
    path(
        "forgot_password/",
        AuthView.as_view(template_name="auth_forgot_password_basic.html"),
        name="forgot-password",
    ),
]
