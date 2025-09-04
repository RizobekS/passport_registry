from django.urls import path

from .views import PassportListView, public_passport, RegistryDashboardView

app_name = 'passports'
urlpatterns = [
    path('list/', PassportListView.as_view(), name='list'),
    path('', RegistryDashboardView.as_view(), name='dashboard'),
    path('p/<uuid:qr_id>/', public_passport, name='public'),
]
