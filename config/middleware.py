from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve

PUBLIC_PATHS = {
    "/dashboard/",
    "/auth/login/",
    "/auth/logout/",
    "/auth/register/",
    "/auth/forgot_password/",
}
class LoginRequiredMiddleware:
    """
    Если пользователь не аутентифицирован — пускаем только на whitelist.
    Остальные URL → редирект на LOGIN_URL.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = getattr(settings, "LOGIN_URL", "/auth/login/")

    def __call__(self, request):
        path = request.path

        # статика/медиа — пропускаем
        if path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # whitelist публичных страниц
        if path in PUBLIC_PATHS:
            return self.get_response(request)

        # админку по желанию можно оставить открытой до страницы логина админки
        if path.startswith("/admin/"):
            return self.get_response(request)

        # если аутентифицирован — пропускаем
        if request.user.is_authenticated:
            return self.get_response(request)

        # редирект на логин с next=
        return redirect(f"{self.login_url}?next={path}")
