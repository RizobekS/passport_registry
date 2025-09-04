from django.contrib import admin
from .models import Vaccination, LabTest


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ("horse", "date", "vaccine", "batch_no", "veterinarian")
    list_filter = ("vaccine", "date")
    search_fields = ("horse__name", "vaccine__name", "batch_no")


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("horse", "date", "test_type", "result", "veterinarian")
    list_filter = ("test_type", "date")
    search_fields = ("horse__name", "result")
