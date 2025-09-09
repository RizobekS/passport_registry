from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to auth/urls.py file for more pages.
"""


class CustomLoginView(LoginView):
    template_name = "auth_login_basic.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        # базовый контекст LoginView (form, errors, next и т.п.)
        context = super().get_context_data(**kwargs)
        # инициализируем Sneat-контекст (layout_path, переменные темы и т.д.)
        context = TemplateLayout.init(self, context)  # положит layout_path по умолчанию (vertical) :contentReference[oaicite:3]{index=3}
        # для страниц аутентификации используем пустой макет
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context)
        })
        return context


class AuthView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # Update the context
        context.update(
            {
                "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
            }
        )

        return context
