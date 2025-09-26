from django.urls import path

from .views import PassportListView, public_passport

app_name = 'passports'
urlpatterns = [
    path('list/', PassportListView.as_view(), name='list'),
    path("p/<slug:number>/", public_passport, name="public"),
]
