from django.contrib import admin
from django import forms

from .models import Region, Breed, Color, Vaccine, LabTestType, NumberSequence, District, Country


def coerce_yes_no_none(v):
    if v in (True, False, None):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v.lower() in ("true", "1", "yes", "да"):
            return True
        if v.lower() in ("false", "0", "no", "нет"):
            return False
        if v.lower() in ("none", "", "-"):
            return None
    return None


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0
    classes = ("tab", "tab-identity")


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    inlines = (DistrictInline, )

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class VaccineAdminForm(forms.ModelForm):
    vaccine_for_grip = forms.TypedChoiceField(
        label="Вакцина для гриппа",
        choices=(("True", "Да"), ("False", "Нет")),
        coerce=lambda v: True if v in (True, "True", "1") else False,
        required=True,
        widget=forms.RadioSelect
    )
    class Meta:
        model = Vaccine
        fields = "__all__"

@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    form = VaccineAdminForm
    list_display = ("name", "batch_number", "vaccine_for_grip", "manufacture_date", "manufacturer_address")
    search_fields = ("name", "batch_number")
    list_filter = ("vaccine_for_grip",)

    @admin.display(boolean=True, description="Для гриппа")
    def vaccine_for_grip_display(self, obj):
        return obj.vaccine_for_grip


@admin.register(LabTestType)
class LabTestTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ("scope", "year", "region_name", "value")
    list_filter = ("scope", "year")
    search_fields = ("region_name",)
