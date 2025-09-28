from django import forms
from django.contrib import admin
from .models import Vaccination, LabTest
from apps.common.admin import coerce_yes_no_none


class VaccinationAdminForm(forms.ModelForm):
    vaccine_for_grip = forms.TypedChoiceField(
        label="Вакцина для гриппа",
        choices=(("True", "Да"), ("False", "Нет")),
        coerce=lambda v: True if v in (True, "True", "1") else False,
        required=True,
        widget=forms.RadioSelect
    )
    class Meta:
        model = Vaccination
        fields = "__all__"

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ("horse", "date", "vaccine", 'vaccine_for_grip', 'registration_number', "veterinarian")
    list_filter = ("vaccine", "date", 'vaccine_for_grip', 'vaccine_for_grip')
    search_fields = ("horse__name", "vaccine__name")

    @admin.display(boolean=True, description="Для гриппа")
    def vaccine_for_grip_display(self, obj):
        return obj.vaccine_for_grip


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("horse", "date", "test_type", "result", "veterinarian")
    list_filter = ("test_type", "date")
    search_fields = ("horse__name", "result")
